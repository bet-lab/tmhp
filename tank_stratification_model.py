"""
Stratified tank model using TDMA (Tri-Diagonal Matrix Algorithm).

This module provides a 1D stratified hot-water tank model with vertical discretization.
The model uses effective thermal conductivity to account for both molecular conduction
and natural convection driven by buoyancy forces.
"""

import numpy as np

from .constants import beta, c_w, g, k_w, mu_w, rho_w
from .heat_transfer import calc_UA_tank_arr
from .tdma import TDMA, _add_loop_advection_terms


class StratifiedTankTDMA:
    """
    TDMA-based 1D stratified hot-water tank model (vertical discretization).

    This class models a cylindrical storage tank split into N vertical layers (nodes).
    Each node enforces an energy balance that includes:
    - Storage term via node thermal capacitance (C).
    - Effective thermal conduction between adjacent nodes using effective
      conductivity (k_eff) that accounts for both molecular conduction and
      natural convection driven by buoyancy forces.
    - Advection due to draw/inlet flow (G = rho_w * c_w * dV).
    - Heat loss to ambient through a per-node UA array (side for all nodes;
      bottom/top discs additionally for the end nodes).
    - Optional point heater applied at a single node.
    - Optional external loop advection across a node range in either direction,
      with loop heat input Q_loop.

    Effective Thermal Conductivity Approach:
    ----------------------------------------
    The model uses an effective thermal conductivity (k_eff) approach to
    integrate molecular conduction and natural convection effects. For each
    node pair (i, i+1), the effective conductivity is calculated based on:
    - Temperature difference (dT = T[i+1] - T[i])
    - Rayleigh number (Ra), which characterizes the buoyancy-driven flow
    - Nusselt number (Nu), which relates effective to molecular conductivity

    Stable stratification (dT < 0, upper warmer than lower):
    - Convection is suppressed, primarily molecular conduction
    - Nu ≈ 1.0 with small correction terms

    Unstable stratification (dT > 0, lower warmer than upper):
    - Natural convection enhances heat transfer
    - Nu > 1.0, increasing with Rayleigh number
    - Laminar (Ra < 1e7): Nu ∝ Ra^0.25
    - Turbulent (Ra ≥ 1e7): Nu ∝ Ra^0.33

    The effective conduction coefficient between nodes is:
    K_eff = k_eff * A / dh, where k_eff = k_molecular * Nu

    The semi-implicit time advance assembles a tri-diagonal linear system
    a, b, c, d and solves it with a TDMA routine (see TDMA()) to obtain
    next-step temperatures.

    Units
    - Temperatures: K
    - Geometry: m
    - Volumetric flow: m³/s
    - UA, K: W/K
    - Heater power, heat flows: W

    Parameters
    ----------
    H : float
        Tank height [m].
    N : int
        Number of vertical layers (nodes).
    r0 : float
        Inner radius of tank [m] (D = 2*r0).
    x_shell : float
        Shell thickness [m].
    x_ins : float
        Insulation thickness [m].
    k_shell : float
        Shell thermal conductivity [W/mK].
    k_ins : float
        Insulation thermal conductivity [W/mK].
    h_w : float
        Internal convective heat transfer coefficient (water side) [W/m²K].
    h_o : float
        External convective heat transfer coefficient (ambient side) [W/m²K].
    C_d_mix : float
        Empirical discharge coefficient for buoyancy-driven mixing [-].
        (Note: This parameter is retained for compatibility but is not used
        in the effective conductivity approach.)

    Attributes
    ----------
    H, D, N : float, float, int
        Geometry and discretization (D = 2*r0).
    A : float
        Cross-sectional area [m²].
    dh : float
        Layer height [m].
    V : float
        Per-node volume [m³].
    UA : np.ndarray
        Node-to-ambient UA per node [W/K], shape (N,).
    K : float
        Reference axial conduction equivalent between nodes [W/K]
        (based on molecular conductivity only, for reference).
    C : float
        Per-node thermal capacitance [J/K].
    C_d_mix : float
        Mixing discharge coefficient [-] (retained for compatibility).
    g : float
        Gravitational acceleration [m/s²].
    beta : float
        Volumetric expansion coefficient of water [1/K].
    nu : float
        Kinematic viscosity of water [m²/s].
    alpha : float
        Thermal diffusivity of water [m²/s].
    Pr : float
        Prandtl number [-].
    k_molecular : float
        Molecular thermal conductivity of water [W/m·K].
    Ra_critical : float
        Critical Rayleigh number for stable stratification (≈1708).
    k_eff : np.ndarray
        Effective thermal conductivity between node pairs [W/m·K],
        shape (N-1,), updated during each time step.
    K_eff : np.ndarray
        Effective conduction coefficient between node pairs [W/K],
        shape (N-1,), updated during each time step.
    G_use, G_loop : float
        Flow-related terms cached from the last update step.

    Methods
    -------
    effective_conductivity(T_upper, T_lower)
        Calculate effective thermal conductivity between two nodes based on
        temperature difference and Rayleigh number.
    update_tank_temp(...)
        Advance temperatures by one time step using the TDMA scheme.
        Heater and optional external loop can be applied. Heater and loop
        node indices are 1-based in the public API.
    info(as_dict=False, precision=3)
        Print or return a concise summary of model geometry and thermal properties.

    Notes
    -----
    - Heater/loop node indices are 1-based (converted to 0-based internally).
    - External loop terms are added to the TDMA coefficients to represent
      directed advection across a node range.
    - The effective conductivity approach replaces the previous Boussinesq
      mixing flow model, providing a more physically consistent representation
      of heat transfer in stratified tanks.
    """

    def __init__(self, H, N, r0, x_shell, x_ins, k_shell, k_ins, h_w, h_o, C_d_mix):
        self.H = H
        self.D = 2 * r0
        self.N = N
        self.A = np.pi * (self.D**2) / 4.0
        self.dh = H / N
        self.V = self.A * self.dh
        self.UA = calc_UA_tank_arr(r0, x_shell, x_ins, k_shell, k_ins, H, N, h_w, h_o)
        self.K = k_w * self.A / self.dh
        self.C = c_w * rho_w
        self.C_d_mix = C_d_mix

        # Water transport properties (for effective conductivity calculation)
        self.g = g  # Gravitational acceleration [m/s²]
        self.beta = beta  # Volumetric expansion coefficient [1/K]
        self.nu = mu_w / rho_w  # Kinematic viscosity [m²/s]
        self.alpha = k_w / (rho_w * c_w)  # Thermal diffusivity [m²/s]
        self.Pr = (mu_w / rho_w) / (k_w / (rho_w * c_w))  # Prandtl number [-]
        self.k_molecular = k_w  # Molecular thermal conductivity [W/m·K]
        self.Ra_critical = 1708  # Critical Rayleigh number (horizontal layer)

    def effective_conductivity(self, T_upper, T_lower):
        """Calculate effective thermal conductivity between two adjacent nodes.

        Integrates molecular conduction and buoyancy-driven natural convection
        into a single effective conductivity using the Rayleigh–Nusselt approach.

        Stable stratification (dT < 0, upper warmer):
            Convection is suppressed; heat transfer is primarily by conduction.
            Nu ≈ 1.0 with a small correction term.

        Unstable stratification (dT > 0, lower warmer):
            Buoyancy drives natural convection, enhancing heat transfer.
            - Ra < 1e3:  Nu = 1.0 (conduction-dominated)
            - Ra < 1e7:  Nu = 0.2 · Ra^0.25 (laminar convection)
            - Ra ≥ 1e7:  Nu = 0.1 · Ra^0.33 (turbulent convection)

        Parameters
        ----------
        T_upper : float
            Temperature of the upper node [K].
        T_lower : float
            Temperature of the lower node [K].

        Returns
        -------
        k_eff : float
            Effective thermal conductivity [W/m·K].

        References
        ----------
        Incropera & DeWitt, *Fundamentals of Heat and Mass Transfer*, 7th ed.
        Bejan, *Convection Heat Transfer*, 4th ed.
        """
        k_molecular = self.k_molecular  # Molecular conductivity [W/m·K]
        dT = T_lower - T_upper  # Temperature difference [K]
        L_char = self.dh  # Characteristic length = node height [m]

        # Rayleigh number: ratio of buoyancy to viscous forces
        Ra = abs(self.g * self.beta * dT * L_char**3) / (self.nu * self.alpha)

        # Stable stratification (upper warmer, dT < 0) — convection suppressed
        if dT < 0:
            Nu = 1.0 + 0.1 * (Ra / self.Ra_critical) ** 0.25 if Ra > 0 else 1.0

        # Unstable stratification (lower warmer, dT > 0) — buoyancy-driven convection
        else:
            if Ra < 1e3:
                Nu = 1.0  # Conduction-dominated
            elif Ra < 1e7:
                Nu = 0.2 * Ra**0.25  # Laminar convection
            else:
                Nu = 0.1 * Ra**0.33  # Turbulent convection

        # Effective conductivity: k_eff = k_molecular · Nu
        k_eff = k_molecular * Nu

        return k_eff

    # ═══ Time-stepping ═════════════════════════════════════════════════════

    def update_tank_temp(
        self,
        T,
        dt,
        T_in,
        dV_use,
        T_amb,
        T0,
        heater_node=None,
        heater_capacity=None,
        loop_outlet_node=None,
        loop_inlet_node=None,
        dV_loop=0.0,
        Q_loop=0.0,
    ):
        """Advance node temperatures by one time step using the TDMA scheme.

        Parameters
        ----------
        T : np.ndarray
            Current node temperature array [K], shape (N,).
        dt : float
            Time step size [s].
        T_in : float
            Inlet (mains) water temperature [K].
        dV_use : float
            Draw-off volumetric flow rate [m³/s].
        T_amb : float
            Ambient temperature [K].
        T0 : float
            Dead-state (reference) temperature for exergy [K].
        heater_node : int, optional
            1-based node index where the heater is located.
        heater_capacity : float, optional
            Heater thermal output [W].
        loop_outlet_node : int, optional
            1-based node index where the external loop exits the tank.
        loop_inlet_node : int, optional
            1-based node index where the external loop enters the tank.
        dV_loop : float, optional
            External loop volumetric flow rate [m³/s].
        Q_loop : float, optional
            Heat input from the external loop [W].

        Returns
        -------
        np.ndarray
            Updated node temperatures for the next time step [K].
        """
        self.T0 = T0  # Store dead-state temperature
        N = self.N
        UA = self.UA
        G_use = c_w * rho_w * dV_use
        eps = 1e-12
        G_loop = c_w * rho_w * max(dV_loop, 0.0)

        # ---- Effective conductivity between adjacent nodes -------------------------
        k_eff = np.zeros(N - 1)
        for i in range(N - 1):
            k_eff[i] = self.effective_conductivity(T[i], T[i + 1])

        # Effective conduction coefficient [W/K]: K_eff = k_eff · A / dh
        K_eff = k_eff * self.A / self.dh

        # ---- Assemble TDMA coefficients (a, b, c, d) + source term S ---------------
        a = np.zeros(N)
        b = np.zeros(N)
        c = np.zeros(N)
        d = np.zeros(N)
        S = np.zeros(N)

        if heater_node is not None:
            idx = heater_node - 1
            if 0 <= idx < N:
                S[idx] = heater_capacity

        # Top node (index 0)
        a[0] = 0
        b[0] = self.C * self.V / dt + G_use + K_eff[0] + UA[0]
        c[0] = -(K_eff[0] + G_use)
        d[0] = self.C * self.V * T[0] / dt + UA[0] * T_amb + S[0]

        # Interior nodes (1 … N-2)
        for i in range(1, N - 1):
            K_eff_upper = K_eff[i - 1]  # Conduction to node above
            K_eff_lower = K_eff[i]  # Conduction to node below

            a[i] = -K_eff_upper
            b[i] = self.C * self.V / dt + G_use + K_eff_upper + K_eff_lower + UA[i]
            c[i] = -(K_eff_lower + G_use)
            d[i] = self.C * self.V * T[i] / dt + UA[i] * T_amb + S[i]

        # Bottom node (index N-1)
        a[N - 1] = -K_eff[N - 2]
        b[N - 1] = self.C * self.V / dt + G_use + K_eff[N - 2] + UA[N - 1]
        c[N - 1] = 0
        d[N - 1] = self.C * self.V * T[N - 1] / dt + UA[N - 1] * T_amb + S[N - 1] + G_use * T_in

        # ---- Cache flow variables on instance --------------------------------------
        self.G_use = G_use
        self.G_loop = G_loop
        self.k_eff = k_eff  # Effective conductivity array [W/m·K]
        self.K_eff = K_eff  # Effective conduction coefficient array [W/K]

        # ---- External loop (forced advection across node range) ---------------------
        if (G_loop > 0.0) and (loop_outlet_node is not None) and (loop_inlet_node is not None):
            out_idx = int(loop_outlet_node) - 1
            in_idx = int(loop_inlet_node) - 1
            if 0 <= out_idx < N and 0 <= in_idx < N and out_idx != in_idx:
                # Loop stream return temperature (based on outlet node + Q_loop)
                T_stream_out = T[out_idx]  # Use explicit (time n) value
                T_loop_in = T_stream_out + Q_loop / max(G_loop, eps)

                _add_loop_advection_terms(a, b, c, d, in_idx, out_idx, G_loop, T_loop_in)

        # ---- Solve tri-diagonal system ---------------------------------------------
        T_next = TDMA(a, b, c, d)

        return T_next

    def info(self, as_dict: bool = False, precision: int = 3):
        """Print or return a summary of tank geometry and thermal properties.

        Parameters
        ----------
        as_dict : bool
            If True, return as dict; otherwise print a formatted summary.
        precision : int
            Number of significant digits for display.
        """

        H = float(self.H)
        D = float(self.D)
        N = int(self.N)
        dz = float(self.dh)
        A = float(self.A)
        V_node = float(self.V)
        V_tot = V_node * N
        C_node = float(self.C * self.V)
        C_tot = C_node * N
        K_ax = float(self.K)  # Axial conduction coefficient [W/K]
        UA_arr = np.asarray(self.UA, dtype=float)
        UA_sum = float(UA_arr.sum())
        UA_min = float(UA_arr.min()) if UA_arr.size else np.nan
        UA_max = float(UA_arr.max()) if UA_arr.size else np.nan

        out = {
            "geometry": {
                "H_m": H,
                "D_m": D,
                "area_m2": A,
                "layers_N": N,
                "dz_m": dz,
                "volume_node_m3": V_node,
                "volume_total_m3": V_tot,
            },
            "thermal": {
                "C_node_J_per_K": C_node,
                "C_total_J_per_K": C_tot,
                "K_axial_W_per_K": K_ax,
                "UA_sum_W_per_K": UA_sum,
                "UA_min_W_per_K": UA_min,
                "UA_max_W_per_K": UA_max,
            },
        }

        if as_dict:
            return out

        # pretty print
        p = precision

        def fmt(x):
            try:
                return f"{x:.{p}g}" if abs(x) >= 1 else f"{x:.{p}f}"
            except Exception:
                return str(x)

        lines = []
        lines.append("=== StratifiedTankTDMA :: Model Info ===")
        lines.append("[Geometry]")
        lines.append(f"  H = {fmt(H)} m,  D = {fmt(D)} m,  A = {fmt(A)} m²")
        lines.append(f"  N = {N} layers,  dz = {fmt(dz)} m")
        lines.append(f"  V_node = {fmt(V_node)} m³,  V_total = {fmt(V_tot)} m³")
        lines.append("[Thermal]")
        lines.append(f"  C_node = {fmt(C_node)} J/K,  C_total = {fmt(C_tot)} J/K")
        lines.append(f"  K_axial (conduction) = {fmt(K_ax)} W/K")
        lines.append(f"  UA_sum = {fmt(UA_sum)} W/K  (min {fmt(UA_min)}, max {fmt(UA_max)})")
        lines.append("[Mixing]")
        lines.append(f"  C_d_mix = {fmt(getattr(self, 'C_d_mix', None))}")
        print("\n".join(lines))
