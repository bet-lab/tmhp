"""
Utility functions for energy, entropy, and exergy analysis.

This module contains helper functions organized into the following categories:

1. Friction and Flow Functions
   - darcy_friction_factor: Calculate Darcy friction factor
   - calc_Orifice_flow_coefficient: Calculate orifice flow coefficient
   - calc_boussinessq_mixing_flow: Calculate mixing flow based on Boussinesq approximation

2. Heat Transfer Functions
   - calc_h_vertical_plate: Natural convection heat transfer coefficient
   - calc_UA_tank_arr: Tank heat loss UA calculation
   - calc_lmtd_*: Log mean temperature difference calculations
   - calc_UA_from_dV_fan: Heat transfer coefficient from fan flow rate

3. Curve Fitting Functions
   - linear_function, quadratic_function, cubic_function, quartic_function

4. Exergy and Entropy Functions
   - generate_entropy_exergy_term: Calculate entropy and exergy terms
   - calc_exergy_flow: Calculate exergy flow rate due to material flow

5. G-function Calculations (Ground Source Heat Pumps)
   - f, chi, G_FLS: Helper functions for g-function calculation

6. TDMA Solver Functions
   - TDMA: Solve tri-diagonal matrix system
   - _add_loop_advection_terms: Add forced convection terms to TDMA coefficients

7. Heat Pump Cycle Functions
   - calculate_ASHP_*_COP: Air source heat pump COP calculations
   - calculate_GSHP_COP: Ground source heat pump COP calculation
   - calc_ref_state: Calculate refrigerant cycle states (with superheating/subcooling support)
   - find_ref_loop_optimal_operation: Find optimal operation point
8. Tank Functions
   - update_tank_temperature: Update tank temperature based on energy balance

9. Schedule Functions
   - _build_dhw_usage_ratio: Build schedule ratio array

10. Balance Printing Utilities
    - print_balance: Print energy/entropy/exergy balance
"""

import math

import numpy as np
from scipy.optimize import root_scalar

from . import calc_util as cu
from .constants import c_a, c_w, rho_a, rho_w
from .cop import (
    calc_ASHP_cooling_COP as calc_ASHP_cooling_COP,
)
from .cop import (
    calc_ASHP_heating_COP as calc_ASHP_heating_COP,
)
from .cop import (
    calc_GSHP_COP as calc_GSHP_COP,
)
from .g_function import (
    G_FLS as G_FLS,
)
from .g_function import (
    air_dynamic_viscosity as air_dynamic_viscosity,
)
from .g_function import (
    air_prandtl_number as air_prandtl_number,
)
from .g_function import (
    chi as chi,
)
from .g_function import (
    f as f,
)
from .hx_fan import (
    calc_fan_power_from_dV_fan as calc_fan_power_from_dV_fan,
)
from .hx_fan import (
    calc_UA_from_dV_fan as calc_UA_from_dV_fan,
)
from .tdma import (
    TDMA as TDMA,
)
from .tdma import (
    _add_loop_advection_terms as _add_loop_advection_terms,
)
from .thermodynamics import (
    calc_energy_flow,
    calc_exergy_flow,
    calc_refrigerant_exergy,
    convert_electricity_to_exergy,
    generate_entropy_exergy_term,
)
from .uv_treatment import (
    calc_uv_exposure_time as calc_uv_exposure_time,
)
from .uv_treatment import (
    calc_uv_lamp_power as calc_uv_lamp_power,
)
from .uv_treatment import (
    get_uv_params_from_turbidity as get_uv_params_from_turbidity,
)

try:
    import dartwork_mpl as dm
except ImportError:
    # dartwork_mpl이 없는 경우를 대비한 fallback
    dm = None


def linear_function(x, a, b):
    """Linear function: y = a*x + b"""
    return a * x + b


def quadratic_function(x, a, b, c):
    """Quadratic function: y = a*x² + b*x + c"""
    return a * x**2 + b * x + c


def cubic_function(x, a, b, c, d):
    """Cubic function: y = a*x³ + b*x² + c*x + d"""
    return a * x**3 + b * x**2 + c * x + d


def quartic_function(x, a, b, c, d, e):
    """Quartic function: y = a*x⁴ + b*x³ + c*x² + d*x + e"""
    return a * x**4 + b * x**3 + c * x**2 + d * x + e


def print_balance(balance, decimal=2):
    """
    Print energy, entropy, or exergy balance dictionary in a formatted way.

    This function prints balance information for subsystems, categorizing entries
    into in, out, consumed, and generated categories.

    Parameters
    ----------
    balance : dict
        Dictionary containing balance information for subsystems.
        Structure: {subsystem_name: {category: {symbol: value}}}
        Categories: 'in', 'out', 'con' (consumed), 'gen' (generated)
    decimal : int, optional
        Number of decimal places for output (default: 2)

    Returns
    -------
    None
        Only prints output

    Example
    -------
    >>> balance = {
    ...     "hot water tank": {
    ...         "in": {"E_heater": 5000.0},
    ...         "out": {"Q_w_tank": 4500.0, "Q_l_tank": 400.0},
    ...         "con": {"X_c_tank": 100.0}
    ...     }
    ... }
    >>> print_balance(balance)
    """
    total_length = 50

    balance_type = "energy"
    unit = "[W]"

    # Determine balance type and unit from dictionary structure
    for _subsystem, category_dict in balance.items():
        for category, _terms in category_dict.items():
            if "gen" in category:
                balance_type = "entropy"
                unit = "[W/K]"
            elif "con" in category:
                balance_type = "exergy"

    # Print balance for each subsystem
    for subsystem, category_dict in balance.items():
        text = f"{subsystem.upper()} {balance_type.upper()} BALANCE:"
        print(f"\n\n{text}" + "=" * (total_length - len(text)))

        for category, terms in category_dict.items():
            print(f"\n{category.upper()} ENTRIES:")

            for symbol, value in terms.items():
                print(f"{symbol}: {round(value, decimal)} {unit}")


# COP, G-function, Air property, and TDMA functions are now in dedicated
# modules.  Re-exported here for backward compatibility.
# See: cop.py, g_function.py, tdma.py


# ============================================================================
# Exergy and Entropy Functions
# ============================================================================


# ============================================================================
# Flow and Mixing Functions
# ============================================================================


def calc_mixing_valve_temp(T_tank_w_K, T_tank_w_in_K, T_mix_w_out_K):
    """Calculate 3-way mixing valve output temperature and mixing ratio.

    Mixes hot tank water with cold mains water to achieve the target
    service temperature ``T_mix_w_out_K``.

    Parameters
    ----------
    T_tank_w_K : float
        Current tank water temperature [K].
    T_tank_w_in_K : float
        Mains (cold) water supply temperature [K].
    T_mix_w_out_K : float
        Target delivery temperature [K].

    Returns
    -------
    dict
        ``{'alp': float, 'T_mix_w_out': float, 'T_mix_w_out_K': float}``
        - ``alp``: hot-water fraction [0–1]
        - ``T_mix_w_out``: actual service temperature [°C]
        - ``T_mix_w_out_K``: actual service temperature [K]
    """
    den = max(1e-6, T_tank_w_K - T_tank_w_in_K)
    alp = min(1.0, max(0.0, (T_mix_w_out_K - T_tank_w_in_K) / den))

    T_mix_w_out_val_K = T_tank_w_K if alp >= 1.0 else alp * T_tank_w_K + (1 - alp) * T_tank_w_in_K

    T_mix_w_out_val = cu.K2C(T_mix_w_out_val_K)
    return {
        "alp": alp,
        "T_mix_w_out": T_mix_w_out_val,
        "T_mix_w_out_K": T_mix_w_out_val_K,
    }


def calc_mixing_valve_flows(
    dV_mix_out: float,
    alp: float
) -> dict:
    """
    Calculate volumetric flow rates at a 3-way mixing valve given a mixing ratio.

    Parameters
    ----------
    dV_mix_out : float
        Total requested service/mixed flow rate [m³/s].
    alp : float
        Hot water mixing ratio [0-1].

    Returns
    -------
    dict
        Dictionary containing generic mixing valve mass balances:
        - `dV_hot_in`: Flow rate drawn from the hot source [m³/s]
        - `dV_cold_in`: Flow rate drawn from the cold source [m³/s]
        - `dV_mix_out`: Total mixed flow rate [m³/s]
    """
    dV_hot_in = alp * dV_mix_out
    dV_cold_in = (1.0 - alp) * dV_mix_out

    return {
        "dV_hot_in": dV_hot_in,
        "dV_cold_in": dV_cold_in,
        "dV_mix_out": dV_mix_out,
    }


# UV functions have been moved to uv_treatment.py.
# Re-exported above via ``from .uv_treatment import …``


def calc_Orifice_flow_coefficient(D0, D1):
    """
    Calculate the orifice flow coefficient based on diameters.

    Flow configuration:
    ---------------
     ->      |
     D0     D1 ->
     ->      |
    ---------------

    Parameters
    ----------
    D0 : float
        Pipe diameter [m]
    D1 : float
        Hole diameter [m]

    Returns
    -------
    C_d : float
        Orifice flow coefficient (dimensionless)

    Notes
    -----
    This is a simplified calculation. A more complete implementation
    should be based on physical equations.
    """
    m = D1 / D0  # Opening ratio
    return m**2


def calc_boussinessq_mixing_flow(T_upper, T_lower, A, dz, C_d=0.1):
    """
    Calculate mixing flow rate between two adjacent nodes based on Boussinesq approximation.

    Mixing occurs only when the lower node temperature is higher than the upper node,
    creating a gravitationally unstable condition.

    Parameters
    ----------
    T_upper : float
        Upper node temperature [K]
    T_lower : float
        Lower node temperature [K]
    A : float
        Tank cross-sectional area [m²]
    dz : float
        Node height [m]
    C_d : float, optional
        Flow coefficient (empirical constant), default 0.1

    Returns
    -------
    dV_mix : float
        Volumetric flow rate exchanged between nodes [m3/s]

    Notes
    -----
    TODO: C_d value should be calculated based on physical equations.
    """
    from .constants import beta, g

    if T_upper < T_lower:
        # Upper is colder (higher density) -> unstable -> mixing occurs
        delta_T = T_lower - T_upper
        dV_mix = C_d * A * math.sqrt(2 * g * beta * delta_T * dz)
        return dV_mix  # From top to bottom
    else:
        # Stable condition -> no mixing
        return 0.0


# ============================================================================
# Tank Heat Transfer Functions
# ============================================================================


# ============================================================================
# TDMA Solver Functions
# ============================================================================


# TDMA and advection-term functions have been moved to tdma.py.
# Re-exported above via ``from .tdma import …`` for backward compatibility.


# calc_UA_from_dV_fan has been moved to hx_fan.py.
# Re-exported above via ``from .hx_fan import …``


def calc_HX_perf_for_target_heat(
    Q_ref_target,
    T_a_in_C=None,
    T_ref_sat_K=None,
    A_cross=None,
    UA_design=None,
    dV_fan_design=None,
    is_active=True,
    exponent=0.71,
    # Legacy parameters for backward compatibility
    T_ou_a_in_C=None,
    T_ref_evap_sat_K=None,
    T_ref_cond_sat_l_K=None,
):
    """ε-NTU 기반 공기측 열교환기 풍량 수치 해석.

    This function determines the airflow that is needed to meet a specified heat transfer demand, accounting for dynamic changes in the overall heat transfer coefficient (UA) as a function of flow velocity based on the correlation for fin-and-tube heat exchangers by Wang et al. (2000) where UA ∝ velocity^0.71.

    Parameters
    ----------
    Q_ref_target : float
        목표 열전달량 [W] (항상 양수).
    T_a_in_C : float, optional
        공기 입구 온도 [°C].
    T_ref_sat_K : float, optional
        냉매 포화 온도 [K] (일정 온도측).
    A_cross : float
        HX 단면적 [m²].
    UA_design : float
        설계 UA [W/K].
    dV_fan_design : float
        설계 팬 풍량 [m³/s].

    is_active : bool
        활성화 여부.
    exponent : float
        UA scaling exponent (default: 0.71).

    # Legacy Aliases (optional)
    T_ou_a_in_C : float, optional
        (하위 호환성) 과거 버전의 ``T_a_in_C`` 역할을 수행합니다.
    T_ref_evap_sat_K : float, optional
        (하위 호환성) 과거 버전의 ``T_ref_sat_K`` 역할을 수행합니다.
    T_ref_cond_sat_l_K : float, optional
        (하위 호환성) 과거 함수 시그니처 유지를 위한 미사용 파라미터입니다.

    Returns
    -------
    dict
        Dictionary containing:
            - dV_fan : Required air-side flow rate [m3/s]
            - UA : Actual heat exchanger overall heat transfer coefficient at solution point [W/K]
            - T_a_mid_C : air temperature between heat exchanger and fan [°C]
            - Q_air : Heat transfer rate at operating point [W]
            - epsilon : Effectiveness at operating point [–]
            - converged : Whether the solver converged
        Returns dict with all values as np.nan if is_active=False
    """
    # ── Legacy alias 하위호환 ──
    if T_a_in_C is None:
        T_a_in_C = T_ou_a_in_C
    if T_ref_sat_K is None:
        T_ref_sat_K = T_ref_evap_sat_K

    if not is_active or T_a_in_C is None or T_ref_sat_K is None:
        return {
            "converged": True,
            "dV_fan": np.nan,
            "UA": np.nan,
            "T_a_mid_C": np.nan,
            "Q_air": np.nan,
            "epsilon": np.nan,
            # Legacy keys
            "T_ou_a_mid": np.nan,
            "Q_ou_air": np.nan,
        }

    T_a_in_K = cu.C2K(T_a_in_C)

    if abs(Q_ref_target) < 1e-6:
        return {
            "converged": True,
            "dV_fan": 0.0,
            "UA": 0.0,
            "T_a_mid_C": T_a_in_C,
            "Q_air": 0.0,
            "epsilon": 0.0,
            # Legacy keys
            "T_ou_a_mid": T_a_in_C,
            "Q_ou_air": 0.0,
        }

    def _error_function(dV_fan):
        if dV_fan <= 0:
            return -Q_ref_target
        UA = calc_UA_from_dV_fan(dV_fan, dV_fan_design, A_cross, UA_design, exponent)
        C_air = c_a * rho_a * dV_fan
        epsilon = 1 - np.exp(-UA / C_air)
        # Heat transfer Q = C_air * epsilon * abs(T_air_in - T_ref_sat)
        Q_air = C_air * epsilon * abs(T_a_in_K - T_ref_sat_K)
        return Q_air - Q_ref_target

    # Search range: 1% to 100% of design flow
    dV_min = dV_fan_design * 0.05
    dV_max = dV_fan_design

    try:
        sol = root_scalar(_error_function, bracket=[dV_min, dV_max], method="bisect")
        dV_sol = sol.root
        converged = sol.converged
    except ValueError:
        # Optimization loop penalty handling: return failure flag
        return {
            "converged": False,
            "dV_fan": np.nan,
            "UA": np.nan,
            "T_a_mid_C": np.nan,
            "Q_air": np.nan,
            "epsilon": np.nan,
            "T_ou_a_mid": np.nan,
            "Q_ou_air": np.nan,
        }

    # Final calculations at solved point
    UA_sol = calc_UA_from_dV_fan(dV_sol, dV_fan_design, A_cross, UA_design, exponent)
    C_air_sol = c_a * rho_a * dV_sol
    eps_sol = 1 - np.exp(-UA_sol / C_air_sol) if dV_sol > 0 else 0.0

    # Exit air temperature (before fan heat if any)
    T_a_mid_K = T_a_in_K - (T_a_in_K - T_ref_sat_K) * eps_sol
    T_a_mid_C = cu.K2C(T_a_mid_K)
    Q_air_sol = C_air_sol * abs(T_a_in_K - T_a_mid_K)

    return {
        "converged": converged,
        "dV_fan": dV_sol,
        "UA": UA_sol,
        "T_a_mid_C": T_a_mid_C,
        "Q_air": Q_air_sol,
        "epsilon": eps_sol,
        # Legacy keys
        "T_ou_a_mid": T_a_mid_C,
        "Q_ou_air": Q_air_sol,
    }




# calc_fan_power_from_dV_fan and check_hp_schedule_active have been moved
# to hx_fan.py.  Re-exported above via ``from .hx_fan import …``


# get_uv_params_from_turbidity and calc_uv_exposure_time have been moved
# to uv_treatment.py.  Re-exported above via ``from .uv_treatment import …``


def update_tank_temperature(T_tank_w_K, Q_gain, UA_tank, T0_K, C_tank, dt):
    """Update tank temperature using the Crank-Nicolson implicit scheme.

    The governing ODE for a lumped-capacitance tank is:

        C dT/dt = Q_gain - UA (T - T0)

    Crank-Nicolson averages the loss term across both time levels:

        T^{n+1} = [(C/dt - UA/2) T^n + Q_gain + UA T0] / (C/dt + UA/2)

    This scheme is second-order accurate in time and unconditionally
    stable, eliminating the overshoot that Forward Euler can exhibit
    when dt is large relative to the thermal time constant C/UA.

    Parameters
    ----------
    T_tank_w_K : float
        Current tank temperature [K].
    Q_gain : float
        Total heat gain rate [W] (condenser, UV, STC, refill, etc.).
    UA_tank : float
        Overall tank heat-loss coefficient [W/K].
    T0_K : float
        Dead-state / ambient temperature [K].
    C_tank : float
        Tank thermal capacitance [J/K] (= c_w * rho_w * V_tank * level).
    dt : float
        Time step [s].

    Returns
    -------
    float
        Updated tank temperature [K].
    """
    a = C_tank / dt
    T_tank_w_K_new = ((a - UA_tank / 2) * T_tank_w_K + Q_gain + UA_tank * T0_K) / (a + UA_tank / 2)
    return T_tank_w_K_new


def calc_stc_performance(
    I_DN_stc,  # 직달일사 [W/m²]
    I_dH_stc,  # 확산일사 [W/m²]
    T_stc_w_in_K,  # STC 입수 온도 (저탕조 온도) [K]
    T0_K,  # 기준 온도 [K]
    A_stc_pipe,  # STC 파이프 면적 [m²]
    alpha_stc,  # 흡수율 [-]
    h_o_stc,  # 외부 대류 열전달계수 [W/m²K]
    h_r_stc,  # 공기층 복사 열전달계수 [W/m²K]
    k_ins_stc,  # 단열재 열전도도 [W/mK]
    x_air_stc,  # 공기층 두께 [m]
    x_ins_stc,  # 단열재 두께 [m]
    dV_stc,  # STC 유량 [m3/s]
    E_pump,  # 펌프 소모 전력 [W]
    is_active=True,  # 활성화 여부 (기본값: True)
):
    """
    Solar Thermal Collector (STC) 성능을 계산합니다.

    이 함수는 태양열 집열판의 열전달 분석을 수행합니다.
    enex_engine.py의 SolarAssistedGasBoiler.system_update() 로직을 참조하여 구현되었습니다.

    Parameters
    ----------
    I_DN_stc : float
        직달일사 [W/m²]
    I_dH_stc : float
        확산일사 [W/m²]
    T_stc_w_in_K : float
        STC 입수 온도 (저탕조 온도) [K]
    T0_K : float
        기준 온도 (환경 온도) [K]
    A_stc_pipe : float
        STC 파이프 면적 [m²]
    alpha_stc : float
        흡수율 [-]
    h_o_stc : float
        외부 대류 열전달계수 [W/m²K]
    h_r_stc : float
        공기층 복사 열전달계수 [W/m²K]
    k_ins_stc : float
        단열재 열전도도 [W/mK]
    x_air_stc : float
        공기층 두께 [m]
    x_ins_stc : float
        단열재 두께 [m]
    dV_stc : float
        STC 유량 [m3/s]
    E_pump : float
        펌프 소모 전력 [W]
    is_active : bool, optional
        활성화 여부 (기본값: True)
        is_active=False일 때 nan 값으로 채워진 딕셔너리 반환

    Returns
    -------
    dict
        계산 결과 딕셔너리:
        - I_sol_stc: 총 일사량 [W/m²]
        - Q_sol_stc: 태양열 흡수 열량 [W]
        - Q_stc_w_in: STC 입수 열량 [W]
        - Q_stc_w_out: STC 출수 열량 [W]
        - ksi_stc: 무차원 수 [-]
        - T_stc_w_out_K: STC 출수 온도 [K]
        - T_stc_w_final_K: 펌프 열 포함 최종 출수 온도 [K]
        - T_stc_w_in_K: STC 입수 온도 [K]
        - T_stc_K: 집열판 평균 온도 [K]
        - Q_l_stc: 집열판 열 손실 [W]
        Returns dict with all values as np.nan (except T_stc_w_out_K, T_stc_w_in_K = T_stc_w_in_K) if is_active=False

    Notes
    -----
    - 모든 변수명에 _stc 접미사를 사용하여 STC 관련 변수임을 명확히 구분합니다.
    - 열 손실은 Q_l_stc로 명명됩니다.
    - 엔트로피 및 엑서지 계산은 제거되었으며, CSV 파일 후처리를 통해 계산해야 합니다.
    """
    from .constants import k_a

    # U_stc 계산 (내부에서 계산)
    # Resistance [m²K/W]
    R_air_stc = x_air_stc / k_a
    R_ins_stc = x_ins_stc / k_ins_stc
    R_o_stc = 1 / h_o_stc
    R_r_stc = 1 / h_r_stc

    R1_stc = (R_r_stc * R_air_stc) / (R_r_stc + R_air_stc) + R_o_stc
    R2_stc = R_ins_stc + R_o_stc

    # U-value [W/m²K] (병렬)
    U1_stc = 1 / R1_stc
    U2_stc = 1 / R2_stc
    U_stc = U1_stc + U2_stc

    # is_active=False일 때 nan 값으로 채워진 딕셔너리 반환
    if not is_active:
        return {
            "I_sol_stc": np.nan,
            "Q_sol_stc": np.nan,
            "Q_stc_w_in": np.nan,
            "Q_stc_w_out": np.nan,
            "ksi_stc": np.nan,
            "T_stc_w_final_K": T_stc_w_in_K,  # 입수 온도와 동일
            "T_stc_w_out_K": T_stc_w_in_K,  # 입수 온도와 동일
            "T_stc_w_in_K": T_stc_w_in_K,
            "T_stc_K": np.nan,
            "Q_l_stc": np.nan,
        }

    # 총 일사량 계산
    I_sol_stc = I_DN_stc + I_dH_stc

    # 태양열 흡수 열량
    Q_sol_stc = I_sol_stc * A_stc_pipe * alpha_stc

    # Heat capacity flow rate
    G_stc = c_w * rho_w * dV_stc

    # 입수 열량 (기준 온도 기준) - calc_energy_flow 사용
    Q_stc_w_in = calc_energy_flow(G_stc, T_stc_w_in_K, T0_K)

    # 무차원 수 (효율 계수)
    ksi_stc = np.exp(-A_stc_pipe * U_stc / G_stc)

    # STC 출수 온도 계산
    T_stc_w_out_numerator = (
        T0_K
        + (
            Q_sol_stc
            + Q_stc_w_in
            + A_stc_pipe * U_stc * (ksi_stc * T_stc_w_in_K / (1 - ksi_stc))
            + A_stc_pipe * U_stc * T0_K
        )
        / G_stc
    )

    T_stc_w_out_denominator = 1 + (A_stc_pipe * U_stc) / ((1 - ksi_stc) * G_stc)

    T_stc_w_out_K = T_stc_w_out_numerator / T_stc_w_out_denominator
    T_stc_w_final_K = T_stc_w_out_K + E_pump / G_stc
    T_stc_K = 1 / (1 - ksi_stc) * T_stc_w_out_K - ksi_stc / (1 - ksi_stc) * T_stc_w_in_K

    # STC 출수 열량 - calc_energy_flow 사용
    Q_stc_w_out = calc_energy_flow(G_stc, T_stc_w_out_K, T0_K)

    # 집열판 열 손실
    Q_l_stc = A_stc_pipe * U_stc * (T_stc_K - T0_K)

    return {
        "I_sol_stc": I_sol_stc,
        "Q_sol_stc": Q_sol_stc,
        "Q_stc_w_in": Q_stc_w_in,
        "Q_stc_w_out": Q_stc_w_out,
        "ksi_stc": ksi_stc,
        "T_stc_w_final_K": T_stc_w_final_K,
        "T_stc_w_out_K": T_stc_w_out_K,
        "T_stc_w_in_K": T_stc_w_in_K,
        "T_stc_K": T_stc_K,
        "Q_l_stc": Q_l_stc,
    }
