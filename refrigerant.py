"""
Refrigerant cycle calculations and optimization.
"""

from collections.abc import Callable
from typing import Any

import CoolProp.CoolProp as CP
import numpy as np

from . import calc_util as cu


def calc_ref_state(
    T_evap_K: float,  # 증발 온도 [K] (포화 온도로 해석)
    T_cond_K: float,  # 응축 온도 [K] (포화 온도로 해석)
    refrigerant: str,  # 냉매 이름
    eta_cmp_isen: float | Callable,  # 압축기 등엔트로피 효율 (Float 또는 함수)
    mode: str = "heating",  # 작동 모드 ('heating' 또는 'cooling')
    dT_superheat: float = 0.0,  # [K] 증발기 출구 과열도 (State 1* → 1)
    dT_subcool: float = 0.0,  # [K] 응축기 출구 과냉각도 (State 3* → 3)
    is_active: bool = True,  # 활성화 여부 (False일 때 nan 값 반환)
) -> dict[str, Any]:
    """
    냉매 사이클의 State 1-4 열역학 물성치를 계산하는 공통 함수.

    증기압축 사이클의 4개 주요 상태점을 계산합니다:

    - State 1 (cmp_in):  압축기 입구 (증발기 출구, 저압 과열 증기)
    - State 2 (cmp_out): 압축기 출구 (응축기 입구, 고압 과열 증기)
    - State 3 (exp_in):  팽창밸브 입구 (응축기 출구, 고압 과냉 액체)
    - State 4 (exp_out): 팽창밸브 출구 (증발기 입구, 저압 2상 혼합물)

    키 배정은 항상 물리적 압축기 입출구 기준이며, mode 값은
    결과 dict의 ``"mode"`` 키에만 기록됩니다.

    Note
    ----
    냉방/난방 모드에서 어느 HX가 증발기/응축기인지는 호출측
    (``_calc_state``)에서 T_evap_K, T_cond_K를 결정하여 전달합니다.
    """

    # is_active=False일 때 nan 값으로 채워진 딕셔너리 반환
    if not is_active:
        return {
            "P_ref_cmp_in [Pa]": np.nan,
            "P_ref_cmp_out [Pa]": np.nan,
            "P_ref_exp_in [Pa]": np.nan,
            "P_ref_exp_out [Pa]": np.nan,
            "P_ref_evap_sat [Pa]": np.nan,
            "P_ref_cond_sat_l [Pa]": np.nan,
            "P_ref_cond_sat_v [Pa]": np.nan,
            "T_ref_cmp_in_K": np.nan,
            "T_ref_cmp_out_K": np.nan,
            "T_ref_exp_in_K": np.nan,
            "T_ref_exp_out_K": np.nan,
            "T_ref_evap_sat_K": np.nan,
            "T_ref_cond_sat_v_K": np.nan,
            "T_ref_cond_sat_l_K": np.nan,
            "T_ref_cmp_in [°C]": np.nan,
            "T_ref_cmp_out [°C]": np.nan,
            "T_ref_exp_in [°C]": np.nan,
            "T_ref_exp_out [°C]": np.nan,
            "T_ref_evap_sat [°C]": np.nan,
            "T_ref_cond_sat_v [°C]": np.nan,
            "T_ref_cond_sat_l [°C]": np.nan,
            "h_ref_cmp_in [J/kg]": np.nan,
            "h_ref_cmp_out [J/kg]": np.nan,
            "h_ref_cond_sat_v [J/kg]": np.nan,
            "h_ref_exp_in [J/kg]": np.nan,
            "h_ref_exp_out [J/kg]": np.nan,
            "h_ref_evap_sat [J/kg]": np.nan,
            "h_ref_cond_sat_l [J/kg]": np.nan,
            "s_ref_cmp_in [J/(kg·K)]": np.nan,
            "s_ref_cmp_out [J/(kg·K)]": np.nan,
            "s_ref_cond_sat_v [J/(kg·K)]": np.nan,
            "s_ref_exp_in [J/(kg·K)]": np.nan,
            "s_ref_exp_out [J/(kg·K)]": np.nan,
            "s_ref_evap_sat [J/(kg·K)]": np.nan,
            "s_ref_cond_sat_l [J/(kg·K)]": np.nan,
            "rho_ref_cmp_in [kg/m3]": np.nan,
            "mode": mode,
        }

    # 1단계: 포화 온도 및 압력 계산
    T_ref_evap_sat_K = T_evap_K
    T_ref_cond_sat_l_K = T_cond_K

    P_evap = CP.PropsSI("P", "T", T_ref_evap_sat_K, "Q", 1, refrigerant)
    P_cond = CP.PropsSI("P", "T", T_ref_cond_sat_l_K, "Q", 0, refrigerant)

    # 포화 상태 추가 계산
    h_ref_evap_sat = CP.PropsSI("H", "T", T_ref_evap_sat_K, "Q", 1, refrigerant)
    s_ref_evap_sat = CP.PropsSI("S", "T", T_ref_evap_sat_K, "Q", 1, refrigerant)
    h_ref_cond_sat_l = CP.PropsSI("H", "T", T_ref_cond_sat_l_K, "Q", 0, refrigerant)
    s_ref_cond_sat_l = CP.PropsSI("S", "T", T_ref_cond_sat_l_K, "Q", 0, refrigerant)

    # 2단계: State 1 (실제 과열 증기) 계산
    T_ref_cmp_in_K = T_ref_evap_sat_K + dT_superheat

    if abs(dT_superheat) < 1e-6:
        h_ref_cmp_in = h_ref_evap_sat
        s_ref_cmp_in = s_ref_evap_sat
        rho_ref_cmp_in = CP.PropsSI("D", "T", T_ref_evap_sat_K, "Q", 1, refrigerant)
    else:
        h_ref_cmp_in = CP.PropsSI("H", "T", T_ref_cmp_in_K, "P", P_evap, refrigerant)
        s_ref_cmp_in = CP.PropsSI("S", "T", T_ref_cmp_in_K, "P", P_evap, refrigerant)
        rho_ref_cmp_in = CP.PropsSI("D", "T", T_ref_cmp_in_K, "P", P_evap, refrigerant)

    # 3단계: State 2 (압축기 출구 - 고압 과열 증기) 계산
    h2_isen = CP.PropsSI("H", "P", P_cond, "S", s_ref_cmp_in, refrigerant)

    if callable(eta_cmp_isen):
        val_eta_cmp_isen = eta_cmp_isen(P_cond / P_evap)
    else:
        val_eta_cmp_isen = eta_cmp_isen

    h_ref_cmp_out = h_ref_cmp_in + (h2_isen - h_ref_cmp_in) / val_eta_cmp_isen
    try:
        T_ref_cmp_out_K = CP.PropsSI("T", "P", P_cond, "H", h_ref_cmp_out, refrigerant)
        s_ref_cmp_out = CP.PropsSI("S", "P", P_cond, "H", h_ref_cmp_out, refrigerant)
    except ValueError:
        # If H is too high, it exceeds Tmax of CoolProp (e.g. 435K for R32).
        # We MUST NOT modify h_ref_cmp_out as it breaks the energy balance.
        # Just set T and s to NaN.
        T_ref_cmp_out_K = np.nan
        s_ref_cmp_out = np.nan

    P_ref_cmp_out = P_cond

    # 3.5단계: State 2* (응축기 포화 증기 도달 지점) 계산
    T_ref_cond_sat_v_K = T_ref_cond_sat_l_K
    P_ref_cond_sat_v = P_cond
    h_ref_cond_sat_v = CP.PropsSI("H", "P", P_cond, "Q", 1, refrigerant)
    s_ref_cond_sat_v = CP.PropsSI("S", "P", P_cond, "Q", 1, refrigerant)

    # 4단계: State 3 (실제 과냉 액체) 계산
    T_ref_exp_in_K = T_ref_cond_sat_l_K - dT_subcool

    if abs(dT_subcool) < 1e-6:
        h_ref_exp_in = h_ref_cond_sat_l
        s_ref_exp_in = s_ref_cond_sat_l
    else:
        h_ref_exp_in = CP.PropsSI("H", "T", T_ref_exp_in_K, "P", P_cond, refrigerant)
        s_ref_exp_in = CP.PropsSI("S", "T", T_ref_exp_in_K, "P", P_cond, refrigerant)

    # 5단계: State 4 (팽창밸브 출구) 계산
    h_ref_exp_out = h_ref_exp_in
    P_ref_exp_out = P_evap
    T_ref_exp_out_K = CP.PropsSI("T", "P", P_evap, "H", h_ref_exp_out, refrigerant)
    s_ref_exp_out = CP.PropsSI("S", "P", P_evap, "H", h_ref_exp_out, refrigerant)

    result = {
        "P_ref_cmp_in [Pa]": P_evap,
        "P_ref_cmp_out [Pa]": P_cond,
        "P_ref_exp_in [Pa]": P_cond,
        "P_ref_exp_out [Pa]": P_evap,
        "P_ref_evap_sat [Pa]": P_evap,
        "P_ref_cond_sat_l [Pa]": P_cond,
        "P_ref_cond_sat_v [Pa]": P_ref_cond_sat_v,
        "T_ref_cmp_in_K": T_ref_cmp_in_K,
        "T_ref_cmp_out_K": T_ref_cmp_out_K,
        "T_ref_exp_in_K": T_ref_exp_in_K,
        "T_ref_exp_out_K": T_ref_exp_out_K,
        "T_ref_evap_sat_K": T_ref_evap_sat_K,
        "T_ref_cond_sat_v_K": T_ref_cond_sat_v_K,
        "T_ref_cond_sat_l_K": T_ref_cond_sat_l_K,
        "T_ref_cmp_in [°C]": cu.K2C(T_ref_cmp_in_K),
        "T_ref_cmp_out [°C]": cu.K2C(T_ref_cmp_out_K),
        "T_ref_exp_in [°C]": cu.K2C(T_ref_exp_in_K),
        "T_ref_exp_out [°C]": cu.K2C(T_ref_exp_out_K),
        "T_ref_evap_sat [°C]": cu.K2C(T_ref_evap_sat_K),
        "T_ref_cond_sat_l [°C]": cu.K2C(T_ref_cond_sat_l_K),
        "T_ref_cond_sat_v [°C]": cu.K2C(T_ref_cond_sat_v_K),
        "h_ref_cmp_in [J/kg]": h_ref_cmp_in,
        "h_ref_cmp_out [J/kg]": h_ref_cmp_out,
        "h_ref_cond_sat_v [J/kg]": h_ref_cond_sat_v,
        "h_ref_exp_in [J/kg]": h_ref_exp_in,
        "h_ref_exp_out [J/kg]": h_ref_exp_out,
        "h_ref_evap_sat [J/kg]": h_ref_evap_sat,
        "h_ref_cond_sat_l [J/kg]": h_ref_cond_sat_l,
        "s_ref_cmp_in [J/(kg·K)]": s_ref_cmp_in,
        "s_ref_cmp_out [J/(kg·K)]": s_ref_cmp_out,
        "s_ref_cond_sat_v [J/(kg·K)]": s_ref_cond_sat_v,
        "s_ref_exp_in [J/(kg·K)]": s_ref_exp_in,
        "s_ref_exp_out [J/(kg·K)]": s_ref_exp_out,
        "s_ref_evap_sat [J/(kg·K)]": s_ref_evap_sat,
        "s_ref_cond_sat_l [J/(kg·K)]": s_ref_cond_sat_l,
        "rho_ref_cmp_in [kg/m3]": rho_ref_cmp_in,
        "mode": mode,
    }

    return result


def create_lmtd_constraints() -> tuple[Any, Any]:
    """Create LMTD-based constraint functions for cycle optimization.

    Optimization requires that the heat transfer calculated by LMTD matches
    the heat transferred by the refrigerant cycle.

    Returns
    -------
    tuple[Any, Any]
        Tuple of constraint functions (constraint_tank, constraint_hx).
    """

    def constraint_tank(perf: dict[str, Any]) -> float:
        """Condenser constraint: Q_LMTD_cond - Q_ref_cond = 0"""
        if perf is None or "Q_cond" not in perf or "Q_cond_LMTD" not in perf:
            return 1e6
        return float(perf["Q_cond_LMTD"] - perf["Q_cond"])

    def constraint_hx(perf: dict[str, Any]) -> float:
        """Evaporator constraint: Q_LMTD_evap - Q_ref_evap = 0"""
        if perf is None or "Q_evap" not in perf or "Q_evap_LMTD" not in perf:
            return 1e6
        return float(perf["Q_evap_LMTD"] - perf["Q_evap"])

    return constraint_tank, constraint_hx


def find_ref_loop_optimal_operation(
    simulator_func: Any,
    refrigerant: str,
    load_W: float,
    initial_guess: list[float],
    bounds: list[tuple[float, float]],
    constraint_funcs: list[Any] | None = None,
) -> dict[str, Any] | None:
    """Find the optimal operation point for the refrigerant loop.

    Minimizes compressor power while satisfying target load and LMTD constraints.

    Parameters
    ----------
    simulator_func : callable
        Function that takes `[dT_ref_HX, dT_ref_tank]` and returns a perf dict.
    refrigerant : str
        Refrigerant name.
    load_W : float
        Target heat load [W].
    initial_guess : list[float]
        Initial guess for `[dT_evap, dT_cond]`.
    bounds : list[tuple[float, float]]
        Bounds for `[dT_evap, dT_cond]`.
    constraint_funcs : list[callable], optional
        List of constraint functions. Each takes `perf` and returns a value
        that should be 0.

    Returns
    -------
    dict[str, Any] | None
        Optimal performance dictionary, or None if optimization fails.
    """
    from scipy.optimize import minimize

    def objective(x: np.ndarray) -> float:
        perf = simulator_func(x)
        if perf is None or "W_comp" not in perf:
            return 1e6

        # Add penalty if load is not met
        load_diff = abs(perf.get("Q_cond", 0) - load_W)
        penalty = (load_diff / load_W) ** 2 * 1e5 if load_W > 0 else 0

        return float(perf["W_comp"] + penalty)

    constraints = []
    if constraint_funcs:
        for cf in constraint_funcs:

            def make_constraint(c_func: Any) -> Any:
                def constraint(x: np.ndarray) -> float:
                    perf = simulator_func(x)
                    return float(c_func(perf))

                return constraint

            constraints.append({"type": "eq", "fun": make_constraint(cf)})

    try:
        res = minimize(
            objective,
            initial_guess,
            bounds=bounds,
            constraints=constraints,
            method="SLSQP",
            options={"disp": False, "ftol": 1e-4, "maxiter": 50},
        )
        if res.success:
            return simulator_func(res.x)  # type: ignore[no-any-return]
    except Exception:
        pass

    return None
