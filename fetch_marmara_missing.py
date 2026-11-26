import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REGION_NAME = "Marmara Bölgesi"
SOURCE_LABEL = "Open-Meteo-ECMWF"

LATS = [39.5, 40.25, 41.0, 41.75, 42.5]
LONS = [26.0, 26.8333, 27.6667, 28.5, 29.3333, 30.1667, 31.0]

HOURLY_VARS = [
    "dew_point_2m",
    "precipitation_type",
    "total_column_integrated_water_vapour",
    "evapotranspiration",
    "cape",
    "convective_inhibition",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
]

points = [(la, lo) for la in LATS for lo in LONS]
CHUNK_SIZE = 4  # Küçük gruplar halinde çekerek 429 limitine takılmayı azaltır

collected = []
for idx in range(0, len(points), CHUNK_SIZE):
    batch = points[idx:idx + CHUNK_SIZE]
    b_lats = ",".join(str(p[0]) for p in batch)
    b_lons = ",".join(str(p[1]) for p in batch)
    params = {
        "latitude": b_lats,
        "longitude": b_lons,
        "hourly": ",".join(HOURLY_VARS),
        "models": "ecmwf_ifs025",
        "past_days": "2",
        "forecast_days": "2",
        "timezone": "UTC",
    }
    url = "https://api.open-meteo.com/v1/ecmwf?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "MarmaraWeatherDashboard/1.0"})

    ok = False
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            items = data if isinstance(data, list) else [data]
            for item in items:
                item["_region"] = REGION_NAME
                item["_source"] = SOURCE_LABEL
            collected.extend(items)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Bölge: {REGION_NAME} | Kaynak: {SOURCE_LABEL} | Grup {idx//CHUNK_SIZE + 1}: {len(batch)} nokta alındı ({len(collected)}/{len(points)})")
            ok = True
            break
        except urllib.error.HTTPError as e:
            wait = 4 * (attempt + 1)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Bölge: {REGION_NAME} | Kaynak: {SOURCE_LABEL} | Grup {idx//CHUNK_SIZE + 1} HTTP {e.code} -> {wait}s bekleniyor...")
            time.sleep(wait)
        except Exception as e:
            wait = 3 * (attempt + 1)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Bölge: {REGION_NAME} | Kaynak: {SOURCE_LABEL} | Grup {idx//CHUNK_SIZE + 1} Hata ({e}) -> {wait}s bekleniyor...")
            time.sleep(wait)

    if not ok:
        print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Bölge: {REGION_NAME} | Kaynak: {SOURCE_LABEL} | Grup {idx//CHUNK_SIZE + 1} atlandı.")
    time.sleep(2.0)

out = {
    "region": REGION_NAME,
    "source": SOURCE_LABEL,
    "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
    "lats": LATS,
    "lons": LONS,
    "records": collected,
}

with open("marmara_extra_ecmwf.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print(f"ÖZET -> Bölge: {REGION_NAME} | Kaynak: {SOURCE_LABEL} | Alınan nokta: {len(collected)}/{len(points)} | Dosya: marmara_extra_ecmwf.json")
