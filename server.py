import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PRESSURE_LEVELS = [1000, 850, 700, 500, 250, 50]

PALETTES = {
    "precip": [
        [0.00, [56, 189, 248]],
        [0.20, [14, 165, 233]],
        [0.45, [34, 197, 94]],
        [0.70, [250, 204, 21]],
        [0.88, [249, 115, 22]],
        [1.00, [147, 51, 234]],
    ],
    "temp": [
        [0.00, [30, 58, 138]],
        [0.22, [37, 99, 235]],
        [0.42, [20, 184, 166]],
        [0.58, [34, 197, 94]],
        [0.74, [250, 204, 21]],
        [0.88, [249, 115, 22]],
        [1.00, [185, 28, 28]],
    ],
    "wind": [
        [0.00, [15, 118, 110]],
        [0.30, [34, 197, 94]],
        [0.55, [250, 204, 21]],
        [0.78, [249, 115, 22]],
        [1.00, [220, 38, 38]],
    ],
    "pressure": [
        [0.00, [126, 34, 206]],
        [0.25, [37, 99, 235]],
        [0.50, [20, 184, 166]],
        [0.75, [250, 204, 21]],
        [1.00, [220, 38, 38]],
    ],
    "cloud": [
        [0.00, [248, 250, 252]],
        [0.35, [186, 230, 253]],
        [0.70, [100, 116, 139]],
        [1.00, [30, 41, 59]],
    ],
    "cape": [
        [0.00, [30, 64, 175]],
        [0.30, [20, 184, 166]],
        [0.60, [250, 204, 21]],
        [0.82, [249, 115, 22]],
        [1.00, [225, 29, 72]],
    ],
    "moisture": [
        [0.00, [217, 119, 6]],
        [0.35, [250, 204, 21]],
        [0.70, [34, 197, 94]],
        [1.00, [29, 78, 216]],
    ],
    "cams": [
        [0.00, [22, 163, 74]],
        [0.25, [132, 204, 22]],
        [0.50, [250, 204, 21]],
        [0.75, [249, 115, 22]],
        [1.00, [153, 27, 27]],
    ],
}


def build_variables() -> list[dict]:
    vars_list = [
        {"key": "precipitation", "provider": "ECMWF", "group": "precip", "name": "Total Precipitation", "unit": "mm", "min": 0.0, "max": 5.0, "ticks": ["0", "1", "3", "5+"], "stops": PALETTES["precip"]},
        {"key": "large_scale_precipitation", "provider": "ECMWF", "group": "precip", "name": "Large-Scale Precip", "unit": "mm", "min": 0.0, "max": 5.0, "ticks": ["0", "1", "3", "5+"], "stops": PALETTES["precip"]},
        {"key": "convective_precipitation", "provider": "ECMWF", "group": "precip", "name": "Convective Precip", "unit": "mm", "min": 0.0, "max": 5.0, "ticks": ["0", "1", "3", "5+"], "stops": PALETTES["precip"]},
        {"key": "precipitation_type", "provider": "ECMWF", "group": "precip", "name": "Precip Type", "unit": "code", "min": 0, "max": 12, "ticks": ["0", "4", "8", "12"], "stops": PALETTES["precip"]},
        {"key": "total_column_water_vapour", "provider": "ECMWF", "group": "precip", "name": "Total Column WV", "unit": "kg/m²", "min": 0, "max": 60, "ticks": ["0", "20", "40", "60+"], "stops": PALETTES["moisture"]},

        {"key": "temperature_2m", "provider": "ECMWF", "group": "temp", "name": "2m Temperature", "unit": "°C", "min": -20, "max": 40, "ticks": ["-20°", "0°", "20°", "40°"], "stops": PALETTES["temp"]},
        {"key": "dewpoint_2m", "provider": "ECMWF", "group": "temp", "name": "2m Dewpoint", "unit": "°C", "min": -20, "max": 30, "ticks": ["-20°", "-3°", "13°", "30°"], "stops": PALETTES["moisture"]},
        {"key": "soil_temperature_1", "provider": "ECMWF", "group": "temp", "name": "Soil Temp L1", "unit": "°C", "min": -15, "max": 40, "ticks": ["-15°", "3°", "21°", "40°"], "stops": PALETTES["temp"]},
        {"key": "soil_water_1", "provider": "ECMWF", "group": "temp", "name": "Soil Moisture L1", "unit": "m³/m³", "min": 0, "max": 0.6, "ticks": ["0.0", "0.2", "0.4", "0.6"], "stops": PALETTES["moisture"]},

        {"key": "wind_speed_10m", "provider": "ECMWF", "group": "wind", "name": "10m Wind Speed", "unit": "m/s", "min": 0, "max": 25, "ticks": ["0", "8", "16", "25+"], "stops": PALETTES["wind"]},
        {"key": "wind_direction_10m", "provider": "ECMWF", "group": "wind", "name": "10m Wind Dir", "unit": "°", "min": 0, "max": 360, "ticks": ["0°", "120°", "240°", "360°"], "stops": PALETTES["wind"]},
        {"key": "wind_u_10m", "provider": "ECMWF", "group": "wind", "name": "10m U Wind", "unit": "m/s", "min": -25, "max": 25, "ticks": ["-25", "-8", "8", "25"], "stops": PALETTES["wind"]},
        {"key": "wind_v_10m", "provider": "ECMWF", "group": "wind", "name": "10m V Wind", "unit": "m/s", "min": -25, "max": 25, "ticks": ["-25", "-8", "8", "25"], "stops": PALETTES["wind"]},
        {"key": "wind_u_100m", "provider": "ECMWF", "group": "wind", "name": "100m U Wind", "unit": "m/s", "min": -30, "max": 30, "ticks": ["-30", "-10", "10", "30"], "stops": PALETTES["wind"]},
        {"key": "wind_v_100m", "provider": "ECMWF", "group": "wind", "name": "100m V Wind", "unit": "m/s", "min": -30, "max": 30, "ticks": ["-30", "-10", "10", "30"], "stops": PALETTES["wind"]},

        {"key": "pressure_msl", "provider": "ECMWF", "group": "pressure", "name": "MSLP", "unit": "hPa", "min": 985, "max": 1035, "ticks": ["985", "1002", "1018", "1035"], "stops": PALETTES["pressure"]},
        {"key": "surface_pressure", "provider": "ECMWF", "group": "pressure", "name": "Surface Pressure", "unit": "hPa", "min": 900, "max": 1035, "ticks": ["900", "945", "990", "1035"], "stops": PALETTES["pressure"]},
        {"key": "cape", "provider": "ECMWF", "group": "pressure", "name": "MUCAPE", "unit": "J/kg", "min": 0, "max": 3000, "ticks": ["0", "1000", "2000", "3000+"], "stops": PALETTES["temp"]},
        {"key": "cin", "provider": "ECMWF", "group": "pressure", "name": "CIN", "unit": "J/kg", "min": -500, "max": 0, "ticks": ["-500", "-330", "-165", "0"], "stops": PALETTES["pressure"]},
        {"key": "total_cloud_cover", "provider": "ECMWF", "group": "pressure", "name": "Total Cloud", "unit": "%", "min": 0, "max": 100, "ticks": ["0%", "35%", "70%", "100%"], "stops": PALETTES["moisture"]},
        {"key": "low_cloud_cover", "provider": "ECMWF", "group": "pressure", "name": "Low Cloud", "unit": "%", "min": 0, "max": 100, "ticks": ["0%", "35%", "70%", "100%"], "stops": PALETTES["moisture"]},
        {"key": "med_cloud_cover", "provider": "ECMWF", "group": "pressure", "name": "Med Cloud", "unit": "%", "min": 0, "max": 100, "ticks": ["0%", "35%", "70%", "100%"], "stops": PALETTES["moisture"]},
        {"key": "high_cloud_cover", "provider": "ECMWF", "group": "pressure", "name": "High Cloud", "unit": "%", "min": 0, "max": 100, "ticks": ["0%", "35%", "70%", "100%"], "stops": PALETTES["moisture"]},
        {"key": "ssrd", "provider": "ECMWF", "group": "pressure", "name": "Solar Rad Down", "unit": "J/m²", "min": 0, "max": 3500000, "ticks": ["0", "1.1M", "2.3M", "3.5M"], "stops": PALETTES["temp"]},
        {"key": "strd", "provider": "ECMWF", "group": "pressure", "name": "Thermal Rad Down", "unit": "J/m²", "min": 0, "max": 3500000, "ticks": ["0", "1.1M", "2.3M", "3.5M"], "stops": PALETTES["temp"]},
        {"key": "ssr", "provider": "ECMWF", "group": "pressure", "name": "Net Solar Rad", "unit": "J/m²", "min": 0, "max": 3000000, "ticks": ["0", "1M", "2M", "3M"], "stops": PALETTES["temp"]},
        {"key": "str", "provider": "ECMWF", "group": "pressure", "name": "Net Thermal Rad", "unit": "J/m²", "min": -2000000, "max": 0, "ticks": ["-2M", "-1.3M", "-0.6M", "0"], "stops": PALETTES["pressure"]},
        {"key": "slhf", "provider": "ECMWF", "group": "pressure", "name": "Latent Heat Flux", "unit": "J/m²", "min": -2000000, "max": 500000, "ticks": ["-2M", "-1.1M", "-0.3M", "0.5M"], "stops": PALETTES["moisture"]},
        {"key": "sshf", "provider": "ECMWF", "group": "pressure", "name": "Sensible Heat Flux", "unit": "J/m²", "min": -2000000, "max": 1000000, "ticks": ["-2M", "-1M", "0", "1M"], "stops": PALETTES["temp"]},
        {"key": "evaporation", "provider": "ECMWF", "group": "precip", "name": "Evaporation", "unit": "mm", "min": -10, "max": 5, "ticks": ["-10", "-5", "0", "5"], "stops": PALETTES["moisture"]},
        {"key": "potential_evaporation", "provider": "ECMWF", "group": "precip", "name": "Pot. Evaporation", "unit": "mm", "min": -15, "max": 5, "ticks": ["-15", "-8", "-2", "5"], "stops": PALETTES["moisture"]},
    ]

    for lvl in PRESSURE_LEVELS:
        vars_list.extend([
            {"key": f"temperature_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Temp", "unit": "°C", "min": -80, "max": 30, "ticks": ["-80°", "-43°", "-7°", "30°"], "stops": PALETTES["temp"]},
            {"key": f"geopotential_height_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Height", "unit": "m", "min": 0, "max": 32000, "ticks": ["0", "10k", "21k", "32k"], "stops": PALETTES["pressure"]},
            {"key": f"wind_speed_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Wind", "unit": "m/s", "min": 0, "max": 60, "ticks": ["0", "20", "40", "60+"], "stops": PALETTES["wind"]},
            {"key": f"wind_direction_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Dir", "unit": "°", "min": 0, "max": 360, "ticks": ["0°", "120°", "240°", "360°"], "stops": PALETTES["wind"]},
            {"key": f"wind_u_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa U Wind", "unit": "m/s", "min": -50, "max": 50, "ticks": ["-50", "-17", "17", "50"], "stops": PALETTES["wind"]},
            {"key": f"wind_v_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa V Wind", "unit": "m/s", "min": -50, "max": 50, "ticks": ["-50", "-17", "17", "50"], "stops": PALETTES["wind"]},
            {"key": f"relative_humidity_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa RH", "unit": "%", "min": 0, "max": 100, "ticks": ["0%", "35%", "70%", "100%"], "stops": PALETTES["moisture"]},
            {"key": f"specific_humidity_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Q", "unit": "g/kg", "min": 0, "max": 20, "ticks": ["0", "7", "14", "20"], "stops": PALETTES["moisture"]},
            {"key": f"vertical_velocity_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Omega", "unit": "Pa/s", "min": -2, "max": 2, "ticks": ["-2.0", "-0.7", "0.7", "2.0"], "stops": PALETTES["pressure"]},
            {"key": f"vorticity_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Vort", "unit": "10⁻⁵ s⁻¹", "min": -20, "max": 20, "ticks": ["-20", "-7", "7", "20"], "stops": PALETTES["wind"]},
            {"key": f"divergence_{lvl}hPa", "provider": "ECMWF", "group": "levels", "level": lvl, "name": f"{lvl} hPa Div", "unit": "10⁻⁵ s⁻¹", "min": -20, "max": 20, "ticks": ["-20", "-7", "7", "20"], "stops": PALETTES["pressure"]},
        ])

    return vars_list

VARIABLES = build_variables()
VAR_MAP = {v["key"]: v for v in VARIABLES}
POINT_CACHE = {}
GRID_CACHE = {}
RATE_LIMIT_UNTIL = {"ECMWF": 0.0, "CAMS": 0.0}


def provider_for_var(var_key: str) -> str:
    return VAR_MAP.get(var_key, {}).get("provider", "ECMWF")


def rate_limited(provider: str) -> bool:
    return time.time() < RATE_LIMIT_UNTIL.get(provider, 0.0)


def fetch_series_raw(provider: str, lat_csv: str, lon_csv: str, var_key: str, timeout: float = 2.5):
    if rate_limited(provider):
        rem = max(1, int(RATE_LIMIT_UNTIL.get(provider, 0.0) - time.time()))
        return None, f"429 ({rem}s)"

    if provider == "CAMS":
        base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {"latitude": lat_csv, "longitude": lon_csv, "hourly": var_key, "past_days": 1, "timezone": "UTC"}
    else:
        base_url = "https://api.open-meteo.com/v1/ecmwf"
        params = {"latitude": lat_csv, "longitude": lon_csv, "hourly": var_key, "past_days": 1, "forecast_days": 16, "timezone": "UTC"}

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), "OK"
    except urllib.error.HTTPError as e:
        if e.code == 429:
            hdr = e.headers.get("Retry-After") if e.headers else None
            wait_s = min(int(hdr), 3) if (hdr and hdr.isdigit()) else 2
            RATE_LIMIT_UNTIL[provider] = time.time() + wait_s
            return None, f"429 ({wait_s}s)"
        return None, f"HTTP_{e.code}"
    except Exception as e:
        return None, f"ERR:{type(e).__name__}"


def parse_series(raw_obj: dict, var_key: str, step_hours: int) -> list[dict]:
    h = raw_obj.get("hourly", {})
    times = h.get("time", [])
    vals = h.get(var_key, [])
    out = []
    for i, t_str in enumerate(times):
        iso = t_str[:16] + ":00" if len(t_str) == 13 else t_str[:19]
        try:
            dt_obj = datetime.fromisoformat(iso)
        except Exception:
            continue
        if step_hours == 3 and dt_obj.hour % 3 != 0:
            continue
        if step_hours == 6 and dt_obj.hour % 6 != 0:
            continue
        v = vals[i] if isinstance(vals, list) and i < len(vals) else None
        out.append({"time": iso, "value": v if v is not None else None})
    return out


import os as _g_os
import cfgrib as _cfgrib
import numpy as _np
import pandas as _pd

_GRIB_FILE_PATH = _g_os.path.join(_g_os.path.dirname(_g_os.path.abspath(__file__)), "marmara_ecmwf.grib2")
_GRIB_DS_LIST = None
_GRIB_SERIES_CACHE = {}

_VAR_TO_GRIB = {
    "temperature_2m": ("t2m", None, lambda v: float(v) - 273.15),
    "t2m": ("t2m", None, lambda v: float(v) - 273.15),
    "dewpoint_2m": ("d2m", None, lambda v: float(v) - 273.15),
    "soil_temperature_1": ("stl1", None, lambda v: float(v) - 273.15),
    "soil_water_1": ("swvl1", None, lambda v: float(v)),
    "precipitation": ("tp", None, lambda v: max(0.0, float(v) * 1000.0)),
    "tp": ("tp", None, lambda v: max(0.0, float(v) * 1000.0)),
    "large_scale_precipitation": ("__lsp_from_tp_cp__", None, lambda v: max(0.0, float(v) * 1000.0)),
    "convective_precipitation": ("cp", None, lambda v: max(0.0, float(v) * 1000.0)),
    "precipitation_type": ("ptype", None, lambda v: float(v)),
    "total_column_water_vapour": ("tcwv", None, lambda v: float(v)),
    "evaporation": ("e", None, lambda v: float(v) * 1000.0),
    "potential_evaporation": ("pev", None, lambda v: float(v) * 1000.0),
    "pressure_msl": ("msl", None, lambda v: float(v) / 100.0),
    "msl": ("msl", None, lambda v: float(v) / 100.0),
    "surface_pressure": ("sp", None, lambda v: float(v) / 100.0),
    "sp": ("sp", None, lambda v: float(v) / 100.0),
    "cape": ("mucape", None, lambda v: float(v)),
    "cin": ("cin", None, lambda v: float(v)),
    "total_cloud_cover": ("tcc", None, lambda v: float(v) * 100.0 if float(v) <= 1.5 else float(v)),
    "low_cloud_cover": ("lcc", None, lambda v: float(v) * 100.0 if float(v) <= 1.5 else float(v)),
    "med_cloud_cover": ("mcc", None, lambda v: float(v) * 100.0 if float(v) <= 1.5 else float(v)),
    "high_cloud_cover": ("hcc", None, lambda v: float(v) * 100.0 if float(v) <= 1.5 else float(v)),
    "ssrd": ("ssrd", None, lambda v: float(v)),
    "strd": ("strd", None, lambda v: float(v)),
    "ssr": ("ssr", None, lambda v: float(v)),
    "str": ("str", None, lambda v: float(v)),
    "slhf": ("slhf", None, lambda v: float(v)),
    "sshf": ("sshf", None, lambda v: float(v)),
    "wind_speed_10m": ("__wind_spd_10m__", None, lambda v: float(v)),
    "wind_direction_10m": ("__wind_dir_10m__", None, lambda v: float(v)),
    "wind_u_10m": ("u10", None, lambda v: float(v)),
    "wind_v_10m": ("v10", None, lambda v: float(v)),
    "wind_u_100m": ("u100", None, lambda v: float(v)),
    "wind_v_100m": ("v100", None, lambda v: float(v)),

    "specific_humidity_1000hPa": ("q", 1000, lambda v: float(v)),
    "vertical_velocity_1000hPa": ("w", 1000, lambda v: float(v)),
    "vorticity_1000hPa": ("vo", 1000, lambda v: float(v)),
    "divergence_1000hPa": ("d", 1000, lambda v: float(v)),
    "specific_humidity_850hPa": ("q", 850, lambda v: float(v)),
    "vertical_velocity_850hPa": ("w", 850, lambda v: float(v)),
    "vorticity_850hPa": ("vo", 850, lambda v: float(v)),
    "divergence_850hPa": ("d", 850, lambda v: float(v)),
    "specific_humidity_700hPa": ("q", 700, lambda v: float(v)),
    "vertical_velocity_700hPa": ("w", 700, lambda v: float(v)),
    "vorticity_700hPa": ("vo", 700, lambda v: float(v)),
    "divergence_700hPa": ("d", 700, lambda v: float(v)),
    "specific_humidity_500hPa": ("q", 500, lambda v: float(v)),
    "vertical_velocity_500hPa": ("w", 500, lambda v: float(v)),
    "vorticity_500hPa": ("vo", 500, lambda v: float(v)),
    "divergence_500hPa": ("d", 500, lambda v: float(v)),
    "specific_humidity_250hPa": ("q", 250, lambda v: float(v)),
    "vertical_velocity_250hPa": ("w", 250, lambda v: float(v)),
    "vorticity_250hPa": ("vo", 250, lambda v: float(v)),
    "divergence_250hPa": ("d", 250, lambda v: float(v)),
    "specific_humidity_50hPa": ("q", 50, lambda v: float(v)),
    "vertical_velocity_50hPa": ("w", 50, lambda v: float(v)),
    "vorticity_50hPa": ("vo", 50, lambda v: float(v)),
    "divergence_50hPa": ("d", 50, lambda v: float(v)),
}

for _lvl in PRESSURE_LEVELS:
    _VAR_TO_GRIB[f"temperature_{_lvl}hPa"] = ("t", _lvl, lambda v: float(v) - 273.15)
    _VAR_TO_GRIB[f"geopotential_height_{_lvl}hPa"] = ("z", _lvl, lambda v: float(v) / 9.80665)
    _VAR_TO_GRIB[f"wind_speed_{_lvl}hPa"] = ("__wind_spd_lvl__", _lvl, lambda v: float(v))
    _VAR_TO_GRIB[f"wind_direction_{_lvl}hPa"] = ("__wind_dir_lvl__", _lvl, lambda v: float(v))
    _VAR_TO_GRIB[f"wind_u_{_lvl}hPa"] = ("u", _lvl, lambda v: float(v))
    _VAR_TO_GRIB[f"wind_v_{_lvl}hPa"] = ("v", _lvl, lambda v: float(v))
    _VAR_TO_GRIB[f"relative_humidity_{_lvl}hPa"] = ("r", _lvl, lambda v: float(v))
    _VAR_TO_GRIB[f"specific_humidity_{_lvl}hPa"] = ("q", _lvl, lambda v: float(v) * 1000.0)
    _VAR_TO_GRIB[f"vertical_velocity_{_lvl}hPa"] = ("w", _lvl, lambda v: float(v))
    _VAR_TO_GRIB[f"vorticity_{_lvl}hPa"] = ("vo", _lvl, lambda v: float(v) * 1e5)
    _VAR_TO_GRIB[f"divergence_{_lvl}hPa"] = ("d", _lvl, lambda v: float(v) * 1e5)


def _load_grib_datasets():
    global _GRIB_DS_LIST
    if _GRIB_DS_LIST is not None:
        return _GRIB_DS_LIST
    if not _g_os.path.exists(_GRIB_FILE_PATH):
        _GRIB_DS_LIST = []
        return _GRIB_DS_LIST
    try:
        _GRIB_DS_LIST = _cfgrib.open_datasets(_GRIB_FILE_PATH)
    except Exception:
        _GRIB_DS_LIST = []
    return _GRIB_DS_LIST


def _find_grib_dataset(ds_list, req_vars, req_level=None):
    for ds in ds_list:
        if not all(rv in ds.data_vars for rv in req_vars):
            continue
        if req_level is not None:
            if "isobaricInhPa" not in ds.coords:
                continue
            lvls = _np.asarray(ds.coords["isobaricInhPa"].values, dtype=float).ravel()
            if lvls.size == 0 or float(_np.min(_np.abs(lvls - float(req_level)))) > 0.5:
                continue
        return ds
    return None


def _select_level_idx(da, req_level):
    if "isobaricInhPa" not in da.dims or req_level is None:
        return da
    lvls = _np.asarray(da.coords["isobaricInhPa"].values, dtype=float).ravel()
    idx = int(_np.argmin(_np.abs(lvls - float(req_level))))
    return da.isel(isobaricInhPa=idx)


def _wind_speed_from_uv(u_val, v_val):
    return _np.sqrt(_np.asarray(u_val, dtype=float) ** 2 + _np.asarray(v_val, dtype=float) ** 2)


def _wind_dir_from_uv(u_val, v_val):
    u_arr = _np.asarray(u_val, dtype=float)
    v_arr = _np.asarray(v_val, dtype=float)
    return (_np.degrees(_np.arctan2(-u_arr, -v_arr)) + 360.0) % 360.0


def _grib_point_series(lat: float, lon: float, var_key: str, step_hours: int = 1) -> list[dict]:
    ck = (round(float(lat), 2), round(float(lon), 2), var_key, int(step_hours))
    if ck in _GRIB_SERIES_CACHE:
        return _GRIB_SERIES_CACHE[ck]

    mapping = _VAR_TO_GRIB.get(var_key)
    if not mapping:
        return []
    gvar, req_level, conv = mapping
    ds_list = _load_grib_datasets()
    if not ds_list:
        return []

    if gvar == "__lsp_from_tp_cp__":
        ds_tp = _find_grib_dataset(ds_list, ["tp"], req_level=None)
        ds_cp = _find_grib_dataset(ds_list, ["cp"], req_level=None)
        if ds_tp is None or "tp" not in ds_tp.data_vars:
            return []
        da_tp = ds_tp["tp"]
        lats_tp = _np.asarray(da_tp["latitude"].values, dtype=float)
        lons_tp = _np.asarray(da_tp["longitude"].values, dtype=float)
        lat_i_tp = int(_np.argmin(_np.abs(lats_tp - float(lat))))
        lon_val = float(lon)
        if _np.nanmax(lons_tp) > 180.0 and lon_val < 0.0:
            lon_val += 360.0
        elif _np.nanmax(lons_tp) <= 180.0 and lon_val > 180.0:
            lon_val -= 360.0
        lon_i_tp = int(_np.argmin(_np.abs(lons_tp - lon_val)))

        cp_val = 0.0
        if ds_cp is not None and "cp" in ds_cp.data_vars:
            da_cp = ds_cp["cp"]
            lats_cp = _np.asarray(da_cp["latitude"].values, dtype=float)
            lons_cp = _np.asarray(da_cp["longitude"].values, dtype=float)
            lat_i_cp = int(_np.argmin(_np.abs(lats_cp - float(lat))))
            lon_val_cp = float(lon)
            if _np.nanmax(lons_cp) > 180.0 and lon_val_cp < 0.0:
                lon_val_cp += 360.0
            elif _np.nanmax(lons_cp) <= 180.0 and lon_val_cp > 180.0:
                lon_val_cp -= 360.0
            lon_i_cp = int(_np.argmin(_np.abs(lons_cp - lon_val_cp)))
            sub_cp = da_cp.isel(latitude=lat_i_cp, longitude=lon_i_cp)
            if "step" in sub_cp.dims:
                sub_cp = sub_cp.isel(step=0)
            raw_cp = float(sub_cp.values)
            if _np.isfinite(raw_cp):
                cp_val = raw_cp

        out = []
        base_dt = _pd.to_datetime(ds_tp["time"].values) if "time" in ds_tp.coords else _pd.Timestamp.utcnow()
        steps_arr = da_tp["step"].values if "step" in da_tp.dims else [0]
        for s_i, st_v in enumerate(steps_arr):
            raw_tp = float(da_tp.isel(step=s_i, latitude=lat_i_tp, longitude=lon_i_tp).values) if "step" in da_tp.dims else float(da_tp.isel(latitude=lat_i_tp, longitude=lon_i_tp).values)
            if not _np.isfinite(raw_tp):
                continue
            mm_val = max(0.0, (raw_tp - cp_val) * 1000.0)
            t_stamp = base_dt + _pd.to_timedelta(st_v)
            out.append({"time": _pd.Timestamp(t_stamp).strftime("%Y-%m-%dT%H:00:00"), "value": round(mm_val, 3)})
        return out

    if gvar in ("__wind_spd_10m__", "__wind_dir_10m__"):
        req_vars = ["u10", "v10"]
    elif gvar in ("__wind_spd_lvl__", "__wind_dir_lvl__"):
        req_vars = ["u", "v"]
    else:
        req_vars = [gvar]

    chosen_ds = _find_grib_dataset(ds_list, req_vars, req_level=req_level)
    if chosen_ds is None:
        return []

    try:
        lats = _np.asarray(chosen_ds["latitude"].values, dtype=float)
        lons = _np.asarray(chosen_ds["longitude"].values, dtype=float)
        lat_idx = int(_np.argmin(_np.abs(lats - float(lat))))
        lon_val = float(lon)
        if _np.nanmax(lons) > 180.0 and lon_val < 0.0:
            lon_val += 360.0
        elif _np.nanmax(lons) <= 180.0 and lon_val > 180.0:
            lon_val -= 360.0
        lon_idx = int(_np.argmin(_np.abs(lons - lon_val)))

        if gvar == "__wind_spd_10m__":
            u_da = chosen_ds["u10"].isel(latitude=lat_idx, longitude=lon_idx)
            v_da = chosen_ds["v10"].isel(latitude=lat_idx, longitude=lon_idx)
            arr_vals = _wind_speed_from_uv(u_da.values, v_da.values)
            ref_da = u_da
        elif gvar == "__wind_dir_10m__":
            u_da = chosen_ds["u10"].isel(latitude=lat_idx, longitude=lon_idx)
            v_da = chosen_ds["v10"].isel(latitude=lat_idx, longitude=lon_idx)
            arr_vals = _wind_dir_from_uv(u_da.values, v_da.values)
            ref_da = u_da
        elif gvar == "__wind_spd_lvl__":
            u_da = _select_level_idx(chosen_ds["u"].isel(latitude=lat_idx, longitude=lon_idx), req_level)
            v_da = _select_level_idx(chosen_ds["v"].isel(latitude=lat_idx, longitude=lon_idx), req_level)
            arr_vals = _wind_speed_from_uv(u_da.values, v_da.values)
            ref_da = u_da
        elif gvar == "__wind_dir_lvl__":
            u_da = _select_level_idx(chosen_ds["u"].isel(latitude=lat_idx, longitude=lon_idx), req_level)
            v_da = _select_level_idx(chosen_ds["v"].isel(latitude=lat_idx, longitude=lon_idx), req_level)
            arr_vals = _wind_dir_from_uv(u_da.values, v_da.values)
            ref_da = u_da
        else:
            da = _select_level_idx(chosen_ds[gvar].isel(latitude=lat_idx, longitude=lon_idx), req_level)
            arr_vals = _np.asarray(da.values, dtype=float)
            ref_da = da

        if "valid_time" in ref_da.coords:
            vt_raw = _np.atleast_1d(_pd.to_datetime(ref_da["valid_time"].values))
            vt = _pd.DatetimeIndex(vt_raw).ravel()
        elif "time" in ref_da.coords and "step" in ref_da.coords:
            t0 = _np.atleast_1d(_pd.to_datetime(ref_da["time"].values))
            st = _np.atleast_1d(_pd.to_timedelta(ref_da["step"].values))
            vt = _pd.to_datetime((t0[:, None] + st[None, :]).ravel())
        elif "time" in ref_da.coords:
            t0 = _np.atleast_1d(_pd.to_datetime(ref_da["time"].values))
            vt = _pd.DatetimeIndex(t0).ravel()
        else:
            return []

        vals_flat = arr_vals.ravel()
        rows = []
        for idx_t, ts in enumerate(vt):
            if idx_t >= len(vals_flat):
                break
            raw_v = vals_flat[idx_t]
            if _np.isnan(raw_v):
                continue
            rows.append({
                "time": _pd.Timestamp(ts).strftime("%Y-%m-%dT%H:00:00"),
                "value": round(conv(raw_v), 3),
            })
        rows.sort(key=lambda r: r["time"])
        if step_hours > 1 and rows:
            rows = rows[::step_hours]
        _GRIB_SERIES_CACHE[ck] = rows
        return rows
    except Exception:
        return []


def _parse_iso_naive(dt_str):
    if not dt_str:
        return None
    s = dt_str.strip().replace("Z", "").replace("z", "").replace(" ", "T")
    if len(s) == 16:
        s += ":00"
    try:
        from datetime import datetime as _dt
        return _dt.fromisoformat(s[:19])
    except ValueError:
        return None

def _match_series_item(series_items, dt_str):
    valid_items = [it for it in series_items if it.get("value") is not None]
    if not valid_items:
        return None, None
    req_dt = _parse_iso_naive(dt_str)
    if req_dt is None:
        return valid_items[0], 0.0
    best_item = None
    best_diff = None
    for it in valid_items:
        it_dt = _parse_iso_naive(str(it.get("time", "")))
        if it_dt is None:
            continue
        diff_h = abs((it_dt - req_dt).total_seconds()) / 3600.0
        if best_diff is None or diff_h < best_diff:
            best_diff = diff_h
            best_item = it
    if best_item is None:
        return valid_items[0], None
    return best_item, round(best_diff, 2)

def get_point_series(lat: float, lon: float, var_key: str, step_hours: int) -> dict:
    provider = provider_for_var(var_key)
    ck = (provider, round(lat, 2), round(lon, 2), var_key, step_hours)
    if ck in POINT_CACHE:
        return POINT_CACHE[ck]

    if provider == "ECMWF":
        g_series = _grib_point_series(lat, lon, var_key, step_hours)
        if g_series:
            res = {"status": "CANLI", "source": "ECMWF-GRIB2", "step_hours": step_hours, "series": g_series}
            POINT_CACHE[ck] = res
            return res
        if _g_os.path.exists(_GRIB_FILE_PATH):
            res = {"status": "DATA YOK", "source": "DATA YOK (ECMWF-GRIB2)", "step_hours": step_hours, "series": []}
            POINT_CACHE[ck] = res
            return res

    raw_obj, state = fetch_series_raw(provider, str(round(lat, 2)), str(round(lon, 2)), var_key)
    if isinstance(raw_obj, dict) and raw_obj.get("hourly"):
        series = parse_series(raw_obj, var_key, step_hours)
        res = {"status": "CANLI", "source": provider, "step_hours": step_hours, "series": series}
        POINT_CACHE[ck] = res
        return res

    return {"status": "DATA YOK", "source": f"DATA YOK ({provider} {state})", "step_hours": step_hours, "series": []}

def _to_naive_utc_ts(dt_val):
    ts = _pd.Timestamp(dt_val)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts

def _to_naive_utc_idx(idx_like):
    idx = _pd.DatetimeIndex(_pd.to_datetime(idx_like))
    if idx.tz is not None:
        idx = idx.tz_convert("UTC").tz_localize(None)
    return idx

def _pick_step_idx(da, step_hours, dt_obj=None):
    if "step" not in da.dims:
        return None
    if dt_obj is not None:
        target_ts = _to_naive_utc_ts(dt_obj)
        if "valid_time" in da.coords:
            vt = _to_naive_utc_idx(_np.asarray(da["valid_time"].values).ravel())
            return int(_np.argmin(_np.abs((vt - target_ts).total_seconds())))
        if "time" in da.coords:
            t0 = _pd.to_datetime(_np.asarray(da["time"].values).ravel())[0]
            st = _pd.to_timedelta(_np.asarray(da["step"].values).ravel())
            vt = _to_naive_utc_idx(t0 + st)
            return int(_np.argmin(_np.abs((vt - target_ts).total_seconds())))
    st_vals = _pd.to_timedelta(da["step"].values)
    target = _pd.Timedelta(hours=int(step_hours))
    diffs = abs(st_vals - target)
    return int(_np.argmin(diffs))

def _slice_da_step_lat_lon(da, step_hours, lat_idxs, lon_idxs, dt_obj=None):
    idxers = {"latitude": lat_idxs, "longitude": lon_idxs}
    if "step" in da.dims:
        s_idx = _pick_step_idx(da, step_hours, dt_obj=dt_obj)
        if s_idx is not None:
            idxers["step"] = s_idx
    return da.isel(**idxers)

def _grib_grid_snapshot(var_key: str, dt_obj: datetime, south: float, north: float, west: float, east: float, step_hours: int, n_lat: int, n_lon: int):
    mapping = _VAR_TO_GRIB.get(var_key)
    if not mapping:
        return None
    gvar, req_level, conv = mapping
    ds_list = _load_grib_datasets()
    if not ds_list:
        return None

    if gvar == "__lsp_from_tp_cp__":
        ds_tp = _find_grib_dataset(ds_list, ["tp"], req_level=None)
        ds_cp = _find_grib_dataset(ds_list, ["cp"], req_level=None)
        if ds_tp is None or "tp" not in ds_tp.data_vars:
            return None
        da_tp = ds_tp["tp"]
        lats_tp = _np.asarray(da_tp["latitude"].values, dtype=float)
        lons_tp = _np.asarray(da_tp["longitude"].values, dtype=float)
        lat_grid = _np.linspace(float(south), float(north), max(2, int(n_lat)))
        lon_grid = _np.linspace(float(west), float(east), max(2, int(n_lon)))
        lat_idxs = [int(_np.argmin(_np.abs(lats_tp - la))) for la in lat_grid]
        lon_idxs = []
        for lo in lon_grid:
            lo_q = float(lo)
            if _np.nanmax(lons_tp) > 180.0 and lo_q < 0.0:
                lo_q += 360.0
            elif _np.nanmax(lons_tp) <= 180.0 and lo_q > 180.0:
                lo_q -= 360.0
            lon_idxs.append(int(_np.argmin(_np.abs(lons_tp - lo_q))))
        sub_tp = _slice_da_step_lat_lon(da_tp, step_hours, lat_idxs, lon_idxs, dt_obj=dt_obj)
        arr_tp = _np.asarray(sub_tp.values, dtype=float)

        arr_cp = _np.zeros_like(arr_tp, dtype=float)
        if ds_cp is not None and "cp" in ds_cp.data_vars:
            da_cp = ds_cp["cp"]
            lats_cp = _np.asarray(da_cp["latitude"].values, dtype=float)
            lons_cp = _np.asarray(da_cp["longitude"].values, dtype=float)
            lat_idxs_cp = [int(_np.argmin(_np.abs(lats_cp - la))) for la in lat_grid]
            lon_idxs_cp = []
            for lo in lon_grid:
                lo_q = float(lo)
                if _np.nanmax(lons_cp) > 180.0 and lo_q < 0.0:
                    lo_q += 360.0
                elif _np.nanmax(lons_cp) <= 180.0 and lo_q > 180.0:
                    lo_q -= 360.0
                lon_idxs_cp.append(int(_np.argmin(_np.abs(lons_cp - lo_q))))
            sub_cp = _slice_da_step_lat_lon(da_cp, step_hours, lat_idxs_cp, lon_idxs_cp, dt_obj=dt_obj)
            arr_cp = _np.broadcast_to(_np.asarray(sub_cp.values, dtype=float), arr_tp.shape)

        mm_grid = _np.maximum(0.0, (arr_tp - arr_cp) * 1000.0)
        vals_out = []
        live_cnt = 0
        for r in range(len(lat_grid)):
            row = []
            for c in range(len(lon_grid)):
                val = float(mm_grid[r, c])
                if _np.isfinite(val):
                    row.append(round(val, 3))
                    live_cnt += 1
                else:
                    row.append(None)
            vals_out.append(row)
        if live_cnt == 0:
            return None
        return {
            "key": var_key,
            "provider": "ECMWF",
            "status": "CANLI",
            "source": "ECMWF-GRIB2",
            "datetime": dt_obj.strftime("%Y-%m-%dT%H:00:00"),
            "step_hours": step_hours,
            "lats": [round(float(x), 4) for x in lat_grid],
            "lons": [round(float(x), 4) for x in lon_grid],
            "values": vals_out,
        }

    if gvar in ("__wind_spd_10m__", "__wind_dir_10m__"):
        req_vars = ["u10", "v10"]
    elif gvar in ("__wind_spd_lvl__", "__wind_dir_lvl__"):
        req_vars = ["u", "v"]
    else:
        req_vars = [gvar]

    chosen_ds = _find_grib_dataset(ds_list, req_vars, req_level=req_level)
    if chosen_ds is None:
        return None

    lats = _np.asarray(chosen_ds["latitude"].values, dtype=float)
    lons = _np.asarray(chosen_ds["longitude"].values, dtype=float)
    lat_grid = _np.linspace(float(south), float(north), max(2, int(n_lat)))
    lon_grid = _np.linspace(float(west), float(east), max(2, int(n_lon)))

    lat_idxs = [int(_np.argmin(_np.abs(lats - la))) for la in lat_grid]
    lon_idxs = []
    for lo in lon_grid:
        lo_q = float(lo)
        if _np.nanmax(lons) > 180.0 and lo_q < 0.0:
            lo_q += 360.0
        elif _np.nanmax(lons) <= 180.0 and lo_q > 180.0:
            lo_q -= 360.0
        lon_idxs.append(int(_np.argmin(_np.abs(lons - lo_q))))

    target_ts = _to_naive_utc_ts(dt_obj)

    def _step_index_for(da_obj):
        if "valid_time" in da_obj.coords:
            vt = _to_naive_utc_idx(_np.asarray(da_obj["valid_time"].values).ravel())
        else:
            t0 = _pd.to_datetime(_np.asarray(da_obj["time"].values).ravel())[0]
            st = _pd.to_timedelta(_np.asarray(da_obj["step"].values).ravel())
            vt = _to_naive_utc_idx(t0 + st)
        return int(_np.argmin(_np.abs((vt - target_ts).total_seconds())))

    if gvar in ("__wind_spd_10m__", "__wind_dir_10m__"):
        da_u = chosen_ds["u10"]
        da_v = chosen_ds["v10"]
        step_idx = _step_index_for(da_u)
        u_sub = _np.asarray(da_u.isel(step=step_idx, latitude=lat_idxs, longitude=lon_idxs).values, dtype=float)
        v_sub = _np.asarray(da_v.isel(step=step_idx, latitude=lat_idxs, longitude=lon_idxs).values, dtype=float)
        mat = _wind_speed_from_uv(u_sub, v_sub) if gvar == "__wind_spd_10m__" else _wind_dir_from_uv(u_sub, v_sub)
    elif gvar in ("__wind_spd_lvl__", "__wind_dir_lvl__"):
        da_u = _select_level_idx(chosen_ds["u"], req_level)
        da_v = _select_level_idx(chosen_ds["v"], req_level)
        step_idx = _step_index_for(da_u)
        u_sub = _np.asarray(da_u.isel(step=step_idx, latitude=lat_idxs, longitude=lon_idxs).values, dtype=float)
        v_sub = _np.asarray(da_v.isel(step=step_idx, latitude=lat_idxs, longitude=lon_idxs).values, dtype=float)
        mat = _wind_speed_from_uv(u_sub, v_sub) if gvar == "__wind_spd_lvl__" else _wind_dir_from_uv(u_sub, v_sub)
    else:
        da = _select_level_idx(chosen_ds[gvar], req_level)
        sub = _slice_da_step_lat_lon(da, step_hours, lat_idxs, lon_idxs, dt_obj=dt_obj)
        mat = _np.asarray(sub.values, dtype=float)

    vals_out = []
    live_cnt = 0
    for r_i in range(len(lat_grid)):
        row = []
        for c_i in range(len(lon_grid)):
            raw_v = float(mat[r_i, c_i])
            if _np.isnan(raw_v):
                row.append(None)
            else:
                row.append(round(conv(raw_v), 3))
                live_cnt += 1
        vals_out.append(row)

    if live_cnt == 0:
        return None
    return {
        "key": var_key,
        "provider": "ECMWF",
        "status": "CANLI",
        "source": "ECMWF-GRIB2",
        "datetime": dt_obj.strftime("%Y-%m-%dT%H:00:00"),
        "step_hours": step_hours,
        "lats": [round(float(x), 4) for x in lat_grid],
        "lons": [round(float(x), 4) for x in lon_grid],
        "values": vals_out,
    }

def get_grid_snapshot(var_key: str, dt_obj: datetime, south: float, north: float, west: float, east: float, step_hours: int) -> dict:
    provider = provider_for_var(var_key)
    iso_key = dt_obj.strftime("%Y-%m-%dT%H:00:00")
    gk = (provider, var_key, iso_key, step_hours, round(south, 1), round(north, 1), round(west, 1), round(east, 1))
    if gk in GRID_CACHE:
        return GRID_CACHE[gk]

    span_lat = min(170.0, max(0.5, abs(north - south)))
    span_lon = min(350.0, max(0.5, abs(east - west)))
    n_lat = min(17, max(9, int(round(span_lat / 0.45)) + 1))
    n_lon = min(35, max(13, int(round(span_lon / 0.55)) + 1))
    lats = [round(south + (north - south) * (i / max(1, n_lat - 1)), 2) for i in range(n_lat)]
    lons = [round(west + (east - west) * (j / max(1, n_lon - 1)), 2) for j in range(n_lon)]
    coords = [(r, c, lats[r], lons[c]) for r in range(n_lat) for c in range(n_lon)]
    grid_vals = [[None for _ in range(n_lon)] for _ in range(n_lat)]

    if provider == "ECMWF":
        g_grid = _grib_grid_snapshot(var_key, dt_obj, south, north, west, east, step_hours, n_lat, n_lon)
        if g_grid:
            g_grid["datetime"] = iso_key
            GRID_CACHE[gk] = g_grid
            return g_grid
        if _g_os.path.exists(_GRIB_FILE_PATH):
            return {
                "key": var_key,
                "provider": provider,
                "status": "DATA YOK",
                "source": "DATA YOK (ECMWF-GRIB2)",
                "datetime": iso_key,
                "step_hours": step_hours,
                "lats": lats,
                "lons": lons,
                "values": grid_vals,
            }

    live_count = 0
    state = "OK"
    chunk_size = 7 if provider == "CAMS" else len(coords)
    for start in range(0, len(coords), chunk_size):
        chunk = coords[start:start + chunk_size]
        lat_csv = ",".join(str(p[2]) for p in chunk)
        lon_csv = ",".join(str(p[3]) for p in chunk)
        raw_obj, st = fetch_series_raw(provider, lat_csv, lon_csv, var_key)
        if raw_obj is None:
            state = st
            break
        if start + chunk_size < len(coords):
            time.sleep(0.5)
        items = raw_obj if isinstance(raw_obj, list) else [raw_obj]
        if len(items) == len(chunk):
            for idx, (r_i, c_i, _, _) in enumerate(chunk):
                s_item = parse_series(items[idx], var_key, step_hours)
                matched = next((item["value"] for item in s_item if str(item.get("time", ""))[:16] == iso_key[:16]), None)
                grid_vals[r_i][c_i] = matched
                if matched is not None:
                    live_count += 1
        else:
            state = f"LEN_{len(items)}_NE_{len(chunk)}" 

    is_live = live_count > 0
    status = "CANLI" if is_live else "DATA YOK"
    source = provider if is_live else f"DATA YOK ({provider} {state})"

    out = {
        "key": var_key,
        "provider": provider,
        "status": status,
        "source": source,
        "datetime": iso_key,
        "step_hours": step_hours,
        "lats": lats,
        "lons": lons,
        "values": grid_vals,
    }
    if is_live:
        GRID_CACHE[gk] = out
    return out


_GEO_CACHE = {}


def resolve_marmara_place(lat: float, lon: float) -> dict:
    key = (round(lat, 4), round(lon, 4))
    now_ts = time.time()
    cached = _GEO_CACHE.get(key)
    if cached and (now_ts - cached[0]) < 3600.0:
        return cached[1]

    url = (
        "https://nominatim.openstreetmap.org/reverse?"
        + urllib.parse.urlencode({
            "format": "jsonv2",
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "zoom": "18",
            "addressdetails": "1",
            "accept-language": "tr",
        })
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "MarmaraWeatherDashboard/1.0 (anileken@local)"},
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            obj = json.loads(resp.read().decode("utf-8"))
        addr = obj.get("address", {}) if isinstance(obj, dict) else {}
        city = addr.get("province") or addr.get("city") or addr.get("state")
        district = (
            addr.get("town")
            or addr.get("city_district")
            or addr.get("county")
            or addr.get("municipality")
        )
        hood = (
            addr.get("neighbourhood")
            or addr.get("suburb")
            or addr.get("quarter")
            or addr.get("village")
            or addr.get("hamlet")
        )
        display_name = obj.get("display_name") if isinstance(obj, dict) else None
        res = {
            "city": city,
            "district": district,
            "neighborhood": hood,
            "display_name": display_name,
            "source": "osm_reverse",
        }
        _GEO_CACHE[key] = (now_ts, res)
        return res
    except Exception as e:
        res = {
            "city": None,
            "district": None,
            "neighborhood": None,
            "error": type(e).__name__,
            "source": "osm_reverse",
        }
        _GEO_CACHE[key] = (now_ts, res)
        return res


_CAMS_ALL_CACHE = {}


def get_all_cams_at_time(lat: float, lon: float, dt_iso: str) -> list[dict]:
    cams_vars = [v for v in build_variables() if v.get("provider") == "CAMS"]
    if not cams_vars:
        return []
    c_key = (round(lat, 1), round(lon, 1), (dt_iso or "")[:13])
    now_ts = time.time()
    cached = _CAMS_ALL_CACHE.get(c_key)
    if cached and (now_ts - cached[0]) < 3600.0:
        return cached[1]
    keys_csv = ",".join(v["key"] for v in cams_vars)
    if rate_limited("CAMS"):
        for _, (_, prev_rows) in reversed(list(_CAMS_ALL_CACHE.items())):
            if any(isinstance(x, dict) and x.get("value") is not None for x in (prev_rows or [])):
                return prev_rows
        rem = max(1, int(RATE_LIMIT_UNTIL.get("CAMS", 0.0) - time.time()))
        return [
            {
                "key": v["key"],
                "name": v["name"],
                "unit": v["unit"],
                "value": None,
                "status": "DATA YOK",
                "reason": f"429 ({rem}s)",
            }
            for v in cams_vars
        ]

    base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": f"{lat:.2f}",
        "longitude": f"{lon:.2f}",
        "hourly": keys_csv,
        "past_days": 1,
        "forecast_days": 1,
        "timezone": "UTC",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=2.5) as resp:
            raw_obj = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            hdr = e.headers.get("Retry-After") if e.headers else None
            wait_s = min(int(hdr), 3) if (hdr and hdr.isdigit()) else 2
            RATE_LIMIT_UNTIL["CAMS"] = time.time() + wait_s
            reason = f"429 ({wait_s}s)"
        else:
            reason = f"HTTP_{e.code}"
        fb = _find_cached_cams(lat, lon, dt_iso)
        if fb and fb.get("cams_all"):
            return fb["cams_all"]
        return [
            {
                "key": v["key"],
                "name": v["name"],
                "unit": v["unit"],
                "value": None,
                "status": "DATA YOK",
                "reason": reason,
            }
            for v in cams_vars
        ]
    except Exception as e:
        fb = _find_cached_cams(lat, lon, dt_iso)
        if fb and fb.get("cams_all"):
            return fb["cams_all"]
        return [
            {
                "key": v["key"],
                "name": v["name"],
                "unit": v["unit"],
                "value": None,
                "status": "DATA YOK",
                "reason": f"ERR:{type(e).__name__}",
            }
            for v in cams_vars
        ]

    hourly = raw_obj.get("hourly", {}) if isinstance(raw_obj, dict) else {}
    times = hourly.get("time", []) or []
    target_16 = (dt_iso or "")[:16]
    idx = None
    for i, t_str in enumerate(times):
        if str(t_str)[:16] == target_16:
            idx = i
            break

    out = []
    for v in cams_vars:
        k = v["key"]
        arr = hourly.get(k, []) or []
        val = None
        if idx is not None and idx < len(arr) and arr[idx] is not None:
            try:
                val = float(arr[idx])
            except (TypeError, ValueError):
                val = None
        out.append({
            "key": k,
            "name": v["name"],
            "unit": v["unit"],
            "value": val,
            "status": "CANLI" if val is not None else "DATA YOK",
        })
    if any(x.get("status") == "CANLI" for x in out):
        _CAMS_ALL_CACHE[c_key] = (time.time(), out)
        main_v = next((x["value"] for x in out if x.get("value") is not None), None)
        _save_cams_disk_entry(lat, lon, dt_iso, out, main_v)
    return out

import os as _os
import math as _math

_CAMS_DISK_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "cams_cache.json")
_CAMS_DISK_STORE = None


def _load_cams_disk_store() -> dict:
    global _CAMS_DISK_STORE
    if _CAMS_DISK_STORE is not None:
        return _CAMS_DISK_STORE
    try:
        if _os.path.exists(_CAMS_DISK_PATH):
            with open(_CAMS_DISK_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    _CAMS_DISK_STORE = data
                    return _CAMS_DISK_STORE
    except Exception:
        pass
    _CAMS_DISK_STORE = {"entries": []}
    return _CAMS_DISK_STORE


def _save_cams_disk_entry(lat: float, lon: float, dt_iso: str, cams_list: list[dict], main_val=None):
    store = _load_cams_disk_store()
    entries = store.setdefault("entries", [])
    item = {
        "lat": round(float(lat), 4),
        "lon": round(float(lon), 4),
        "dt": (dt_iso or "")[:19],
        "ts": time.time(),
        "main_val": main_val,
        "cams_all": cams_list,
    }
    entries.append(item)
    if len(entries) > 500:
        store["entries"] = entries[-500:]
    try:
        with open(_CAMS_DISK_PATH, "w", encoding="utf-8") as fh:
            json.dump(store, fh, ensure_ascii=False)
    except Exception:
        pass


def _find_cached_cams(lat: float, lon: float, dt_iso: str):
    store = _load_cams_disk_store()
    entries = store.get("entries", [])
    if not entries:
        return None
    target_h = (dt_iso or "")[:13]
    best = None
    best_score = 1e18
    for e in reversed(entries):
        cams = e.get("cams_all") or []
        if not any(x.get("status") == "CANLI" and x.get("value") is not None for x in cams):
            continue
        dlat = _math.radians(float(e.get("lat", lat)) - lat)
        dlon = _math.radians(float(e.get("lon", lon)) - lon)
        a = (
            _math.sin(dlat / 2) ** 2
            + _math.cos(_math.radians(lat))
            * _math.cos(_math.radians(float(e.get("lat", lat))))
            * _math.sin(dlon / 2) ** 2
        )
        dist_km = 6371.0 * 2 * _math.atan2(_math.sqrt(a), _math.sqrt(max(0.0, 1.0 - a)))
        hour_penalty = 0.0 if str(e.get("dt", ""))[:13] == target_h else 50.0
        score = dist_km + hour_penalty
        if score < best_score:
            best_score = score
            best = e
    return best

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/anileken/marmara_weather", **kwargs)

    def _send_json(self, obj: dict, code: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/variables":
            now_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            self._send_json({
                "models": ["ECMWF", "CAMS"],
                "min_date": (now_utc - timedelta(days=1)).strftime("%Y-%m-%d"),
                "max_date": (now_utc + timedelta(days=15)).strftime("%Y-%m-%d"),
                "pressure_levels_hpa": PRESSURE_LEVELS,
                "variables": VARIABLES,
            })
            return

        if parsed.path == "/api/point":
            q = urllib.parse.parse_qs(parsed.query)
            lat = float(q.get("lat", ["41.01"])[0])
            lon = float(q.get("lon", ["28.97"])[0])
            var_key = q.get("var", ["precipitation"])[0]
            step_h = int(q.get("step", ["1"])[0])
            if step_h not in (1, 3, 6):
                step_h = 1
            dt_str = q.get("datetime", [None])[0]
            data = get_point_series(lat, lon, var_key, step_h)
            series_items = data.get("series", [])
            best_item, time_diff_hours = _match_series_item(series_items, dt_str)
            val = best_item.get("value") if best_item else None
            matched_time = (best_item.get("time") if best_item else None) or dt_str
            has_val = data.get("status") == "CANLI" and val is not None
            var_unit = VAR_MAP.get(var_key, {}).get("unit")
            self._send_json({
                "status": "CANLI" if has_val else "DATA YOK",
                "source": "ECMWF" if (has_val and provider_for_var(var_key) == "ECMWF") else ("CAMS" if has_val else data.get("source")),
                "step_hours": step_h,
                "datetime": matched_time,
                "requested_datetime": dt_str,
                "time_diff_hours": time_diff_hours,
                "unit": var_unit,
                "value": (
                    val if has_val else (
                        (_find_cached_cams(lat, lon, dt_str or "") or {}).get("main_val")
                    )
                ),
                "location": resolve_marmara_place(lat, lon),
                "cams_all": []
            })
            return

        if parsed.path == "/api/grid":
            q = urllib.parse.parse_qs(parsed.query)
            var_key = q.get("var", ["precipitation"])[0]
            step_h = int(q.get("step", ["1"])[0])
            if step_h not in (1, 3, 6):
                step_h = 1
            dt_str = q.get("datetime", [None])[0]
            try:
                dt_obj = datetime.fromisoformat((dt_str or "").replace(" ", "T")[:19]).replace(tzinfo=timezone.utc)
            except Exception:
                dt_obj = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

            south = max(-60.0, min(75.0, float(q.get("south", ["-60.0"])[0])))
            north = max(-60.0, min(75.0, float(q.get("north", ["75.0"])[0])))
            west = max(-180.0, min(180.0, float(q.get("west", ["-180.0"])[0])))
            east = max(-180.0, min(180.0, float(q.get("east", ["180.0"])[0])))
            if north <= south:
                south, north = -60.0, 75.0
            if east <= west:
                west, east = -180.0, 180.0

            self._send_json(get_grid_snapshot(var_key, dt_obj, south, north, west, east, step_h))
            return

        super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("ECMWF + CAMS Sunucusu aktif: http://localhost:8000/")
    server.serve_forever()
