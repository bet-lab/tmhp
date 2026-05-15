"""
Weather data processing and irradiance calculations.
"""

import warnings

import numpy as np
import pandas as pd
import pvlib

from . import calc_util as cu


def load_kma_solar_csv(csv_path: str, encoding: str = "euc-kr") -> pd.DataFrame:
    """Load KMA (기상청) 1-minute cumulative solar irradiance CSV.

    Parameters
    ----------
    csv_path : str
        Path to CSV file.
    encoding : str, optional
        File encoding. Default is 'euc-kr'.

    Returns
    -------
    pd.DataFrame
        DataFrame with datetime index and 'ghi' column [W/m2].
    """
    warnings.warn(
        "load_kma_solar_csv is deprecated. Use enex_analysis.external_api.kma_loader instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    df = pd.read_csv(csv_path, encoding=encoding)

    # 1. 일시 파싱
    time_col = df.columns[df.columns.str.contains("일시|시간")][0]
    df["datetime"] = pd.to_datetime(df[time_col])

    # [BUGFIX] KMA 데이터는 KST 기준이나, 시간대(tz) 정보가 없는 Naive Datetime으로 파싱됨.
    # 이를 그대로 pvlib에 넘기면 UTC로 오인하여 9시간의 태양 위치 계산 오차(일몰/일출 시 DNI 폭증 Anomaly 등)가 발생함.
    # 따라서 반드시 'Asia/Seoul' 시간대를 명시적으로 부여해야 함.
    if df["datetime"].dt.tz is None:
        df["datetime"] = df["datetime"].dt.tz_localize("Asia/Seoul")

    df.set_index("datetime", inplace=True)

    # 2. 일사량 파싱 (MJ/m2 -> W/m2)
    # 1분 단위 누적 일사량이라 가정
    solar_col = df.columns[df.columns.str.contains("일사")][0]
    df["ghi"] = df[solar_col].diff().fillna(0) * 1e6 / 60
    df.loc[df["ghi"] < 0, "ghi"] = 0

    return df[["ghi"]]


def load_kma_T0_sol_hourly_csv(csv_path: str, encoding: str = "euc-kr") -> pd.DataFrame:
    """Load KMA hourly temperature and solar irradiance CSV.

    Parameters
    ----------
    csv_path : str
        Path to CSV file.
    encoding : str, optional
        File encoding. Default is 'euc-kr'.

    Returns
    -------
    pd.DataFrame
        DataFrame with datetime index, 'T0_K', and 'ghi' columns.
    """
    warnings.warn(
        "load_kma_T0_sol_hourly_csv is deprecated. Use enex_analysis.external_api.kma_loader instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    df = pd.read_csv(csv_path, encoding=encoding)

    # 컬럼 찾기 함수
    def _find_col(patterns: list[str]) -> str:
        for p in patterns:
            match = df.columns[df.columns.str.lower().str.contains(p.lower())]
            if len(match) > 0:
                return str(match[0])
        raise ValueError(f"Column matching {patterns} not found.")

    time_col = _find_col(["일시", "시간", "time", "date"])
    temp_col = _find_col(["기온", "온도", "temp", "t0", "°C", "℃"])
    ghi_col = _find_col(["일사", "ghi", "irradiance", "mj", "solar"])

    df["datetime"] = pd.to_datetime(df[time_col])

    # [BUGFIX] KMA 데이터는 KST 기준이나, 시간대(tz) 정보가 없는 Naive Datetime으로 파싱됨.
    # 이를 그대로 pvlib에 넘기면 UTC로 오인하여 9시간의 태양 위치 계산 오차(일몰/일출 시 DNI 폭증 Anomaly 등)가 발생함.
    # 따라서 반드시 'Asia/Seoul' 시간대를 명시적으로 부여해야 함.
    if df["datetime"].dt.tz is None:
        df["datetime"] = df["datetime"].dt.tz_localize("Asia/Seoul")

    df.set_index("datetime", inplace=True)

    # 온도를 Kelvin으로 변환
    df["T0_K"] = cu.C2K(df[temp_col])

    # 일사량을 W/m2로 변환 (1시간 누적 MJ/m2 -> W/m2)
    df["ghi"] = df[ghi_col] * cu.MJ2J * cu.s2h
    df.loc[df["ghi"] < 0, "ghi"] = 0

    return df[["T0_K", "ghi"]]


def decompose_ghi_to_poa(
    ghi: np.ndarray,
    latitude: float,
    longitude: float,
    tilt: float,
    azimuth: float,
    altitude: float = 0,
    tz: str = "Asia/Seoul",
    decomposition: str = "erbs",
    transposition: str = "perez",
) -> pd.DataFrame:
    """Decompose GHI to POA (Plane of Array) total irradiance.

    Parameters
    ----------
    ghi : np.ndarray or pd.Series
        Global horizontal irradiance timeseries [W/m2]. Must have DatetimeIndex.
    latitude : float
        Location latitude.
    longitude : float
        Location longitude.
    tilt : float
        Surface tilt angle [deg].
    azimuth : float
        Surface azimuth [deg]. 180 is South.
    altitude : float, optional
        Location altitude [m]. Default is 0.
    tz : str, optional
        Timezone. Default is 'Asia/Seoul'.
    decomposition : str, optional
        DNI/DHI decomposition model ('erbs', 'dirint', etc). Default is 'erbs'.
    transposition : str, optional
        POA transposition model ('perez', 'isotropic', etc). Default is 'perez'.

    Returns
    -------
    pd.DataFrame
        DataFrame with 'poa_global', 'poa_direct', 'poa_diffuse'.
    """
    if not isinstance(ghi, pd.Series):
        raise ValueError("ghi must be a pandas Series with DatetimeIndex")

    times = ghi.index
    location = pvlib.location.Location(latitude, longitude, tz, altitude)

    # 1. 태양 위치 계산
    solar_position = location.get_solarposition(times)

    # 2. DNI, DHI 분해
    if decomposition.lower() == "erbs":
        dni_dhi = pvlib.irradiance.erbs(ghi, solar_position["zenith"], times.dayofyear)
    else:
        # 간단히 erbs 폴백
        dni_dhi = pvlib.irradiance.erbs(ghi, solar_position["zenith"], times.dayofyear)

    dni = dni_dhi["dni"]
    dhi = dni_dhi["dhi"]

    # 3. POA 변환
    dni_extra = pvlib.irradiance.get_extra_radiation(times)
    airmass = location.get_airmass(times=times)
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=solar_position["zenith"],
        solar_azimuth=solar_position["azimuth"],
        dni=dni,
        ghi=ghi,
        dhi=dhi,
        dni_extra=dni_extra,
        airmass=airmass["airmass_absolute"],
        model=transposition.lower(),
    )

    return poa
