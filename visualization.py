"""
Visualization and summary output functions.
"""

from functools import lru_cache

import CoolProp.CoolProp as CP
import dartwork_mpl as dm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import calc_util as cu


def _print_convergence_status(df: pd.DataFrame) -> None:
    """Print convergence statistics."""
    # 1. Convergence Status
    converged_all = df["converged"].all()
    print(f"[Convergence Status] All converged: {converged_all}")
    if not converged_all:
        nonconverged_count = (~df["converged"]).sum()
        print(f"  - Non-converged steps: {nonconverged_count} / {len(df)}")
    print("-" * 50)


def _print_compressor_stats(df: pd.DataFrame, active_mask: pd.Series) -> None:
    """Print compressor RPM statistics."""
    # 2. Compressor Statistics
    cmp_rpm_active = df.loc[active_mask, "cmp_rpm [rpm]"]
    print("[Compressor Speed]")
    if not cmp_rpm_active.empty:
        print(f"  - Min: {cmp_rpm_active.min():.1f} rpm | Max: {cmp_rpm_active.max():.1f} rpm")
        print(f"  - Avg (active): {cmp_rpm_active.mean():.1f} rpm")
    else:
        print("  - No active data.")
    print("-" * 50)


def _print_fan_stats(
    df: pd.DataFrame, active_mask: pd.Series, dV_ou_a_design: float, simulation_time_step: int
) -> None:
    """Print fan flow rate, velocity, pressure, power, and efficiency ratio."""
    # 3. Fan Flow Rate Statistics
    fan_active = df.loc[active_mask, "dV_ou_a [m3/s]"]
    print("[Fan Flow Rate]")
    if not fan_active.empty:
        fan_avg = fan_active.mean()
        fan_avg_pct = (fan_avg / dV_ou_a_design) * 100
        print(f"  - Min: {fan_active.min():.3f} m³/s | Max: {fan_active.max():.3f} m³/s")
        print(f"  - Avg: {fan_avg:.3f} m³/s ({fan_avg_pct:.1f}% of design)")
    else:
        print("  - No active data.")
    print("-" * 50)

    # 3-1. Fan Velocity & Pressure Statistics
    if "v_ou_a [m/s]" in df.columns:
        v_fan_active = df.loc[active_mask, "v_ou_a [m/s]"]
        print("[Fan Velocity]")
        if not v_fan_active.empty:
            print(f"  - Min: {v_fan_active.min():.2f} m/s | Max: {v_fan_active.max():.2f} m/s")
            print(f"  - Avg: {v_fan_active.mean():.2f} m/s")
        else:
            print("  - No active data.")
        print("-" * 50)

    if "dP_ou_fan_static [Pa]" in df.columns and "dP_ou_fan_dynamic [Pa]" in df.columns:
        dP_static = df.loc[active_mask, "dP_ou_fan_static [Pa]"]
        dP_dynamic = df.loc[active_mask, "dP_ou_fan_dynamic [Pa]"]

        print("[Fan Pressure (Static / Dynamic)]")
        if not dP_static.empty:
            print(
                f"  - Static  : Avg {dP_static.mean():.1f} Pa | Min {dP_static.min():.1f} Pa | Max {dP_static.max():.1f} Pa"
            )
            print(
                f"  - Dynamic : Avg {dP_dynamic.mean():.1f} Pa | Min {dP_dynamic.min():.1f} Pa | Max {dP_dynamic.max():.1f} Pa"
            )
        else:
            print("  - No active data.")
        print("-" * 50)

    # 4. Fan Power Statistics
    fan_p_active = df.loc[active_mask, "E_ou_fan [W]"]
    print("[Fan Power Use]")
    if not fan_p_active.empty:
        print(f"  - Min: {fan_p_active.min():.1f} W | Max: {fan_p_active.max():.1f} W")
        print(f"  - Avg: {fan_p_active.mean():.1f} W")
    else:
        print("  - No active data.")
    print("-" * 50)

    # 5. System Efficiency Metrics
    total_fan_energy = df["E_ou_fan [W]"].sum() * simulation_time_step
    total_energy = df["E_tot [W]"].sum() * simulation_time_step
    fan_ratio = (total_fan_energy / total_energy * 100) if total_energy > 0 else 0
    print(f"[Fan Power Ratio] {fan_ratio:.1f}% (Typical: 5-10%)")
    print("-" * 50)


def _print_heat_exchange_stats(df: pd.DataFrame, active_mask: pd.Series) -> None:
    """Print heat exchanger temperature differences."""
    # 6. Heat Exchange Performance: Outdoor Air
    if "T_ou_a_in [°C]" in df.columns and "T_ou_a_out [°C]" in df.columns:
        print("[Outdoor Air Temperature Difference (In - Out)]")
        if active_mask.any():
            delta_T = df.loc[active_mask, "T_ou_a_in [°C]"] - df.loc[active_mask, "T_ou_a_out [°C]"]
            print(f"  - Avg Delta T: {delta_T.mean():.2f} K | Max Delta T: {delta_T.max():.2f} K")
        else:
            print("  - No active data.")
        print("-" * 50)

    # 7. Heat Exchange Performance: Temp Differences
    print("[Heat Exchanger Temperature Differences]")

    # Condenser (T_cond - T_tank_w)
    if "T_ref_cond_sat_l [°C]" in df.columns and "T_tank_w [°C]" in df.columns:
        T_cond = df.loc[active_mask, "T_ref_cond_sat_l [°C]"]
        T_tank_w = df.loc[active_mask, "T_tank_w [°C]"]

        if not T_cond.empty and not T_tank_w.empty:
            dT_cond = T_cond - T_tank_w
            print(
                f"  - Condenser (T_cond - T_tank) Avg: {dT_cond.mean():.2f} K | Min: {dT_cond.min():.2f} K | Max: {dT_cond.max():.2f} K"
            )
        else:
            print("  - Condenser: No data")

    # Evaporator (T_air_in - T_evap) & (T_air_in - T_air_out)
    if "T_ou_a_in [°C]" in df.columns and "T_ref_evap_sat [°C]" in df.columns and "T_ou_a_out [°C]" in df.columns:
        T_air_in = df.loc[active_mask, "T_ou_a_in [°C]"]
        T_evap_sat = df.loc[active_mask, "T_ref_evap_sat [°C]"]
        T_air_out = df.loc[active_mask, "T_ou_a_out [°C]"]

        if not T_air_in.empty:
            dT_evap_drive = T_air_in - T_evap_sat
            dT_air_drop = T_air_in - T_air_out

            print(f"  - Evap Drive (T_air_in - T_evap) Avg: {dT_evap_drive.mean():.2f} K")
            print(f"  - Air Drop (T_air_in - T_air_out) Avg: {dT_air_drop.mean():.2f} K")
        else:
            print("  - Evaporator: No data")


def print_simulation_summary(df: pd.DataFrame, simulation_time_step: int, dV_ou_a_design: float) -> None:
    """Print a comprehensive summary of simulation results.

    Parameters
    ----------
    df : pd.DataFrame
        Simulation result DataFrame.
    simulation_time_step : int
        Time step [s].
    dV_ou_a_design : float
        Design airflow rate of outdoor unit [m3/s].
    """
    if df.empty:
        print("Empty DataFrame provided.")
        return

    required_columns = ["converged", "E_ou_fan [W]", "E_tot [W]", "dV_ou_a [m3/s]", "cmp_rpm [rpm]"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Required columns not found in DataFrame: {missing_columns}")

    active_mask = df["cmp_rpm [rpm]"] > 0

    print("=" * 50)
    _print_convergence_status(df)
    _print_compressor_stats(df, active_mask)
    _print_fan_stats(df, active_mask, dV_ou_a_design, simulation_time_step)
    _print_heat_exchange_stats(df, active_mask)
    print("=" * 50)


def _draw_cycle_lines_and_annotations(
    ax: plt.Axes,
    pts_x: dict[str, float],
    pts_y: dict[str, float],
    is_on: bool,
    color_sat_liq: str,
    color_sat_vap: str,
    line_color: str = "oc.gray5",
    color_on: str = "black",
    color_off: str = "oc.gray6",
    tol_atol: float = 0.1,
    tol_y_atol: float | None = None,
) -> None:
    """Draw heat pump cycle lines, scatter markers, and aligned text annotations."""
    cycle_markerfacecolor = color_on if is_on else color_off
    cycle_markeredgecolor = color_on if is_on else color_off

    _tol_y = tol_y_atol if tol_y_atol is not None else tol_atol

    def points_are_close(x1, y1, x2, y2, tol=tol_atol):
        if np.isnan(x1) or np.isnan(y1) or np.isnan(x2) or np.isnan(y2):
            return False
        return abs(x1 - x2) < tol and abs(y1 - y2) < _tol_y

    def draw_segment(k1, k2):
        if not (np.isnan(pts_x[k1]) or np.isnan(pts_x[k2]) or np.isnan(pts_y[k1]) or np.isnan(pts_y[k2])):
            if points_are_close(pts_x[k1], pts_y[k1], pts_x[k2], pts_y[k2], tol=tol_atol):
                ax.plot(
                    pts_x[k1],
                    pts_y[k1],
                    marker="o",
                    linestyle="None",
                    markerfacecolor=cycle_markerfacecolor,
                    markeredgecolor=cycle_markeredgecolor,
                    markeredgewidth=dm.lw(0),
                    markersize=2.5,
                    zorder=1,
                )
            else:
                ax.plot(
                    [pts_x[k1], pts_x[k2]],
                    [pts_y[k1], pts_y[k2]],
                    color=line_color,
                    linewidth=dm.lw(0),
                    linestyle=":",
                    zorder=1,
                )

    draw_segment("4", "1_star")
    draw_segment("1_star", "1")
    draw_segment("1", "2")
    draw_segment("2", "2_star")
    draw_segment("2_star", "3_star")
    draw_segment("3_star", "3")
    draw_segment("3", "4")

    points_list = []
    if points_are_close(pts_x["1_star"], pts_y["1_star"], pts_x["1"], pts_y["1"], tol_atol):
        points_list.append((pts_x["1"], pts_y["1"], "1"))
    else:
        if not (np.isnan(pts_x["1_star"]) or np.isnan(pts_y["1_star"])):
            points_list.append((pts_x["1_star"], pts_y["1_star"], "1'"))
        if not (np.isnan(pts_x["1"]) or np.isnan(pts_y["1"])):
            points_list.append((pts_x["1"], pts_y["1"], "1"))

    if points_are_close(pts_x["2"], pts_y["2"], pts_x["2_star"], pts_y["2_star"], tol_atol):
        points_list.append((pts_x["2"], pts_y["2"], "2"))
    else:
        if not (np.isnan(pts_x["2"]) or np.isnan(pts_y["2"])):
            points_list.append((pts_x["2"], pts_y["2"], "2"))
        if not (np.isnan(pts_x["2_star"]) or np.isnan(pts_y["2_star"])):
            points_list.append((pts_x["2_star"], pts_y["2_star"], "2'"))

    if points_are_close(pts_x["3_star"], pts_y["3_star"], pts_x["3"], pts_y["3"], tol_atol):
        points_list.append((pts_x["3"], pts_y["3"], "3"))
    else:
        if not (np.isnan(pts_x["3_star"]) or np.isnan(pts_y["3_star"])):
            points_list.append((pts_x["3_star"], pts_y["3_star"], "3'"))
        if not (np.isnan(pts_x["3"]) or np.isnan(pts_y["3"])):
            points_list.append((pts_x["3"], pts_y["3"], "3"))

    if not (np.isnan(pts_x["4"]) or np.isnan(pts_y["4"])):
        points_list.append((pts_x["4"], pts_y["4"], "4"))

    text_cfg = {
        "1": (4, 0, "left", "center"),
        "2": (4, 0, "left", "center"),
        "3": (-4, 0, "right", "center"),
        "4": (-4, 0, "right", "center"),
    }

    label_map = {"1": "cmp,in", "2": "cmp,out", "3": "exp,in", "4": "exp,out"}

    fig = ax.figure

    for x_val, y_val, key in points_list:
        if key in ["1'", "2'"]:
            ax.plot(
                x_val,
                y_val,
                marker="o",
                markersize=2.5,
                markerfacecolor="white",
                markeredgecolor=color_sat_vap,
                markeredgewidth=dm.lw(0),
                zorder=2,
            )
            continue
        elif key == "3'":
            ax.plot(
                x_val,
                y_val,
                marker="o",
                markersize=2.5,
                markerfacecolor="white",
                markeredgecolor=color_sat_liq,
                markeredgewidth=dm.lw(0),
                zorder=2,
            )
            continue

        ax.plot(
            x_val,
            y_val,
            marker="o",
            markersize=2.5,
            markerfacecolor=cycle_markerfacecolor,
            markeredgecolor=cycle_markeredgecolor,
            markeredgewidth=dm.lw(0),
            zorder=2,
        )

        dx, dy, ha, va = text_cfg.get(key, (0, 4, "center", "bottom"))
        text_str = label_map.get(key, key)

        if fig is not None:
            offset = dm.make_offset(dx, dy, fig)
            ax.text(x_val, y_val, text_str, transform=ax.transData + offset, ha=ha, va=va, fontsize = dm.fs(-2))
        else:
            ax.annotate(
                text_str, (x_val, y_val), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, fontsize = dm.fs(-2)
            )



@lru_cache(maxsize=8)
def _get_saturation_curves(refrigerant: str):
    T_min = CP.PropsSI("Tmin", refrigerant)
    T_crit = CP.PropsSI("Tcrit", refrigerant)
    temps_K = np.linspace(T_min + 1, T_crit - 0.5, 10000)
    temps = [cu.K2C(T) for T in temps_K]
    h_liq = [CP.PropsSI("H", "T", T, "Q", 0, refrigerant) / 1000 for T in temps_K]
    h_vap = [CP.PropsSI("H", "T", T, "Q", 1, refrigerant) / 1000 for T in temps_K]
    p_sat = [CP.PropsSI("P", "T", T, "Q", 0, refrigerant) / 1000 for T in temps_K]
    s_liq = [CP.PropsSI("S", "T", T, "Q", 0, refrigerant) / 1000 for T in temps_K]
    s_vap = [CP.PropsSI("S", "T", T, "Q", 1, refrigerant) / 1000 for T in temps_K]
    try:
        h_crit = CP.PropsSI("H", "T", T_crit, "Q", 0, refrigerant) / 1000
        p_crit = CP.PropsSI("P", "T", T_crit, "Q", 0, refrigerant) / 1000
        s_crit = CP.PropsSI("S", "T", T_crit, "Q", 0, refrigerant) / 1000
        temps.append(cu.K2C(T_crit))
        h_liq.append(h_crit)
        h_vap.append(h_crit)
        p_sat.append(p_crit)
        s_liq.append(s_crit)
        s_vap.append(s_crit)
    except Exception:
        pass
    return temps, h_liq, h_vap, p_sat, s_liq, s_vap

REF_LIMITS = {
    "R410A": {
        "th": {"xmin": 0, "xmax": 700, "ymin": -40, "ymax": 140},
        "ph": {"xmin": 0, "xmax": 700, "ymin": 100, "ymax": 10000},
        "ts": {"xmin": 0.0, "xmax": 3.0, "ymin": -40, "ymax": 140},
    },
    "R134a": {
        "th": {"xmin": 0, "xmax": 600, "ymin": -40, "ymax": 120},
        "ph": {"xmin": 0, "xmax": 600, "ymin": 100, "ymax": 10000},
        "ts": {"xmin": 0.0, "xmax": 2.5, "ymin": -40, "ymax": 120},
    },
    "R32": {
        "th": {"xmin": 0, "xmax": 800, "ymin": -40, "ymax": 200},
        "ph": {"xmin": 0, "xmax": 800, "ymin": 100, "ymax": 10000},
        "ts": {"xmin": 0.0, "xmax": 3.0, "ymin": -40, "ymax": 200},
    },
    "R290": {
        "th": {"xmin": 0, "xmax": 850, "ymin": -40, "ymax": 140},
        "ph": {"xmin": 0, "xmax": 850, "ymin": 100, "ymax": 10000},
        "ts": {"xmin": 0.0, "xmax": 3.0, "ymin": -40, "ymax": 140},
    }
}


def plot_th_diagram(
    ax: plt.Axes,
    result: dict[str, float],
    refrigerant: str,
    T_cond_bound: dict[str, float | str] | None = None,
    T_evap_bound: dict[str, float | str] | None = None,
    fontsize: float | None = None,
    tick_pad: float | None = None,
) -> None:
    """Plot T-h diagram on given axis."""
    color1, color2, color3, color4, line_color = "oc.blue5", "oc.red5", "black", "oc.gray6", "oc.gray5"
    limits = REF_LIMITS.get(refrigerant, {"th": {"xmin": 200, "xmax": 750, "ymin": -40, "ymax": 160}})["th"]

    temps, h_liq, h_vap, _, _, _ = _get_saturation_curves(refrigerant)

    h1_star = result.get("h_ref_evap_sat [J/kg]", result.get("h1_star [J/kg]", np.nan)) * cu.J2kJ
    h1 = result.get("h_ref_cmp_in [J/kg]", result.get("h1 [J/kg]", np.nan)) * cu.J2kJ
    h2 = result.get("h_ref_cmp_out [J/kg]", result.get("h2 [J/kg]", np.nan)) * cu.J2kJ
    h2_star = result.get("h_ref_cond_sat_v [J/kg]", result.get("h2_star [J/kg]", np.nan)) * cu.J2kJ
    h3_star = result.get("h_ref_cond_sat_l [J/kg]", result.get("h3_star [J/kg]", np.nan)) * cu.J2kJ
    h3 = result.get("h_ref_exp_in [J/kg]", result.get("h3 [J/kg]", np.nan)) * cu.J2kJ
    h4 = result.get("h_ref_exp_out [J/kg]", result.get("h4 [J/kg]", np.nan)) * cu.J2kJ
    T1_star = result.get("T_ref_evap_sat [°C]", result.get("T1_star [°C]", np.nan))
    T1 = result.get("T_ref_cmp_in [°C]", result.get("T1 [°C]", np.nan))
    T2 = result.get("T_ref_cmp_out [°C]", result.get("T2 [°C]", np.nan))
    T2_star = result.get("T_ref_cond_sat_v [°C]", result.get("T2_star [°C]", np.nan))
    T3_star = result.get("T_ref_cond_sat_l [°C]", result.get("T3_star [°C]", np.nan))
    T3 = result.get("T_ref_exp_in [°C]", result.get("T3 [°C]", np.nan))
    T4 = result.get("T_ref_exp_out [°C]", result.get("T4 [°C]", np.nan))

    if np.isnan(h1_star) and not np.isnan(h1):
        h1_star, T1_star = h1, T1
    if np.isnan(h3_star) and not np.isnan(h3):
        h3_star, T3_star = h3, T3

    ax.plot(h_liq, temps, color=color1, label="Sat. liquid", linewidth=dm.lw(0))
    ax.plot(h_vap, temps, color=color2, label="Sat. vapor", linewidth=dm.lw(0))

    pts_x = {"1_star": h1_star, "1": h1, "2": h2, "2_star": h2_star, "3_star": h3_star, "3": h3, "4": h4}
    pts_y = {"1_star": T1_star, "1": T1, "2": T2, "2_star": T2_star, "3_star": T3_star, "3": T3, "4": T4}
    is_on = bool(result.get("hp_is_on", result.get("is_on", False)))
    # T-h 다이어그램: x축=엔탈피[kJ/kg], y축=온도[°C]
    # 두 축의 단위가 달라 tol_y_atol을 별도로 지정:
    # - h 기준(tol_atol): 0.5 kJ/kg → 포화 구간 좁은 엔탈피 차 허용
    # - T 기준(tol_y_atol): 0.5 °C → SH/SC 적용 시 과열·과냉 구간 구별 허용
    _draw_cycle_lines_and_annotations(
        ax, pts_x, pts_y, is_on, color1, color2, line_color, color3, color4,
        tol_atol=0.5, tol_y_atol=0.5,
    )


    trans = ax.get_yaxis_transform()

    if T_cond_bound is not None:
        val = T_cond_bound.get("val")
        label = T_cond_bound.get("label", "Cond_bound")
        if pd.notna(val):
            val = float(val)  # type: ignore
            ax.axhline(y=val, color="oc.red5", linestyle=":", linewidth=dm.lw(0))
            offset = dm.make_offset(4, 2, ax.figure) if ax.figure else None
            transform = trans + offset if offset else trans
            ax.text(
                0.0,
                val,
                f"{label}: {val:.1f}°C",
                color="oc.red5",
                ha="left",
                va="bottom",
                transform=transform,
                fontsize = dm.fs(-2),
            )

    if T_evap_bound is not None:
        val = T_evap_bound.get("val")
        label = T_evap_bound.get("label", "Evap_bound")
        if pd.notna(val):
            val = float(val)  # type: ignore
            ax.axhline(y=val, color="oc.orange5", linestyle=":", linewidth=dm.lw(0))
            offset = dm.make_offset(4, -2, ax.figure) if ax.figure else None
            transform = trans + offset if offset else trans
            ax.text(
                0.0,
                val,
                f"{label}: {val:.1f}°C",
                color="oc.orange5",
                ha="left",
                va="top",
                transform=transform,
                fontsize = dm.fs(-2)
            )

    ax.set_xlabel("Enthalpy [kJ/kg]")
    ax.set_ylabel("Temperature [°C]")
    ax.set_xlim(limits["xmin"], limits["xmax"])
    ax.set_ylim(limits["ymin"], limits["ymax"])

    import matplotlib.ticker as ticker
    if refrigerant == "R32":
        ax.yaxis.set_major_locator(ticker.MultipleLocator(40))

    legend_handles = [
        ax.plot([], [], color=color1, linewidth=dm.lw(0), label="Sat. liquid")[0],
        ax.plot([], [], color=color2, linewidth=dm.lw(0), label="Sat. vapor")[0],
        ax.plot(
            [],
            [],
            color=line_color,
            linewidth=dm.lw(0),
            marker="o",
            linestyle=":",
            markersize=2.5,
            markerfacecolor=color3,
            markeredgecolor=color3,
            markeredgewidth=dm.lw(0),
            label="Ref. cycle",
        )[0],
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        handlelength=1.5,
        labelspacing=0.5,
        columnspacing=2,
        ncol=3,
        frameon=False,
    )


def plot_ph_diagram(
    ax: plt.Axes,
    result: dict[str, float],
    refrigerant: str,
    fontsize: float | None = None,
    tick_pad: float | None = None,
) -> None:
    """Plot P-h diagram on given axis."""
    color1, color2, color3, color4, line_color = "oc.blue5", "oc.red5", "black", "oc.gray6", "oc.gray4"
    limits = REF_LIMITS.get(refrigerant, {"ph": {"xmin": 200, "xmax": 750, "ymin": 100, "ymax": 10000}})["ph"]

    temps, h_liq, h_vap, _, _, _ = _get_saturation_curves(refrigerant)
    p_sat = [CP.PropsSI("P", "T", cu.C2K(T), "Q", 0, refrigerant) / 1000 for T in temps]

    P1_star = (result.get("P_ref_evap_sat [Pa]") or result.get("P1_star [Pa]", np.nan)) * cu.Pa2kPa
    P1 = (result.get("P_ref_cmp_in [Pa]") or result.get("P1 [Pa]", np.nan)) * cu.Pa2kPa
    P2 = (result.get("P_ref_cmp_out [Pa]") or result.get("P2 [Pa]", np.nan)) * cu.Pa2kPa
    P2_star = (result.get("P_ref_cond_sat_v [Pa]") or result.get("P2_star [Pa]", np.nan)) * cu.Pa2kPa
    P3_star = (result.get("P_ref_cond_sat_l [Pa]") or result.get("P3_star [Pa]", np.nan)) * cu.Pa2kPa
    P3 = (result.get("P_ref_exp_in [Pa]") or result.get("P3 [Pa]", np.nan)) * cu.Pa2kPa
    P4 = (result.get("P_ref_exp_out [Pa]") or result.get("P4 [Pa]", np.nan)) * cu.Pa2kPa

    h1_star = (result.get("h_ref_evap_sat [J/kg]") or result.get("h1_star [J/kg]", np.nan)) * cu.J2kJ
    h1 = (result.get("h_ref_cmp_in [J/kg]") or result.get("h1 [J/kg]", np.nan)) * cu.J2kJ
    h2 = (result.get("h_ref_cmp_out [J/kg]") or result.get("h2 [J/kg]", np.nan)) * cu.J2kJ
    h2_star = (result.get("h_ref_cond_sat_v [J/kg]") or result.get("h2_star [J/kg]", np.nan)) * cu.J2kJ
    h3_star = (result.get("h_ref_cond_sat_l [J/kg]") or result.get("h3_star [J/kg]", np.nan)) * cu.J2kJ
    h3 = (result.get("h_ref_exp_in [J/kg]") or result.get("h3 [J/kg]", np.nan)) * cu.J2kJ
    h4 = (result.get("h_ref_exp_out [J/kg]") or result.get("h4 [J/kg]", np.nan)) * cu.J2kJ

    if np.isnan(h1_star) and not np.isnan(h1):
        h1_star, P1_star = h1, P1
    if np.isnan(h3_star) and not np.isnan(h3):
        h3_star, P3_star = h3, P3

    ax.plot(h_liq, p_sat, color=color1, label="Sat. liquid", linewidth=dm.lw(0))
    ax.plot(h_vap, p_sat, color=color2, label="Sat. vapor", linewidth=dm.lw(0))

    pts_x = {"1_star": h1_star, "1": h1, "2": h2, "2_star": h2_star, "3_star": h3_star, "3": h3, "4": h4}
    pts_y = {"1_star": P1_star, "1": P1, "2": P2, "2_star": P2_star, "3_star": P3_star, "3": P3, "4": P4}
    is_on = result.get("hp_is_on", result.get("is_on", False))
    _draw_cycle_lines_and_annotations(ax, pts_x, pts_y, is_on, color1, color2, line_color, color3, color4, tol_atol=0.5, tol_y_atol=None)

    ax.set_xlabel("Enthalpy [kJ/kg]")
    ax.set_ylabel("Pressure [kPa]")
    ax.set_xlim(limits["xmin"], limits["xmax"])
    ax.set_ylim(limits["ymin"], limits["ymax"])
    ax.set_yscale("log")

    legend_handles = [
        ax.plot([], [], color=color1, linewidth=dm.lw(0), label="Sat. liquid")[0],
        ax.plot([], [], color=color2, linewidth=dm.lw(0), label="Sat. vapor")[0],
        ax.plot(
            [],
            [],
            color=line_color,
            linewidth=dm.lw(0),
            marker="o",
            linestyle=":",
            markersize=2.5,
            markerfacecolor=color3,
            markeredgecolor=color3,
            markeredgewidth=dm.lw(0),
            label="Ref. cycle",
        )[0],
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        handlelength=1.5,
        labelspacing=0.5,
        columnspacing=2,
        ncol=3,
        frameon=False,
    )


def plot_ts_diagram(
    ax: plt.Axes,
    result: dict[str, float],
    refrigerant: str,
    T_cond_bound: dict[str, float | str] | None = None,
    T_evap_bound: dict[str, float | str] | None = None,
) -> None:
    """Plot T-s diagram on given axis with super heating/cooling considered."""
    color1, color2, color3, color4, line_color = "oc.blue5", "oc.red5", "black", "oc.gray6", "oc.gray5"
    limits = REF_LIMITS.get(refrigerant, {"ts": {"xmin": 1.0, "xmax": 3.0, "ymin": -40, "ymax": 160}})["ts"]

    temps, _, _, _, s_liq, s_vap = _get_saturation_curves(refrigerant)

    ax.plot(s_liq, temps, color=color1, label="Sat. liquid", linewidth=dm.lw(0))
    ax.plot(s_vap, temps, color=color2, label="Sat. vapor", linewidth=dm.lw(0))

    s1_star = (result.get("s_ref_evap_sat [J/(kg·K)]") or result.get("s1_star [J/(kg·K)]", np.nan)) / 1000
    s1 = (result.get("s_ref_cmp_in [J/(kg·K)]") or result.get("s1 [J/(kg·K)]", np.nan)) / 1000
    s2 = (result.get("s_ref_cmp_out [J/(kg·K)]") or result.get("s2 [J/(kg·K)]", np.nan)) / 1000
    s2_star = (result.get("s_ref_cond_sat_v [J/(kg·K)]") or result.get("s2_star [J/(kg·K)]", np.nan)) / 1000
    s3_star = (result.get("s_ref_cond_sat_l [J/(kg·K)]") or result.get("s3_star [J/(kg·K)]", np.nan)) / 1000
    s3 = (result.get("s_ref_exp_in [J/(kg·K)]") or result.get("s3 [J/(kg·K)]", np.nan)) / 1000
    s4 = (result.get("s_ref_exp_out [J/(kg·K)]") or result.get("s4 [J/(kg·K)]", np.nan)) / 1000

    T1_star = result.get("T_ref_evap_sat [°C]") or result.get("T1_star [°C]", np.nan)
    T1 = result.get("T_ref_cmp_in [°C]") or result.get("T1 [°C]", np.nan)
    T2 = result.get("T_ref_cmp_out [°C]") or result.get("T2 [°C]", np.nan)
    T2_star = result.get("T_ref_cond_sat_v [°C]") or result.get("T2_star [°C]", np.nan)
    T3_star = result.get("T_ref_cond_sat_l [°C]") or result.get("T3_star [°C]", np.nan)
    T3 = result.get("T_ref_exp_in [°C]") or result.get("T3 [°C]", np.nan)
    T4 = result.get("T_ref_exp_out [°C]") or result.get("T4 [°C]", np.nan)

    if np.isnan(s1_star) and not np.isnan(s1):
        s1_star, T1_star = s1, T1
    if np.isnan(s3_star) and not np.isnan(s3):
        s3_star, T3_star = s3, T3

    pts_x = {"1_star": s1_star, "1": s1, "2": s2, "2_star": s2_star, "3_star": s3_star, "3": s3, "4": s4}
    pts_y = {"1_star": T1_star, "1": T1, "2": T2, "2_star": T2_star, "3_star": T3_star, "3": T3, "4": T4}
    is_on = result.get("hp_is_on", result.get("is_on", False))
    _draw_cycle_lines_and_annotations(
        ax, pts_x, pts_y, is_on, color1, color2, line_color, color3, color4, tol_atol=0.05, tol_y_atol=0.5
    )

    trans = ax.get_yaxis_transform()

    if T_cond_bound is not None:
        val = T_cond_bound.get("val")
        label = T_cond_bound.get("label", "Cond_bound")
        if pd.notna(val):
            val = float(val)  # type: ignore
            ax.axhline(y=val, color="oc.red5", linestyle=":", linewidth=dm.lw(0))
            offset = dm.make_offset(4, 2, ax.figure) if ax.figure else None
            transform = trans + offset if offset else trans
            ax.text(
                0.0,
                val,
                f"{label}: {val:.1f}°C",
                color="oc.red5",
                ha="left",
                va="bottom",
                transform=transform,
                fontsize = dm.fs(-2)
            )

    if T_evap_bound is not None:
        val = T_evap_bound.get("val")
        label = T_evap_bound.get("label", "Evap_bound")
        if pd.notna(val):
            val = float(val)  # type: ignore
            ax.axhline(y=val, color="oc.orange5", linestyle=":", linewidth=dm.lw(0))
            offset = dm.make_offset(4, -2, ax.figure) if ax.figure else None
            transform = trans + offset if offset else trans
            ax.text(
                0.0,
                val,
                f"{label}: {val:.1f}°C",
                color="oc.orange5",
                ha="left",
                va="top",
                transform=transform,
                fontsize = dm.fs(-2)
            )

    ax.set_xlabel("Entropy [kJ/(kg·K)]")
    ax.set_ylabel("Temperature [°C]")
    ax.set_xlim(limits["xmin"], limits["xmax"])
    ax.set_ylim(limits["ymin"], limits["ymax"])

    import matplotlib.ticker as ticker
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    if refrigerant == "R32":
        ax.yaxis.set_major_locator(ticker.MultipleLocator(40))

    legend_handles = [
        ax.plot([], [], color=color1, linewidth=dm.lw(0), label="Sat. liquid")[0],
        ax.plot([], [], color=color2, linewidth=dm.lw(0), label="Sat. vapor")[0],
        ax.plot(
            [],
            [],
            color=line_color,
            linewidth=dm.lw(0),
            marker="o",
            linestyle=":",
            markersize=2.5,
            markerfacecolor=color3,
            markeredgecolor=color3,
            markeredgewidth=dm.lw(0),
            label="Ref. cycle",
        )[0],
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        handlelength=1.5,
        labelspacing=0.5,
        columnspacing=2,
        ncol=3,
        frameon=False,
    )
