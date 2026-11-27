import json, re, time, urllib.parse, urllib.request
from pathlib import Path

html = Path("index.html").read_text(encoding="utf-8", errors="ignore")
m_vars = re.search(r"const VARS\s*=\s*\[(.*?)\n\s*\];", html, re.S)
entries = re.findall(r'\{\s*code:\s*"([^"]+)",\s*om:\s*"([^"]+)",\s*name:\s*"([^"]+)",\s*unit:\s*"([^"]+)"', m_vars.group(1))
lat, lng = 41.0082, 28.9784

def fetch_om(f_name, la=lat, lo=lng):
    qs = urllib.parse.urlencode({
        "latitude": f"{la:.4f}",
        "longitude": f"{lo:.4f}",
        "hourly": f_name,
        "timezone": "Europe/Istanbul",
        "forecast_days": 1
    })
    url = f"https://api.open-meteo.com/v1/ecmwf?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            arr = (data.get("hourly") or {}).get(f_name)
            if isinstance(arr, list):
                nums = [x for x in arr if isinstance(x, (int, float))]
                if nums:
                    return True, f"OK ({nums[min(len(nums)-1, 12)]})"
            return False, "BOS_NULL"
    except urllib.error.HTTPError as e:
        return False, f"HTTP_{e.code}"
    except Exception as e:
        return False, f"ERR_{type(e).__name__}"

ok_list, fail_list = [], []
print(f"{'KOD':<8} | {'ALAN':<30} | {'DURUM':<22} | AD")
print("-" * 90)

for code, om, name, unit in entries:
    if om.startswith("derived_"):
        if om == "derived_thickness_500_1000":
            ok1, s1 = fetch_om("geopotential_height_500hPa")
            time.sleep(0.35)
            ok2, s2 = fetch_om("geopotential_height_1000hPa")
            ok = ok1 and ok2
            status = "DERIVED_OK (Z500-Z1000)" if ok else f"NO_DATA ({s1}/{s2})"
        else:
            m_d = re.match(r"^derived_(vorticity|divergence)_([0-9]+hPa)$", om)
            if m_d:
                _, lvl = m_d.groups()
                ok1, s1 = fetch_om(f"wind_speed_{lvl}", lat + 0.25, lng)
                time.sleep(0.35)
                ok2, s2 = fetch_om(f"wind_direction_{lvl}", lat, lng + 0.25)
                ok = ok1 and ok2
                status = f"DERIVED_OK ({lvl})" if ok else f"NO_DATA ({s1}/{s2})"
            else:
                ok, status = False, "NO_DATA"
    else:
        ok, status = fetch_om(om)
    time.sleep(0.35)
    print(f"{code:<8} | {om:<30} | {status:<22} | {name} [{unit}]")
    (ok_list if ok else fail_list).append((code, om, name, status))

print(f"\nCALISAN: {len(ok_list)} | VERI_YOK: {len(fail_list)}")
for code, om, name, status in fail_list:
    print(f"  - {code} ({om}) -> {status}: {name}")
