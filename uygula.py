import re
from pathlib import Path

p = Path("index.html")
s = p.read_text(encoding="utf-8", errors="ignore")

# 1) precipBundle kaldirilsin, her degisken tekil istensin
s, _ = re.subn(
    r'const precipBundle = \[.*?\];\s*const fieldsSet = new Set\(\[fieldName\]\.filter\(Boolean\)\);\s*if \(precipBundle\.includes\(fieldName\) \|\| v\.code === "wmo"\) \{\s*precipBundle\.forEach\(f => fieldsSet\.add\(f\)\);\s*\}\s*const fieldsParam = Array\.from\(fieldsSet\)\.map\(encodeURIComponent\)\.join\(","\);',
    'const fieldsParam = encodeURIComponent(fieldName);',
    s, count=1, flags=re.S
)

# 2) VARS sonuna turetilmis sinoptik alanlar eklensin
if "derived_vorticity_850hPa" not in s:
    s, n_dp = re.subn(
        r'(\{\s*code:\s*"dp850"[^\n]+\})',
        r'\1,\n'
        '    { code: "vor850", om: "derived_vorticity_850hPa", name: "850hPa Bağıl Vortisite", unit: "10⁻⁵ s⁻¹", min: -15, max: 25 },\n'
        '    { code: "vor500", om: "derived_vorticity_500hPa", name: "500hPa Bağıl Vortisite", unit: "10⁻⁵ s⁻¹", min: -20, max: 30 },\n'
        '    { code: "div850", om: "derived_divergence_850hPa", name: "850hPa Yatay Diverjans", unit: "10⁻⁵ s⁻¹", min: -15, max: 15 },\n'
        '    { code: "div250", om: "derived_divergence_250hPa", name: "250hPa Yatay Diverjans", unit: "10⁻⁵ s⁻¹", min: -15, max: 20 },\n'
        '    { code: "thk500", om: "derived_thickness_500_1000", name: "500-1000hPa Kalınlık", unit: "m", min: 5100, max: 5820 }',
        s, count=1
    )
    assert n_dp == 1, "dp850 satiri bulunamadi"

# 3) Turetilmis sinoptik alan hesaplayiciyi ekle
if "fetchDerivedEcmwfVal" not in s:
    helper = """const fetchDerivedEcmwfVal = async (lat, lng, fieldName, offsetHours) => {
      const reqDays = 16;
      const g = async (la, lo, f) => {
        const u = `https://api.open-meteo.com/v1/ecmwf?latitude=${la.toFixed(4)}&longitude=${lo.toFixed(4)}&hourly=${encodeURIComponent(f)}&timezone=Europe%2FIstanbul&forecast_days=${reqDays}`;
        const r = await fetch(u, { cache: "no-store" });
        if (!r.ok) return null;
        const v = extractNowVal(await r.json(), f, offsetHours);
        return (typeof v === "number" && Number.isFinite(v)) ? v : null;
      };
      if (fieldName === "derived_thickness_500_1000") {
        const [z5, z1] = await Promise.all([g(lat, lng, "geopotential_height_500hPa"), g(lat, lng, "geopotential_height_1000hPa")]);
        return (z5 === null || z1 === null) ? { val: null, tag: "Veri yok" } : { val: Number((z5 - z1).toFixed(1)), tag: "ECMWF" };
      }
      const m = fieldName.match(/^derived_(vorticity|divergence)_([0-9]+hPa)$/);
      if (!m) return { val: null, tag: "Veri yok" };
      const [, kind, lvl] = m, d = 0.25, rad = Math.PI / 180, R = 6371000;
      const dy = 2 * d * rad * R, dx = dy * Math.max(0.2, Math.cos(lat * rad));
      const uv = async (la, lo) => {
        const [ws, wd] = await Promise.all([g(la, lo, `wind_speed_${lvl}`), g(la, lo, `wind_direction_${lvl}`)]);
        if (ws === null || wd === null) return null;
        const th = wd * rad;
        return { u: -ws * Math.sin(th), v: -ws * Math.cos(th) };
      };
      const [e, w, n, so] = await Promise.all([uv(lat, lng + d), uv(lat, lng - d), uv(lat + d, lng), uv(lat - d, lng)]);
      if (!e || !w || !n || !so) return { val: null, tag: "Veri yok" };
      const raw = kind === "vorticity" ? ((e.v - w.v) / dx - (n.u - so.u) / dy) : ((e.u - w.u) / dx + (n.v - so.v) / dy);
      return { val: Number((raw * 1e5).toFixed(2)), tag: "ECMWF" };
    };
    const fetchRealVal = async"""
    s, n_fn = re.subn(r'const fetchRealVal = async', helper, s, count=1)
    assert n_fn == 1, "fetchRealVal bulunamadi"
    s, n_rd = re.subn(
        r'(const fieldName = v\.om \|\| v\.key \|\| v\.code;)',
        r'\1\n      if (String(fieldName).startsWith("derived_")) { try { return await fetchDerivedEcmwfVal(lat, lng, fieldName, offsetHours); } catch (_) { return { val: null, tag: "Veri yok" }; } }',
        s, count=1
    )
    assert n_rd == 1, "fieldName bulunamadi"

p.write_text(s, encoding="utf-8")
print("TAMAM_OK")
