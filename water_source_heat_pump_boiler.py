"""Ground source heat pump boiler — physics-based cycle model.

Resolves a vapour-compression refrigerant cycle coupled to a borehole heat
exchanger (BHE) on the evaporator side and a lumped-capacitance hot-water
tank on the condenser side. At each time step the model finds the
minimum-power operating point via 1D Brent optimization over the evaporator
approach temperature difference, while the condenser temperature is solved
analytically.

Borehole thermal response is tracked with pygfunction-based multi-borehole
g-functions, enabling robust long-term ground temperature drift modeling.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import CoolProp.CoolProp as CP
import numpy as np
import pandas as pd
from tqdm import tqdm

from . import calc_util as cu
from .constants import c_w, k_w, mu_w, rho_w
from .dynamic_context import (
    ControlState,
    StepContext,
    determine_heat_source_on_off,
    determine_tank_refill_flow,
    tank_mass_energy_residual,
)
from .enex_functions import (
    calc_mixing_valve_flows,
    calc_mixing_valve_temp,
)
from .heat_transfer import calc_simple_tank_UA
from .refrigerant import calc_ref_state
from .thermodynamics import calc_exergy_flow

if TYPE_CHECKING:
    from .subsystems import SolarThermalCollector


class WaterSourceHeatPumpBoiler:
    """Water source heat pump boiler with BHE and lumped-tank model.

    The refrigerant cycle is resolved via CoolProp with user-specified
    superheat / subcool margins. An optimizer minimises total cycle
    electrical input subject to NTU-based evaporator constraints and
    analytical condenser temperature relations.
    """

    def __init__(
        self,
        # 1. Refrigerant / cycle / compressor
        refrigerant: str = "R410A",
        V_disp_cmp: float = 0.0005,
        eta_cmp_isen: float = 0.7,
        # 2. Heat exchanger UA
        UA_cond_design: float = 500,
        UA_evap_design: float = 500,
        # 3. Tank / control / load
        T0: float = 0.0,
        Ts: float = 16.0,
        T_tank_w_upper_bound: float = 65.0,
        T_tank_w_lower_bound: float = 55.0,
        T_mix_w_out: float = 40.0,
        T_tank_w_in: float = 15.0,
        hp_capacity: float = 8000.0,
        dV_mix_w_out_max: float = 0.0001,
        # Tank / insulation
        r0: float = 0.2,
        H: float = 0.8,
        x_shell: float = 0.01,
        x_ins: float = 0.05,
        k_shell: float = 25,
        k_ins: float = 0.03,
        h_o: float = 15,
        # 4. Borehole heat exchanger (Field + Params)
        N_1: int = 1,
        N_2: int = 1,
        B: float = 6.0,
        D_b: float = 0,
        H_b: float = 200,
        r_b: float = 0.08,
        R_b: float | None = None,
        k_g: float = 1.5,
        k_p: float = 0.4,
        r_out: float = 0.016,
        r_in: float = 0.013,
        D_s: float = 0.025,
        dV_b_f_lpm: float = 24,
        k_s: float = 2.0,
        c_s: float = 800,
        rho_s: float = 2000,
        E_pmp: float = 200,
        v_river: float = 0.5,
        # 6. Superheat / subcool
        dT_superheat: float = 5.0,
        dT_subcool: float = 5.0,
        # 7. Tank fluid limits
        tank_always_full: bool = True,
        prevent_simultaneous_flow: bool = False,
        tank_level_lower_bound: float = 0.5,
        tank_level_upper_bound: float = 1.0,
        dV_tank_w_in_refill: float = 0.001,
        # 8. Operation Schedule
        hp_on_schedule: list[tuple[float, float]] | None = None,
        # 9. Subsystems
        stc: SolarThermalCollector | None = None,
        pv=None,
        uv=None,
        # 10. Simulation scope (for precomputing g-functions)
        t_max_s: float = 8760 * 3600,
        dt_s: float = 3600,
    ) -> None:

        self.tank_physical = {
            "r0": r0,
            "H": H,
            "x_shell": x_shell,
            "x_ins": x_ins,
            "k_shell": k_shell,
            "k_ins": k_ins,
            "h_o": h_o,
        }
        self.UA_tank = calc_simple_tank_UA(**self.tank_physical)
        self.V_tank_full: float = math.pi * r0**2 * H
        self.C_tank = c_w * rho_w * self.V_tank_full

        self.ref = refrigerant
        self.V_disp_cmp = V_disp_cmp
        self.eta_cmp_isen = eta_cmp_isen

        self.UA_cond = UA_cond_design
        self.UA_evap = UA_evap_design

        self.T0_K = cu.C2K(T0)
        self.Ts = Ts
        self.Ts_K = cu.C2K(self.Ts)
        self.T_bhe_f_in = Ts
        self.T_bhe_f_in_K = self.Ts_K

        self.hp_capacity = hp_capacity
        self.hp_on_schedule = hp_on_schedule or [(0.0, 24.0)]
        self.dV_mix_w_out_max = dV_mix_w_out_max
        self.T_tank_w_upper_bound = T_tank_w_upper_bound
        self.T_tank_w_lower_bound = T_tank_w_lower_bound
        self.T_mix_w_out = T_mix_w_out
        self.T_mix_w_out_K = cu.C2K(T_mix_w_out)
        self.T_tank_w_in = T_tank_w_in
        self.T_tank_w_in_K = cu.C2K(T_tank_w_in)

        self.tank_always_full = tank_always_full
        self.prevent_simultaneous_flow = prevent_simultaneous_flow
        self.tank_level_lower_bound = tank_level_lower_bound
        self.tank_level_upper_bound = tank_level_upper_bound
        self.dV_tank_w_in_refill = dV_tank_w_in_refill

        self.dT_superheat = dT_superheat
        self.dT_subcool = dT_subcool

        # BHE properties
        self.N_1 = N_1
        self.N_2 = N_2
        self.B = B
        self.D_b = D_b
        self.H_b = H_b
        self.r_b = r_b
        self.k_s = k_s
        self.c_s = c_s
        self.rho_s = rho_s
        self.alp_s = k_s / (c_s * rho_s)
        self.E_pmp = E_pmp
        self.dV_b_f_m3s = dV_b_f_lpm * cu.L2m3 / cu.m2s
        self.v_river = v_river

        if R_b is None:
            from .g_function import calc_submerged_coil_thermal_resistance

            n_boreholes = max(1, self.N_1 * self.N_2)
            m_flow_total = self.dV_b_f_m3s * rho_w
            m_flow_pipe = m_flow_total / n_boreholes

            self.R_b = calc_submerged_coil_thermal_resistance(
                r_out=r_out,
                r_in=r_in,
                D_s=D_s,
                k_p=k_p,
                m_flow_pipe=m_flow_pipe,
                rho_f=rho_w,
                mu_f=mu_w,
                cp_f=c_w,
                k_f=k_w,
                v_river=self.v_river,
            )
        else:
            self.R_b = R_b

        # Subsystems
        self.stc = stc
        self.pv = pv
        self._subsystems: dict[str, Any] = {}
        if stc is not None:
            self._subsystems["stc"] = stc
        if pv is not None:
            self._subsystems["pv"] = pv
        if uv is not None:
            self._subsystems["uv"] = uv

        self.Q_cond_LOAD_OFF_TOL: float = 50.0  # W

        self.dt_s: float = dt_s

        # Simulation state tracking (dynamically updated in analyze_dynamic)
        self.time: np.ndarray = np.array([])
        self.dt: float = dt_s
        self._opt_evals: int = 0
        self.T_bhe_f: float = self.Ts
        self.T_bhe: float = self.Ts
        self.T_bhe_f_out: float = self.Ts
        self.T_bhe_f_out_K: float = self.Ts_K
        self.Q_bhe: float = 0.0

        # NOTE: Removed self.dV_mix_w_out, self.dV_tank_w_in, self.dV_mix_sup_w_in
        # They will be passed inside `flow_state: dict`.

    @staticmethod
    def _calc_tank_flow_context(
        dV_mix_w_out: float,
        T_tank_w_K: float,
        T_tank_w_in_K: float,
        T_mix_w_out_K: float,
        dV_tank_w_in_override: float | None = None,
    ) -> dict:
        mix_state = calc_mixing_valve_temp(T_tank_w_K, T_tank_w_in_K, T_mix_w_out_K)
        flows = calc_mixing_valve_flows(dV_mix_w_out, mix_state["alp"])
        dV_tank_w_out = flows["dV_hot_in"]
        dV_tank_w_in = dV_tank_w_out if dV_tank_w_in_override is None else dV_tank_w_in_override
        return {
            "alp": mix_state["alp"],
            "dV_mix_w_out": dV_mix_w_out,
            "dV_tank_w_out": dV_tank_w_out,
            "dV_tank_w_in": dV_tank_w_in,
            "dV_mix_sup_w_in": flows["dV_cold_in"],
        }

    def _calc_off_state(self, T_tank_w: float, T0: float, flow_state: dict) -> dict:
        T_tank_w_K = cu.C2K(T_tank_w)
        mix = calc_mixing_valve_temp(T_tank_w_K, self.T_tank_w_in_K, self.T_mix_w_out_K)

        # Bound temperatures for PropsSI to prevent crashes when tank overheats
        # R410A critical temp is ~344.49K (71.3 °C)
        T_cond_K_calc = min(max(T_tank_w_K, 250.0), 340.0)
        T_evap_K_calc = min(max(self.T_bhe_f_in_K, 250.0), 340.0)

        P_ref_evap_sat = CP.PropsSI("P", "T", T_evap_K_calc, "Q", 1, self.ref)
        h_ref_evap_sat = CP.PropsSI("H", "P", P_ref_evap_sat, "Q", 1, self.ref)
        s_ref_evap_sat = CP.PropsSI("S", "P", P_ref_evap_sat, "Q", 1, self.ref)

        P_ref_cond_sat = CP.PropsSI("P", "T", T_cond_K_calc, "Q", 0, self.ref)
        h_ref_cond_sat_l = CP.PropsSI("H", "P", P_ref_cond_sat, "Q", 0, self.ref)
        s_ref_cond_sat_l = CP.PropsSI("S", "P", P_ref_cond_sat, "Q", 0, self.ref)

        return {
            "hp_is_on": False,
            "converged": True,
            "T_tank_w [°C]": T_tank_w,
            "T0 [°C]": T0,
            "T_mix_w_out [°C]": cu.K2C(mix["T_mix_w_out_K"]),
            "T_tank_w_in [°C]": self.T_tank_w_in,
            "Ts [°C]": self.Ts,
            "T_bhe [°C]": getattr(self, "T_bhe", self.Ts),
            "T_bhe_f [°C]": getattr(self, "T_bhe_f", self.Ts),
            "T_bhe_f_in [°C]": cu.K2C(getattr(self, "T_bhe_f_in_K", self.Ts_K)),
            "T_bhe_f_out [°C]": cu.K2C(getattr(self, "T_bhe_f_out_K", self.Ts_K)),
            "T_ref_evap_sat [°C]": cu.K2C(self.T_bhe_f_in_K),
            "T_ref_cond_sat_v [°C]": T_tank_w,
            "T_ref_cond_sat_l [°C]": T_tank_w,
            "T_ref_cmp_in [°C]": cu.K2C(self.T_bhe_f_in_K),
            "T_ref_cmp_out [°C]": T_tank_w,
            "T_ref_exp_in [°C]": T_tank_w,
            "T_ref_exp_out [°C]": cu.K2C(self.T_bhe_f_in_K),
            "T_cond [°C]": T_tank_w,
            "dV_mix_w_out [m3/s]": flow_state.get("dV_mix_w_out", 0.0),
            "dV_tank_w_in [m3/s]": flow_state.get("dV_tank_w_in", 0.0),
            "dV_tank_w_out [m3/s]": flow_state.get("dV_tank_w_out", 0.0),
            "dV_mix_sup_w_in [m3/s]": flow_state.get("dV_mix_sup_w_in", 0.0),
            "dV_bhe_f [m3/s]": self.dV_b_f_m3s,
            "P_ref_cmp_in [Pa]": P_ref_evap_sat,
            "P_ref_cmp_out [Pa]": P_ref_cond_sat,
            "P_ref_exp_in [Pa]": P_ref_cond_sat,
            "P_ref_exp_out [Pa]": P_ref_evap_sat,
            "P_ref_evap_sat [Pa]": P_ref_evap_sat,
            "P_ref_cond_sat_v [Pa]": P_ref_cond_sat,
            "P_ref_cond_sat_l [Pa]": P_ref_cond_sat,
            "h_ref_cmp_in [J/kg]": h_ref_evap_sat,
            "h_ref_cmp_out [J/kg]": h_ref_evap_sat,
            "h_ref_exp_in [J/kg]": h_ref_cond_sat_l,
            "h_ref_exp_out [J/kg]": h_ref_cond_sat_l,
            "h_ref_evap_sat [J/kg]": h_ref_evap_sat,
            "h_ref_cond_sat_v [J/kg]": h_ref_evap_sat,
            "h_ref_cond_sat_l [J/kg]": h_ref_cond_sat_l,
            "s_ref_cmp_in [J/(kg·K)]": s_ref_evap_sat,
            "s_ref_cmp_out [J/(kg·K)]": s_ref_evap_sat,
            "s_ref_exp_in [J/(kg·K)]": s_ref_cond_sat_l,
            "s_ref_exp_out [J/(kg·K)]": s_ref_cond_sat_l,
            "x_ref_cmp_in [J/kg]": 0.0,
            "x_ref_cmp_out [J/kg]": 0.0,
            "x_ref_exp_in [J/kg]": 0.0,
            "x_ref_exp_out [J/kg]": 0.0,
            "Q_bhe [W]": 0.0,
            "Q_ref_cond [W]": 0.0,
            "Q_ref_evap [W]": 0.0,
            "Q_cond_load [W]": 0.0,
            "E_cmp [W]": 0.0,
            "E_pmp [W]": 0.0,
            "E_tot [W]": 0.0,
            "m_dot_ref [kg/s]": 0.0,
            "cmp_rpm [rpm]": 0.0,
        }

    def _calc_state(
        self, dT_ref_evap: float, T_tank_w: float, Q_cond_load: float, T0: float, *, flow_state: dict
    ) -> dict | None:
        if Q_cond_load <= 0:
            return self._calc_off_state(T_tank_w, T0, flow_state)

        # 1. Analytical Condenser Approach Temperature
        dT_ref_cond = Q_cond_load / self.UA_cond

        T_tank_w_K = cu.C2K(T_tank_w)

        # The source temperature leaving BHE and entering HP
        T_source_K = float(getattr(self, "T_bhe_f_out_K", cu.C2K(15.0)))

        m_dot_cp_b = self.dV_b_f_m3s * rho_w * c_w
        T_evap_in_K = T_source_K + (self.E_pmp / m_dot_cp_b)

        T_ref_evap_sat_K = T_evap_in_K - dT_ref_evap
        T_ref_cond_sat_K = T_tank_w_K + dT_ref_cond

        pinch_min: float = 0.5
        actual_dT_subcool = min(self.dT_subcool, max(0.0, dT_ref_cond - pinch_min))

        # 2. Refrigerant Cycle Evaluation
        try:
            cycle_states = calc_ref_state(
                T_evap_K=T_ref_evap_sat_K,
                T_cond_K=T_ref_cond_sat_K,
                refrigerant=self.ref,
                eta_cmp_isen=self.eta_cmp_isen,
                dT_superheat=self.dT_superheat,
                dT_subcool=actual_dT_subcool,
            )
        except Exception:
            return None

        rho_ref_cmp_in = cycle_states["rho_ref_cmp_in [kg/m3]"]
        h_ref_cmp_in = cycle_states["h_ref_cmp_in [J/kg]"]
        h_ref_cmp_out = cycle_states["h_ref_cmp_out [J/kg]"]
        h_ref_exp_in = cycle_states["h_ref_exp_in [J/kg]"]
        h_ref_exp_out = cycle_states["h_ref_exp_out [J/kg]"]

        if (h_ref_cmp_out - h_ref_exp_in) <= 0:
            return None

        # 3. Cycle Performance
        m_dot_ref = Q_cond_load / (h_ref_cmp_out - h_ref_exp_in)
        Q_ref_cond = Q_cond_load
        Q_ref_evap = m_dot_ref * (h_ref_cmp_in - h_ref_exp_out)
        E_cmp = m_dot_ref * (h_ref_cmp_out - h_ref_cmp_in)
        cmp_rps = m_dot_ref / (self.V_disp_cmp * rho_ref_cmp_in)

        # 4. NTU Evaporator Analysis
        NTU_evap = self.UA_evap / m_dot_cp_b
        eps = 1.0 - math.exp(-NTU_evap)
        Q_evap_actual = eps * m_dot_cp_b * (T_evap_in_K - T_ref_evap_sat_K)
        err = Q_ref_evap - Q_evap_actual

        # Penalize if cycle evap load exceeds physics limit
        penalty = 0.0
        if Q_ref_evap > Q_evap_actual:
            penalty = 1e4 * (Q_ref_evap - Q_evap_actual) ** 2

        # 5. BHE state
        Q_bhe = Q_ref_evap - self.E_pmp
        Q_bhe_unit = Q_bhe / self.H_b

        # Fluid enters BHE at T_bhe_f_in_K
        T_bhe_f_in_K = T_evap_in_K - Q_ref_evap / m_dot_cp_b
        T_bhe_f_out_K = T_source_K

        T_bhe_f = (cu.K2C(T_bhe_f_in_K) + cu.K2C(T_bhe_f_out_K)) / 2
        T_bhe = T_bhe_f + Q_bhe_unit * self.R_b

        # 6. Assemble
        result: dict = cycle_states.copy()
        result.update(
            {
                "hp_is_on": True,
                "converged": True,
                "_penalty": penalty,
                "err_Q_evap [W]": err,
                "T_ref_evap_sat [°C]": cu.K2C(cycle_states.get("T_ref_evap_sat_K", np.nan)),
                "T_ref_cond_sat_v [°C]": cu.K2C(cycle_states.get("T_ref_cond_sat_l_K", np.nan)),
                "T_ref_cond_sat_l [°C]": cu.K2C(cycle_states.get("T_ref_cond_sat_l_K", np.nan)),
                "T0 [°C]": T0,
                "T_ref_cmp_in [°C]": cu.K2C(cycle_states.get("T_ref_cmp_in_K", np.nan)),
                "T_ref_cmp_out [°C]": cu.K2C(cycle_states.get("T_ref_cmp_out_K", np.nan)),
                "T_ref_exp_in [°C]": cu.K2C(cycle_states.get("T_ref_exp_in_K", np.nan)),
                "T_ref_exp_out [°C]": cu.K2C(cycle_states.get("T_ref_exp_out_K", np.nan)),
                "T_cond [°C]": cu.K2C(cycle_states.get("T_ref_cond_sat_l_K", np.nan)),
                "T_tank_w [°C]": T_tank_w,
                "T_mix_w_out [°C]": self.T_mix_w_out,
                "T_tank_w_in [°C]": self.T_tank_w_in,
                "Ts [°C]": self.Ts,
                "T_bhe [°C]": T_bhe,
                "T_bhe_f [°C]": T_bhe_f,
                "T_bhe_f_in [°C]": cu.K2C(T_bhe_f_in_K),
                "T_bhe_f_out [°C]": cu.K2C(T_bhe_f_out_K),
                "dV_bhe_f [m3/s]": self.dV_b_f_m3s,
                "dV_mix_w_out [m3/s]": flow_state.get("dV_mix_w_out", 0.0),
                "dV_tank_w_in [m3/s]": flow_state.get("dV_tank_w_in", 0.0),
                "dV_tank_w_out [m3/s]": flow_state.get("dV_tank_w_out", 0.0),
                "dV_mix_sup_w_in [m3/s]": flow_state.get("dV_mix_sup_w_in", 0.0),
                "P_ref_evap_sat [Pa]": cycle_states.get("P_ref_cmp_in [Pa]", np.nan),
                "P_ref_cond_sat_l [Pa]": cycle_states.get("P_ref_exp_in [Pa]", np.nan),
                "m_dot_ref [kg/s]": m_dot_ref,
                "cmp_rpm [rpm]": cmp_rps * 60,
                "h_ref_evap_sat [J/kg]": CP.PropsSI(
                    "H", "P", cycle_states.get("P_ref_cmp_in [Pa]", 1e5), "Q", 1, self.ref
                ),
                "h_ref_cond_sat_v [J/kg]": CP.PropsSI(
                    "H", "P", cycle_states.get("P_ref_cmp_out [Pa]", 1e6), "Q", 1, self.ref
                ),
                "h_ref_cond_sat_l [J/kg]": h_ref_exp_in,
                "Q_cond_load [W]": Q_cond_load,
                "Q_ref_cond [W]": Q_ref_cond,
                "Q_ref_evap [W]": Q_ref_evap,
                "Q_bhe [W]": Q_bhe,
                "E_cmp [W]": E_cmp,
                "E_pmp [W]": self.E_pmp,
                "E_tot [W]": E_cmp + self.E_pmp,
            }
        )
        return result

    def _optimize_operation(self, T_tank_w: float, Q_cond_load: float, T0: float, *, flow_state: dict):
        from scipy.optimize import brentq

        self._opt_evals = getattr(self, "_opt_evals", 0)

        def _objective(dT_evap):
            self._opt_evals += 1
            perf = self._calc_state(
                dT_ref_evap=dT_evap, T_tank_w=T_tank_w, Q_cond_load=Q_cond_load, T0=T0, flow_state=flow_state
            )
            if perf is None:
                raise ValueError(f"Cycle impossible at dT_evap={dT_evap}")

            err = perf.get("err_Q_evap [W]", np.nan)
            if np.isnan(err):
                raise ValueError(f"NaN error at dT_evap={dT_evap}")

            return err

        self._opt_evals = 0
        try:
            opt_x = brentq(_objective, 1, 20.0, xtol=1e-4, maxiter=50)

            class OptRes:
                success = True
                x = opt_x

            return OptRes()
        except Exception:

            class OptResFail:
                success = False
                x = np.nan

            return OptResFail()

    def _determine_hp_state(self, ctx: StepContext, is_on_prev: bool) -> tuple[bool, dict, float]:
        T_tank_w = cu.K2C(ctx.T_tank_w_K)

        hp_is_on = determine_heat_source_on_off(
            T_tank_w_C=T_tank_w,
            T_lower=self.T_tank_w_lower_bound,
            T_upper=self.T_tank_w_upper_bound,
            is_on_prev=is_on_prev,
            hour_of_day=ctx.hour_of_day,
            on_schedule=self.hp_on_schedule,
        )

        Q_cond_load = self.hp_capacity if hp_is_on else 0.0

        flow_state = self._calc_tank_flow_context(
            dV_mix_w_out=ctx.dV_mix_w_out,
            T_tank_w_K=ctx.T_tank_w_K,
            T_tank_w_in_K=self.T_tank_w_in_K,
            T_mix_w_out_K=self.T_mix_w_out_K,
        )

        if Q_cond_load <= self.Q_cond_LOAD_OFF_TOL:
            # OFF
            perf = self._calc_off_state(T_tank_w, cu.K2C(ctx.T0_K), flow_state=flow_state)
            return False, perf, 0.0
        else:
            # ON
            opt_res = self._optimize_operation(T_tank_w, Q_cond_load, cu.K2C(ctx.T0_K), flow_state=flow_state)
            if opt_res.success:
                opt_x = float(getattr(opt_res, "x", 0.0))
                perf = self._calc_state(opt_x, T_tank_w, Q_cond_load, cu.K2C(ctx.T0_K), flow_state=flow_state)
                if perf is None:
                    perf = self._calc_off_state(T_tank_w, cu.K2C(ctx.T0_K), flow_state=flow_state)
            else:
                perf = self._calc_off_state(T_tank_w, cu.K2C(ctx.T0_K), flow_state=flow_state)

            perf["hp_is_on"] = True
            perf["converged"] = opt_res.success
            Q_ref_cond_actual = perf.get("Q_ref_cond [W]", 0.0)
            if np.isnan(Q_ref_cond_actual):
                Q_ref_cond_actual = 0.0
            return True, perf, Q_ref_cond_actual

    # =============================================================
    # Hooks
    # =============================================================

    def _get_activation_flags(self, hour_of_day: float) -> dict[str, bool]:
        flags = {}
        if self.stc is not None:
            flags["stc"] = self.stc.is_preheat_on(hour_of_day)
        return flags

    def _needs_solar_input(self) -> bool:
        return self.stc is not None

    def _build_residual_fn(
        self,
        ctx: StepContext,
        ctrl: ControlState,
        dt_s: float,
        T_tank_w_in_K_n: float,
        T_sup_w_K_n: float,
        tank_level: float,
        sub_states: dict,
    ):
        def residual(T_cand_K: float) -> float:
            return tank_mass_energy_residual(
                [T_cand_K, tank_level],
                ctx,
                ctrl,
                dt_s,
                T_tank_w_in_K_n,
                T_sup_w_K_n,
                self.T_mix_w_out_K,
                self.C_tank,
                self.UA_tank,
                self.V_tank_full,
                self._subsystems,
                sub_states,
            )[0]

        return residual

    def _run_subsystems(
        self,
        ctx: StepContext,
        ctrl: ControlState,
        dt: float,
        T_tank_w_in_K: float,
    ) -> dict[str, dict]:
        states = {}
        for name, sub in self._subsystems.items():
            if hasattr(sub, "step"):
                states[name] = sub.step(ctx, ctrl, dt, T_tank_w_in_K)
        return states

    def _augment_results(
        self,
        r: dict,
        ctx: StepContext,
        ctrl: ControlState,
        sub_states: dict[str, dict],
        T_solved_K: float,
    ) -> dict:
        for name, sub in self._subsystems.items():
            if hasattr(sub, "assemble_results"):
                sub_record = sub.assemble_results(
                    ctx,
                    ctrl,
                    sub_states.get(name, {}),
                    T_solved_K,
                )
                r.update(sub_record)
        return r

    def _postprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.postprocess_exergy(df)

    def _assemble_core_results(
        self, ctx: StepContext, ctrl: ControlState, T_solved_K: float, level_solved: float, perf: dict, flow_state: dict
    ) -> dict:
        r = perf.copy()
        r["T_tank_w [°C]"] = cu.K2C(T_solved_K)
        r["T0 [°C]"] = cu.K2C(ctx.T0_K)
        r["hp_is_on"] = ctrl.is_on

        Q_tank_loss = self.UA_tank * (T_solved_K - ctx.T0_K)
        mix = calc_mixing_valve_temp(T_solved_K, self.T_tank_w_in_K, self.T_mix_w_out_K)
        r["T_mix_w_out [°C]"] = cu.K2C(mix["T_mix_w_out_K"])

        r["Q_tank_loss [W]"] = Q_tank_loss
        r["dV_mix_w_out [m3/s]"] = ctx.dV_mix_w_out
        r["dV_tank_w_in [m3/s]"] = flow_state["dV_tank_w_in"]
        r["dV_tank_w_out [m3/s]"] = flow_state["dV_tank_w_out"]
        r["dV_mix_sup_w_in [m3/s]"] = flow_state["dV_mix_sup_w_in"]
        r["tank_level [-]"] = 1.0  # lumped capacitance

        if not self.tank_always_full or (self.tank_always_full and self.prevent_simultaneous_flow):
            r["tank_level [-]"] = level_solved

        r.pop("_penalty", None)

        return r

    # _compute_bhe_superposition removed: river water operates as infinite capacity boundary.

    # =============================================================
    # Orchestration
    # =============================================================

    def analyze_dynamic(
        self,
        simulation_period_sec: float,
        dt_s: float,
        T_tank_w_init_C: float,
        dhw_usage_schedule,
        T0_schedule,
        I_DN_schedule=None,
        I_dH_schedule=None,
        T_sup_w_schedule=None,
        T_source_w_schedule=None,
        tank_level_init: float = 1.0,
        result_save_csv_path=None,
    ) -> pd.DataFrame:
        from scipy.optimize import fsolve

        time = np.arange(0, simulation_period_sec, dt_s)
        tN = len(time)
        T0_schedule = np.array(T0_schedule)

        if I_DN_schedule is None:
            I_DN_schedule = np.zeros(tN)
        if I_dH_schedule is None:
            I_dH_schedule = np.zeros(tN)

        if T_sup_w_schedule is not None:
            T_sup_w_arr = np.array(T_sup_w_schedule, dtype=float)
        else:
            T_sup_w_arr = np.full(tN, cu.K2C(self.T_tank_w_in_K))

        if T_source_w_schedule is not None:
            T_source_w_arr = np.array(T_source_w_schedule, dtype=float)
        else:
            T_source_w_arr = np.full(tN, self.Ts)

        results_data = []

        self.time = time
        self.dt = dt_s

        T_tank_w_K = cu.C2K(T_tank_w_init_C)
        tank_level = tank_level_init
        is_on_prev = False
        is_refilling = False

        self.T_bhe = self.Ts
        self.T_bhe_f_in = self.Ts
        self.T_bhe_f_in_K = self.Ts_K
        self.T_bhe_f_out = self.Ts
        self.Q_bhe = 0.0

        # DHW schedule handling: direct m³/s flow array
        dhw_flow_m3s = np.asarray(dhw_usage_schedule, dtype=float)
        if len(dhw_flow_m3s) != tN:
            raise ValueError(f"dhw_usage_schedule length ({len(dhw_flow_m3s)}) != tN ({tN})")

        _use_solar = self._needs_solar_input()

        for n in tqdm(range(tN), desc="GSHPB Simulating"):
            t_s = time[n]
            hr = t_s * cu.s2h
            hour_of_day = (t_s % (24 * 3600)) * cu.s2h

            T0_K = cu.C2K(T0_schedule[n])
            T_sup_w_n = T_sup_w_arr[n]
            T_sup_w_K_n = cu.C2K(T_sup_w_n)

            # Set boundary condition for water source
            T_source_w_n = T_source_w_arr[n]
            if np.isnan(T_source_w_n):
                # Fallback to last known BHE wall temperature when source schedule has NaN.
                # WARNING: if all schedule values are NaN, this silently uses self.Ts (init value).
                if n == 0 or n % 43200 == 0:  # Log at start and every ~30 days
                    import warnings
                    warnings.warn(
                        f"[WSHPB] T_source_w_schedule[{n}] is NaN — falling back to "
                        f"T_bhe={self.T_bhe:.2f}°C. Check NIER data quality.",
                        RuntimeWarning,
                        stacklevel=2,
                    )
                T_source_w_n = self.T_bhe  # fallback to last known valid
            T_source_w_K_n = cu.C2K(T_source_w_n)

            # Subsystem activation
            activation_flags = self._get_activation_flags(hour_of_day)

            dV_mix_w_out = dhw_flow_m3s[n]

            ctx = StepContext(
                n=n,
                current_time_s=t_s,
                current_hour=hr,
                hour_of_day=hour_of_day,
                T0=T0_schedule[n],
                T0_K=T0_K,
                activation_flags=activation_flags,
                T_tank_w_K=T_tank_w_K,
                tank_level=tank_level,
                dV_mix_w_out=dV_mix_w_out,
                I_DN=I_DN_schedule[n] if _use_solar else 0.0,
                I_dH=I_dH_schedule[n] if _use_solar else 0.0,
                T_sup_w_K=T_sup_w_K_n,
            )

            # --- Phase A: Control Decisions ---
            hp_is_on, hp_result, Q_ref_cond = self._determine_hp_state(ctx, is_on_prev)
            is_on_prev = hp_is_on

            # Refill logic
            flow_state_guess = self._calc_tank_flow_context(
                dV_mix_w_out=ctx.dV_mix_w_out,
                T_tank_w_K=ctx.T_tank_w_K,
                T_tank_w_in_K=T_sup_w_K_n,
                T_mix_w_out_K=self.T_mix_w_out_K,
            )
            dV_tank_w_in_ctrl, is_refilling = determine_tank_refill_flow(
                dt=dt_s,
                tank_level=ctx.tank_level,
                dV_tank_w_out=flow_state_guess["dV_tank_w_out"],
                V_tank_full=self.V_tank_full,
                tank_always_full=self.tank_always_full,
                prevent_simultaneous_flow=self.prevent_simultaneous_flow,
                tank_level_lower_bound=self.tank_level_lower_bound,
                tank_level_upper_bound=self.tank_level_upper_bound,
                dV_tank_w_in_refill=self.dV_tank_w_in_refill,
                is_refilling=is_refilling,
            )

            ctrl = ControlState(
                is_on=hp_is_on,
                Q_heat_source=Q_ref_cond,
                dV_tank_w_in_ctrl=dV_tank_w_in_ctrl,
            )

            # --- Phase B: Implicit Solving ---
            sub_states = self._run_subsystems(ctx, ctrl, dt_s, T_sup_w_K_n)

            alp_prev: float = min(
                1.0, max(0.0, (self.T_mix_w_out_K - T_sup_w_K_n) / max(1e-6, ctx.T_tank_w_K - T_sup_w_K_n))
            )
            dV_tank_w_out_prev = alp_prev * ctx.dV_mix_w_out
            dV_tank_w_in_prev = dV_tank_w_out_prev if ctrl.dV_tank_w_in_ctrl is None else ctrl.dV_tank_w_in_ctrl
            tank_vol_change_prev = (dV_tank_w_in_prev - dV_tank_w_out_prev) * dt_s
            level_next_approx = min(1.0, max(0.0, ctx.tank_level + tank_vol_change_prev / self.V_tank_full))
            tank_level_solve = max(0.001, level_next_approx)

            res_fn = self._build_residual_fn(
                ctx=ctx,
                ctrl=ctrl,
                dt_s=dt_s,
                T_tank_w_in_K_n=T_sup_w_K_n,
                T_sup_w_K_n=T_sup_w_K_n,
                tank_level=tank_level_solve,
                sub_states=sub_states,
            )

            from typing import cast

            T_guess_K = ctx.T_tank_w_K
            try:
                T_solved_K_arr = cast(np.ndarray, fsolve(res_fn, x0=[T_guess_K]))
                T_solved_K = float(T_solved_K_arr[0])
            except Exception:
                # explicit Euler fallback
                Q_hp_val = ctrl.Q_heat_source
                Q_flow_curr = c_w * rho_w * dV_tank_w_out_prev * (T_sup_w_K_n - ctx.T_tank_w_K)
                Q_loss_curr = self.UA_tank * (ctx.T_tank_w_K - ctx.T0_K)
                Q_tot = Q_hp_val + Q_flow_curr - Q_loss_curr
                T_solved_K = ctx.T_tank_w_K + dt_s * Q_tot / (self.C_tank * tank_level_solve)

            if T_solved_K <= T_sup_w_K_n:
                T_solved_K = T_sup_w_K_n

            # Flow state evaluated at solved temperature
            flow_state_final = self._calc_tank_flow_context(
                dV_mix_w_out=ctx.dV_mix_w_out,
                T_tank_w_K=T_solved_K,
                T_tank_w_in_K=T_sup_w_K_n,
                T_mix_w_out_K=self.T_mix_w_out_K,
                dV_tank_w_in_override=ctrl.dV_tank_w_in_ctrl,
            )

            tank_vol_change_final = (flow_state_final["dV_tank_w_in"] - flow_state_final["dV_tank_w_out"]) * dt_s
            level_next = min(1.0, max(0.0, ctx.tank_level + tank_vol_change_final / self.V_tank_full))

            # Heat extraction calculation for reporting
            Q_bhe_unit = hp_result.get("Q_bhe [W]", 0.0) / self.H_b if hp_is_on else 0.0
            self.Q_bhe = Q_bhe_unit * self.H_b
            m_cp_b = c_w * rho_w * self.dV_b_f_m3s

            # Infinite heat capacity boundary (River/Lake), no ground interference
            self.T_bhe = T_source_w_n
            T_bhe_K = cu.C2K(self.T_bhe)

            # Thermal resistance of pipe
            T_bhe_f_K = T_bhe_K - Q_bhe_unit * self.R_b
            self.T_bhe_f = cu.K2C(T_bhe_f_K)

            # Assume symmetrical temperature approach around average BHE fluid temperature
            dT_bhe_f_half = float((self.Q_bhe / m_cp_b) / 2) if m_cp_b > 0 else 0.0
            self.T_bhe_f_in_K = T_bhe_f_K - dT_bhe_f_half
            self.T_bhe_f_in = cu.K2C(self.T_bhe_f_in_K)
            T_bhe_f_out_K = T_bhe_f_K + dT_bhe_f_half
            self.T_bhe_f_out = cu.K2C(T_bhe_f_out_K)
            self.T_bhe_f_out_K = T_bhe_f_out_K

            # Apply BHE state to hp_result
            hp_result["Ts [°C]"] = T_source_w_n  # Override: record timestep-specific river water temp (not the static init value self.Ts)
            hp_result["T_bhe [°C]"] = self.T_bhe
            hp_result["T_bhe_f [°C]"] = self.T_bhe_f
            hp_result["T_bhe_f_in [°C]"] = self.T_bhe_f_in
            hp_result["T_bhe_f_out [°C]"] = self.T_bhe_f_out

            # Assemble step results
            step_record = self._assemble_core_results(ctx, ctrl, T_solved_K, level_next, hp_result, flow_state_final)
            self._augment_results(step_record, ctx, ctrl, sub_states, T_solved_K)
            results_data.append(step_record)

            # Step forward
            T_tank_w_K = T_solved_K
            tank_level = level_next

        results_df = pd.DataFrame(results_data)
        results_df.ffill(inplace=True)
        results_df = self._postprocess(results_df)

        if result_save_csv_path:
            results_df.to_csv(result_save_csv_path, index=False)

        return results_df

    def analyze_steady(
        self,
        T_tank_w: float,
        T_source: float,
        Q_ref_cond: float,
        T0: float = 0.0,
        *,
        return_dict: bool = True,
    ) -> dict | pd.DataFrame:
        """Run a steady-state performance snapshot.

        Evaluates the refrigerant cycle at a given operating point
        (``T_tank_w``, ``T_source``, ``Q_ref_cond``) **without** solving the tank energy
        balance or tracking dynamic flows.

        Parameters
        ----------
        T_tank_w : float
            Tank water temperature [°C] — treated as a given input.
        T_source : float
            Source fluid temperature entering the heat pump [°C].
        Q_ref_cond : float
            Target condenser heat rate [W].
        T0 : float
            Dead-state / outdoor-air temperature [°C] (for exergy calculations).
        return_dict : bool
            If ``True`` return dict; else single-row DataFrame.

        Returns
        -------
        dict | pd.DataFrame
        """
        import warnings
        import contextlib

        # Empty flow state as steady state ignores dynamic withdrawal/refill
        flow_state = {
            "dV_mix_w_out": 0.0,
            "dV_tank_w_out": 0.0,
            "dV_tank_w_in": 0.0,
            "dV_mix_sup_w_in": 0.0,
            "alp": 0.0,
        }

        # Override T_bhe_f_out_K so that _calc_state uses T_source correctly
        self.T_bhe_f_out_K = cu.C2K(T_source)

        if Q_ref_cond <= 0:
            result = self._calc_off_state(
                T_tank_w=T_tank_w,
                T0=T0,
                flow_state=flow_state,
            )
        else:
            opt_result = self._optimize_operation(
                T_tank_w=T_tank_w,
                Q_cond_load=Q_ref_cond,
                T0=T0,
                flow_state=flow_state,
            )
            result = None
            with contextlib.suppress(Exception):
                opt_x = float(getattr(opt_result, "x", 5.0))
                result = self._calc_state(
                    dT_ref_evap=opt_x,
                    T_tank_w=T_tank_w,
                    Q_cond_load=Q_ref_cond,
                    T0=T0,
                    flow_state=flow_state,
                )

            if result is None or not isinstance(result, dict):
                warnings.warn(
                    f"analyze_steady: optimization failed "
                    f"(T_tank_w={T_tank_w:.1f}°C, T_source={T_source:.1f}°C, "
                    f"Q_ref_cond={Q_ref_cond:.0f}W). "
                    "Returning HP-off state.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                try:
                    result = self._calc_state(
                        dT_ref_evap=5.0,
                        T_tank_w=T_tank_w,
                        Q_cond_load=0.0,
                        T0=T0,
                        flow_state=flow_state,
                    )
                except Exception:
                    result = self._calc_off_state(
                        T_tank_w=T_tank_w,
                        T0=T0,
                        flow_state=flow_state,
                    )

            if (
                result is not None
                and isinstance(result, dict)
                and "opt_result" in locals()
                and hasattr(opt_result, "success")
            ):
                result["converged"] = opt_result.success

        if result is None:
            result = {}

        if result:
            # Steady state doesn't have tank loss because we don't solve tank mass/energy balance
            result["Q_tank_loss [W]"] = 0.0
            result["tank_level [-]"] = 1.0  # steady-state: always_full

        if return_dict:
            return result
        return pd.DataFrame([result])

    def postprocess_exergy(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute GSHPB-specific exergy variables."""
        from .thermodynamics import calc_energy_flow, calc_refrigerant_exergy, convert_electricity_to_exergy

        df = df.copy()
        T0_K = cu.C2K(df["T0 [°C]"])
        T_tank_K = cu.C2K(df["T_tank_w [°C]"])

        df["Q_tank_w_out [W]"] = calc_energy_flow(c_w * rho_w * df["dV_tank_w_out [m3/s]"].fillna(0), T_tank_K, T0_K)

        # 1. Refrigerant state points
        df = calc_refrigerant_exergy(df, self.ref, T0_K)
        df = convert_electricity_to_exergy(df)

        # 2. Exergy flows
        G_b = c_w * rho_w * df["dV_bhe_f [m3/s]"]
        T_bhe_f_in_K = cu.C2K(df["T_bhe_f_in [°C]"])
        T_bhe_f_out_K = cu.C2K(df["T_bhe_f_out [°C]"])

        # Exergy at BHE boundaries
        X_bhe_in = calc_exergy_flow(G_b, T_bhe_f_in_K, T0_K)
        X_bhe_out = calc_exergy_flow(G_b, T_bhe_f_out_K, T0_K)

        # Fluid enters evaporator after being heated by the pump
        T_evap_in_K = T_bhe_f_out_K + df["E_pmp [W]"] / G_b.replace(0, np.nan)
        X_evap_in = calc_exergy_flow(G_b, T_evap_in_K, T0_K)

        # Fluid leaves evaporator and enters BHE
        X_evap_out = X_bhe_in

        df["X_ref_cond [W]"] = df["Q_ref_cond [W]"] * (1 - T0_K / cu.C2K(df["T_ref_cond_sat_v [°C]"]))
        df["X_ref_evap [W]"] = df["Q_ref_evap [W]"] * (1 - T0_K / cu.C2K(df["T_ref_evap_sat [°C]"]))

        df["X_tank_w_in [W]"] = calc_exergy_flow(
            c_w * rho_w * df["dV_tank_w_in [m3/s]"].fillna(0), cu.C2K(df["T_tank_w_in [°C]"]), T0_K
        )
        df["X_tank_w_out [W]"] = calc_exergy_flow(c_w * rho_w * df["dV_tank_w_out [m3/s]"].fillna(0), T_tank_K, T0_K)

        df["X_mix_w_out [W]"] = calc_exergy_flow(
            c_w * rho_w * df["dV_mix_w_out [m3/s]"].fillna(0), cu.C2K(df["T_mix_w_out [°C]"]), T0_K
        )
        df["X_mix_sup_w_in [W]"] = calc_exergy_flow(
            c_w * rho_w * df["dV_mix_sup_w_in [m3/s]"].fillna(0), cu.C2K(df["T_tank_w_in [°C]"]), T0_K
        )

        df["X_tank_loss [W]"] = df["Q_tank_loss [W]"] * (1 - T0_K / T_tank_K)

        tank_lvl = df["tank_level [-]"].fillna(1.0) if "tank_level [-]" in df.columns else 1.0
        C_tank_actual = self.C_tank * tank_lvl
        T_tank_K_prev = T_tank_K.shift(1)
        df["Xst_tank [W]"] = (1 - T0_K / T_tank_K) * C_tank_actual * (T_tank_K - T_tank_K_prev) / self.dt
        df.loc[df.index[0], "Xst_tank [W]"] = 0.0

        import typing

        # Subsystems exergy
        X_sub_tot_add = typing.cast(typing.Any, 0.0)
        X_sub_in_tank_add = typing.cast(typing.Any, 0.0)
        X_sub_out_tank_add = typing.cast(typing.Any, 0.0)

        for _name, sub in self._subsystems.items():
            if hasattr(sub, "calc_exergy"):
                ex_res = sub.calc_exergy(df, T0_K)
                if ex_res is not None:
                    for col_name, s in ex_res.columns.items():
                        df[col_name] = s
                    X_sub_tot_add = X_sub_tot_add + ex_res.X_tot_add
                    X_sub_in_tank_add = X_sub_in_tank_add + ex_res.X_in_tank_add
                    X_sub_out_tank_add = X_sub_out_tank_add + ex_res.X_out_tank_add

        # Components Destruction
        df["X_tot [W]"] = df["E_cmp [W]"] + df["E_pmp [W]"] + df.get("X_uv [W]", 0.0) + X_sub_tot_add

        df["Xc_cmp [W]"] = df["X_cmp [W]"] + df["X_ref_cmp_in [W]"] - df["X_ref_cmp_out [W]"]
        df["Xc_cond [W]"] = (df["X_ref_cmp_out [W]"] - df["X_ref_exp_in [W]"]) - df["X_ref_cond [W]"]
        df["Xc_exp [W]"] = df["X_ref_exp_in [W]"] - df["X_ref_exp_out [W]"]
        df["Xc_evap [W]"] = (X_evap_in - X_evap_out) - df["X_ref_evap [W]"]
        df["Xc_pmp [W]"] = df["E_pmp [W]"] - (X_evap_in - X_bhe_out)

        X_in_tank = df["X_ref_cond [W]"] + df["X_tank_w_in [W]"].fillna(0) + df.get("X_uv [W]", 0.0) + X_sub_in_tank_add
        X_out_tank = df["Xst_tank [W]"] + df["X_tank_w_out [W]"].fillna(0) + X_sub_out_tank_add
        df["Xc_tank [W]"] = X_in_tank - X_out_tank

        df["Xc_mix [W]"] = (
            df["X_tank_w_out [W]"].fillna(0) + df["X_mix_sup_w_in [W]"].fillna(0) - df["X_mix_w_out [W]"].fillna(0)
        )

        # Efficiency
        df["X_eff_ref [-]"] = df["X_ref_cond [W]"] / df["X_cmp [W]"].replace(0, np.nan)
        df["X_eff_sys [-]"] = df["X_ref_cond [W]"] / df["X_tot [W]"].replace(0, np.nan)

        return df
