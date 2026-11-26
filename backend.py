from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from ecmwf.opendata import Client
import xarray as xr
import numpy as np
import pandas as pd
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GRIB_FILE = "marmara_ecmwf.grib2"
PRESSURE_LEVELS = [1000, 850, 700, 500, 250, 50]

_GRIB_CACHE = {"mtime_ns": None, "path": None, "data": None}

def get_cached_grib_data(grib_path: str = GRIB_FILE, parser_fn=None):
    st = os.stat(grib_path)
    cur_mtime = st.st_mtime_ns
    if (
        _GRIB_CACHE["data"] is not None
        and _GRIB_CACHE["path"] == grib_path
        and _GRIB_CACHE["mtime_ns"] == cur_mtime
    ):
        return _GRIB_CACHE["data"]
    if parser_fn is None:
        raise RuntimeError("GRIB parser fonksiyonu bulunamadi.")
    parsed = parser_fn(grib_path)
    _GRIB_CACHE["path"] = grib_path
    _GRIB_CACHE["mtime_ns"] = cur_mtime
    _GRIB_CACHE["data"] = parsed
    return parsed


def _retrieve_safe(client: Client, **kwargs):
    try:
        client.retrieve(**kwargs)
        return True
    except Exception as e:
        print(f"ECMWF retrieve uyarisi ({kwargs.get('typeOfLevel', 'sfc')}): {e}")
        return False


def download_latest_ecmwf():
    client = Client(source="ecmwf")
    steps = list(range(0, 385, 3))
    tmp_sfc = "marmara_sfc.tmp.grib2"
    tmp_pl = "marmara_pl.tmp.grib2"

    for p in (tmp_sfc, tmp_pl):
        if os.path.exists(p):
            os.remove(p)

    ok_sfc = _retrieve_safe(
        client,
        step=steps,
        type="fc",
        param=["tp", "2t", "10u", "10v", "msl", "sp"],
        target=tmp_sfc,
    )
    if not ok_sfc:
        _retrieve_safe(
            client,
            step=steps,
            type="fc",
            param=["tp", "2t", "10u", "10v"],
            target=tmp_sfc,
        )

    _retrieve_safe(
        client,
        step=steps,
        type="fc",
        levtype="pl",
        levelist=PRESSURE_LEVELS,
        param=["z", "t", "u", "v", "r"],
        target=tmp_pl,
    )

    merged_parts = []
    for part in (tmp_sfc, tmp_pl):
        if os.path.exists(part) and os.path.getsize(part) > 0:
            with open(part, "rb") as f_in:
                merged_parts.append(f_in.read())
            os.remove(part)

    if merged_parts:
        with open(GRIB_FILE, "wb") as f_out:
            for chunk in merged_parts:
                f_out.write(chunk)
        for idx_file in os.listdir("."):
            if idx_file.startswith(GRIB_FILE + ".") and idx_file.endswith(".idx"):
                os.remove(idx_file)


@app.on_event("startup")
def startup_event():
    if not os.path.exists(GRIB_FILE):
        print("ECMWF verisi indiriliyor...")
        download_latest_ecmwf()
        print("Veri hazir!")


@app.get("/")
def serve_frontend():
    return FileResponse("index.html")


def _sub_grid(ds):
    lat_vals = ds.latitude.values
    lon_vals = ds.longitude.values
    lat_slice = slice(43.0, 35.0) if lat_vals[0] >= lat_vals[-1] else slice(35.0, 43.0)
    lon_slice = slice(25.0, 45.0) if lon_vals[0] <= lon_vals[-1] else slice(45.0, 25.0)
    return ds.sel(latitude=lat_slice, longitude=lon_slice)


def _raw__open_pl_datasets(grib_path: str):
    pl_map = {}
    for lvl in PRESSURE_LEVELS:
        try:
            ds_lvl = xr.open_dataset(
                grib_path,
                engine="cfgrib",
                backend_kwargs={"filter_by_keys": {"typeOfLevel": "isobaricInhPa", "level": lvl}},
            )
            pl_map[str(lvl)] = _sub_grid(ds_lvl)
        except Exception:
            continue
    return pl_map



import math
from fastapi.responses import JSONResponse


import json as _json
import math as _math
from fastapi.responses import Response as _JSONRawResponse

def _to_pure_json_safe(obj):
    if obj is None or isinstance(obj, (bool, str)):
        return obj
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        return None if (_math.isnan(v) or _math.isinf(v)) else round(v, 4)
    if isinstance(obj, np.ndarray):
        return _to_pure_json_safe(obj.tolist())
    if isinstance(obj, (tuple, set, list)):
        return [_to_pure_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _to_pure_json_safe(v) for k, v in obj.items()}
    return str(obj)

@app.get("/api/weather")
def get_weather_grid():
    try:
        _st = os.stat(GRIB_FILE)
        _mt = _st.st_mtime_ns
        if _GRIB_CACHE.get("data") is not None and _GRIB_CACHE.get("mtime_ns") == _mt:
            return _GRIB_CACHE["data"]
    except OSError:
        pass
    ds_sfc = xr.open_dataset(
        GRIB_FILE,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "surface"}},
    )
    ds_wind = xr.open_dataset(
        GRIB_FILE,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround", "level": 10}},
    )
    ds_2m = xr.open_dataset(
        GRIB_FILE,
        engine="cfgrib",
        backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround", "level": 2}},
    )

    sfc_sub = _sub_grid(ds_sfc)
    wind_sub = _sub_grid(ds_wind)
    t2m_sub = _sub_grid(ds_2m)
    pl_map = _open_pl_datasets(GRIB_FILE)

    lats = sfc_sub.latitude.values.tolist()
    lons = sfc_sub.longitude.values.tolist()
    valid_times = pd.to_datetime(sfc_sub.valid_time.values) + pd.Timedelta(hours=3)

    tp_cum = sfc_sub["tp"].values * 1000.0
    tp_step = np.clip(np.diff(tp_cum, axis=0, prepend=tp_cum[0:1]), 0, None)

    t2m_var = "t2m" if "t2m" in t2m_sub else "2t"
    t2m_c = t2m_sub[t2m_var].values - 273.15
    u10 = wind_sub["u10"].values
    v10 = wind_sub["v10"].values

    msl_hpa = None
    if "msl" in sfc_sub:
        msl_hpa = sfc_sub["msl"].values / 100.0
    elif "sp" in sfc_sub:
        msl_hpa = sfc_sub["sp"].values / 100.0

    steps_data = []
    for i, t in enumerate(valid_times):
        item = {
            "time_tsi": t.strftime("%d %b %Y %H:%M TSİ"),
            "tp": np.round(tp_step[i], 2).tolist(),
            "t2m": np.round(t2m_c[i], 1).tolist(),
            "u10": np.round(u10[i], 1).tolist(),
            "v10": np.round(v10[i], 1).tolist(),
            "msl": np.round(msl_hpa[i], 1).tolist() if msl_hpa is not None and i < msl_hpa.shape[0] else None,
        }
        if msl_hpa is not None and i < len(msl_hpa):
            item["msl"] = np.round(msl_hpa[i], 1).tolist()

        if pl_map:
            lvl_dict = {}
            for lvl_str, ds_l in pl_map.items():
                entry = {}
                if "z" in ds_l and i < ds_l["z"].shape[0]:
                    entry["z"] = np.round(ds_l["z"].values[i] / 9.80665, 0).tolist()
                if "t" in ds_l and i < ds_l["t"].shape[0]:
                    entry["t"] = np.round(ds_l["t"].values[i] - 273.15, 1).tolist()
                if "u" in ds_l and i < ds_l["u"].shape[0]:
                    entry["u"] = np.round(ds_l["u"].values[i], 1).tolist()
                if "v" in ds_l and i < ds_l["v"].shape[0]:
                    entry["v"] = np.round(ds_l["v"].values[i], 1).tolist()
                if "r" in ds_l and i < ds_l["r"].shape[0]:
                    entry["r"] = np.round(np.clip(ds_l["r"].values[i], 0, 100), 0).tolist()
                if entry:
                    lvl_dict[lvl_str] = entry
            if lvl_dict:
                item["levels"] = lvl_dict

        steps_data.append(item)

    raw_payload = _to_pure_json_safe({
        "lats": lats,
        "lons": lons,
        "steps": steps_data,
    })
    clean_str = _json.dumps(raw_payload, allow_nan=False, ensure_ascii=False)
    return _JSONRawResponse(content=clean_str, media_type="application/json")

@app.get("/api/refresh")
def refresh_data():
    download_latest_ecmwf()
    return {"status": "updated"}

def _open_pl_datasets(grib_path: str = GRIB_FILE):
    return get_cached_grib_data(grib_path, _raw__open_pl_datasets)
