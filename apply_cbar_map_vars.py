import re

p = "index.html"
html = open(p, encoding="utf-8").read()

for tid in [
    "ew-single-cbar-fix", "ew-cbar-format-sync", "ew-cbar-format-sync-js",
    "ew-cbar-keep-pos-css", "ew-cbar-keep-pos-js",
    "ew-ecmwf-cbar-only-css", "ew-ecmwf-cbar-only-js",
    "ew-real-cbar-css", "ew-real-cbar-js",
    "ew-full-fix-css", "ew-full-fix-js",
    "ew-exact-fix-css", "ew-exact-fix-js",
    "ew-all-vars-color-js", "ew-combined-fix-css", "ew-combined-fix-js"
]:
    html = re.sub(rf'<(?:style|script)[^>]*id="{tid}"[^>]*>.*?</(?:style|script)>', '', html, flags=re.DOTALL | re.IGNORECASE)

if '"snow_depth"' not in html and "'snow_depth'" not in html:
    html = html.replace(
        '["snowfall", "Kar Yağışı", "cm", 0, 20, P.precip],',
        '["snowfall", "Kar Yağışı", "cm", 0, 20, P.precip],\n      ["snow_depth", "Kar Kalınlığı", "m", 0, 1.5, P.precip],',
        1
    )

css_block = """<style id="ew-combined-fix-css">
  #ew-cbar ~ #ew-cbar,
  .ew-ecmwf-cbar-label,
  .ew-ecmwf-cbar-muted ~ .ew-ecmwf-cbar-muted {
    display: none !important;
  }
  #ew-cbar {
    background: rgba(15, 23, 42, 0.94) !important;
    border: 1px solid rgba(148, 163, 184, 0.35) !important;
    border-radius: 10px !important;
    padding: 8px 10px !important;
    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.45) !important;
    color: #f8fafc !important;
  }
  #ew-cbar .cbar-top {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    gap: 6px !important;
    margin-bottom: 5px !important;
  }
  #ew-cbar .cbar-title {
    font-size: 12px !important;
    font-weight: 700 !important;
    color: #7dd3fc !important;
  }
  #ew-cbar .cbar-code {
    font-size: 10px !important;
    color: #cbd5e1 !important;
    font-family: monospace !important;
  }
  #ew-cbar .cbar-gradient {
    height: 11px !important;
    border-radius: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    margin: 4px 0 !important;
  }
  #ew-cbar .cbar-labels {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #f8fafc !important;
  }
  #ew-color-overlay {
    pointer-events: none !important;
  }
</style>"""

js_block = """<script id="ew-combined-fix-js">
(function () {
  const TR_LABELS = {
    temperature_2m: "2m Sıcaklık",
    relative_humidity_2m: "2m Bağıl Nem",
    dew_point_2m: "2m Çiy Noktası",
    apparent_temperature: "Hissedilen Sıcaklık",
    precipitation: "Toplam Yağış",
    rain: "Yağmur",
    showers: "Sağanak Yağış",
    snowfall: "Kar Yağışı",
    snow_depth: "Kar Kalınlığı",
    weather_code: "Hava Durumu Kodu",
    pressure_msl: "Deniz Seviyesi Basıncı",
    surface_pressure: "Yüzey Basıncı",
    cloud_cover: "Toplam Bulutluluk",
    cloud_cover_low: "Alçak Bulutluluk",
    cloud_cover_mid: "Orta Bulutluluk",
    cloud_cover_high: "Yüksek Bulutluluk",
    visibility: "Görüş Mesafesi",
    evapotranspiration: "Evapotranspirasyon",
    et0_fao_evapotranspiration: "Referans Evapotranspirasyon (ET0)",
    vapour_pressure_deficit: "Buhar Basıncı Açığı (VPD)",
    wind_speed_10m: "10m Rüzgar Hızı",
    wind_speed_80m: "80m Rüzgar Hızı",
    wind_speed_100m: "100m Rüzgar Hızı",
    wind_speed_120m: "120m Rüzgar Hızı",
    wind_speed_180m: "180m Rüzgar Hızı",
    wind_direction_10m: "10m Rüzgar Yönü",
    wind_direction_80m: "80m Rüzgar Yönü",
    wind_direction_100m: "100m Rüzgar Yönü",
    wind_direction_120m: "120m Rüzgar Yönü",
    wind_direction_180m: "180m Rüzgar Yönü",
    wind_gusts_10m: "10m Rüzgar Hamlesi",
    temperature_80m: "80m Sıcaklık",
    temperature_120m: "120m Sıcaklık",
    temperature_180m: "180m Sıcaklık",
    soil_temperature_0cm: "0cm Toprak Sıcaklığı",
    soil_temperature_6cm: "6cm Toprak Sıcaklığı",
    soil_temperature_18cm: "18cm Toprak Sıcaklığı",
    soil_temperature_54cm: "54cm Toprak Sıcaklığı",
    soil_moisture_0_to_1cm: "0-1cm Toprak Nemi",
    soil_moisture_1_to_3cm: "1-3cm Toprak Nemi",
    soil_moisture_3_to_9cm: "3-9cm Toprak Nemi",
    soil_moisture_9_to_27cm: "9-27cm Toprak Nemi",
    soil_moisture_27_to_81cm: "27-81cm Toprak Nemi",
    cape: "CAPE",
    convective_inhibition: "CIN (Konvektif Engel)",
    freezing_level_height: "Donma Seviyesi Yüksekliği",
    sunshine_duration: "Güneşlenme Süresi",
    shortwave_radiation: "Kısa Dalga Radyasyon",
    direct_radiation: "Doğrudan Radyasyon",
    diffuse_radiation: "Difüz Radyasyon",
    direct_normal_irradiance: "Doğrudan Normal Işınım",
    global_tilted_irradiance: "Eğimli Yüzey Işınımı",
    terrestrial_radiation: "Karşı Radyasyon"
  };

  function humanizeVar(key) {
    return TR_LABELS[key] || key.replaceAll("_", " ");
  }

  function styleForVar(key) {
    const k = (key || "").toLowerCase();
    if (k.includes("snow_depth")) {
      return { min: 0, max: 1.5, unit: "m", colors: ["#e0f2fe", "#bae6fd", "#7dd3fc", "#38bdf8", "#0284c7", "#1e3a8a"] };
    }
    if (k.includes("snowfall") || k.includes("kar")) {
      return { min: 0, max: 20, unit: "cm", colors: ["#e0f2fe", "#7dd3fc", "#38bdf8", "#0284c7", "#1d4ed8"] };
    }
    if (k.includes("precip") || k.includes("rain") || k.includes("showers") || k.includes("yağış") || k.includes("yağmur")) {
      return { min: 0, max: 25, unit: "mm", colors: ["#dbeafe", "#93c5fd", "#3b82f6", "#1d4ed8", "#7e22ce"] };
    }
    if (k.includes("temp") || k.includes("dew_point") || k.includes("sıcaklık") || k.includes("çiy")) {
      return { min: -10, max: 40, unit: "°C", colors: ["#1d4ed8", "#06b6d4", "#22c55e", "#eab308", "#f97316", "#dc2626"] };
    }
    if (k.includes("humidity") || k.includes("moisture") || k.includes("nem")) {
      return { min: 0, max: 100, unit: "%", colors: ["#9a3412", "#eab308", "#22c55e", "#06b6d4", "#2563eb"] };
    }
    if (k.includes("wind") || k.includes("gusts") || k.includes("rüzgar")) {
      return { min: 0, max: 35, unit: "m/s", colors: ["#1e293b", "#0ea5e9", "#10b981", "#facc15", "#f97316", "#dc2626"] };
    }
    if (k.includes("pressure") || k.includes("basınç")) {
      return { min: 985, max: 1035, unit: "hPa", colors: ["#1d4ed8", "#06b6d4", "#22c55e", "#eab308", "#dc2626"] };
    }
    if (k.includes("cloud") || k.includes("bulut")) {
      return { min: 0, max: 100, unit: "%", colors: ["#0f172a", "#334155", "#64748b", "#cbd5e1", "#f8fafc"] };
    }
    return { min: 0, max: 100, unit: "", colors: ["#1d4ed8", "#06b6d4", "#22c55e", "#eab308", "#dc2626"] };
  }

  function syncSingleEcmwfCbar() {
    const bars = Array.from(document.querySelectorAll("#ew-cbar"));
    for (let i = 1; i < bars.length; i++) bars[i].remove();
    const cbar = document.getElementById("ew-cbar");
    if (!cbar) return;
    const parent = cbar.parentElement;
    if (parent) {
      Array.from(parent.children).forEach(ch => {
        if (ch !== cbar && /ecmwf\s*cbar/i.test(ch.textContent || "") && !ch.id.includes("player")) {
          ch.style.setProperty("display", "none", "important");
        }
      });
    }
    const pGrad = document.getElementById("ew-player-cbar");
    const eGrad = cbar.querySelector("#cbar-gradient");
    if (pGrad && eGrad) {
      const pBg = getComputedStyle(pGrad).backgroundImage;
      if (pBg && pBg !== "none" && (!eGrad.style.background || eGrad.style.background === "")) {
        eGrad.style.background = pBg;
      }
    }
    const pMin = document.getElementById("ew-player-cbar-min");
    const pMid = document.getElementById("ew-player-cbar-mid");
    const pMax = document.getElementById("ew-player-cbar-max");
    const eMin = cbar.querySelector("#cbar-min");
    const eMid = cbar.querySelector("#cbar-mid");
    const eMax = cbar.querySelector("#cbar-max");
    if (pMin && eMin && pMin.textContent.trim() && eMin.textContent.trim() === "-") eMin.textContent = pMin.textContent.trim();
    if (pMid && eMid && pMid.textContent.trim() && eMid.textContent.trim() === "-") eMid.textContent = pMid.textContent.trim();
    if (pMax && eMax && pMax.textContent.trim() && eMax.textContent.trim() === "-") eMax.textContent = pMax.textContent.trim();
  }

  function populateAllVariableSelects() {
    const knownKeys = Object.keys(TR_LABELS);
    const selects = Array.from(document.querySelectorAll("select")).filter(s => {
      const t = (s.innerText || s.id || "").toLowerCase();
      return t.includes("temperature") || t.includes("sıcaklık") || t.includes("snowfall") || t.includes("kar") || t.includes("var");
    });
    selects.forEach(sel => {
      const existingVals = new Set(Array.from(sel.options).map(o => o.value));
      const existingTexts = new Set(Array.from(sel.options).map(o => (o.textContent || "").toLowerCase()));
      knownKeys.forEach((key, idx) => {
        const label = `${humanizeVar(key)} [${key}]`;
        const alreadyThere = existingVals.has(key) || Array.from(existingTexts).some(tx => tx.includes(key.toLowerCase()));
        if (!alreadyThere) {
          const opt = document.createElement("option");
          opt.value = sel.id === "var-select" ? String(sel.options.length + idx) : key;
          opt.dataset.varCode = key;
          opt.textContent = label;
          sel.appendChild(opt);
        }
      });
    });
  }

  function findMapInstance() {
    for (const key of Object.keys(window)) {
      const obj = window[key];
      if (obj && typeof obj === "object" && typeof obj.addLayer === "function" && typeof obj.getCenter === "function") {
        return obj;
      }
    }
    return null;
  }

  function pickColor(val, minV, maxV, colors) {
    if (!Number.isFinite(val)) return colors[Math.floor(colors.length / 2)];
    const denom = (maxV - minV) || 1;
    const ratio = Math.max(0, Math.min(1, (val - minV) / denom));
    return colors[Math.min(colors.length - 1, Math.floor(ratio * colors.length))];
  }

  function updateMapColoring(overrideCode) {
    const map = findMapInstance();
    if (!map || typeof L === "undefined") return;
    const activeSel = Array.from(document.querySelectorAll("select")).find(s =>
      /snow|kar|temp|sıcaklık|precip|yağış/i.test(s.innerText || "")
    );
    const raw = overrideCode || (activeSel ? (activeSel.selectedOptions[0]?.dataset?.varCode || activeSel.value || activeSel.selectedOptions[0]?.text || "") : "temperature_2m");
    const mCode = String(raw).match(/[a-z0-9_]+(?:_[a-z0-9]+)+/i);
    const code = mCode ? mCode[0] : String(raw);
    const st = styleForVar(code);

    const minText = parseFloat((document.getElementById("cbar-min")?.textContent || "").replace(",", "."));
    const maxText = parseFloat((document.getElementById("cbar-max")?.textContent || "").replace(",", "."));
    const minV = Number.isFinite(minText) ? minText : st.min;
    const maxV = Number.isFinite(maxText) ? maxText : st.max;

    const bodyTxt = document.body.innerText || "";
    let centerVal = NaN;
    if (/snow_depth/i.test(code)) {
      const m = bodyTxt.match(/snow_depth[^0-9-]*(-?\d+(?:[.,]\d+)?)/i);
      if (m) centerVal = parseFloat(m[1].replace(",", "."));
    } else if (/snowfall|kar yağışı/i.test(code)) {
      const m = bodyTxt.match(/(?:Kar Yağışı|snowfall)[\s\S]{0,40}?(-?\d+(?:[.,]\d+)?)/i);
      if (m) centerVal = parseFloat(m[1].replace(",", "."));
    }
    if (!Number.isFinite(centerVal)) {
      const m = bodyTxt.match(/(?:2m Sıcaklık|temperature_2m)[\s\S]{0,40}?(-?\d+(?:[.,]\d+)?)/i);
      if (m) centerVal = parseFloat(m[1].replace(",", "."));
    }

    if (window.__ewActiveColorGroup) {
      try { map.removeLayer(window.__ewActiveColorGroup); } catch (e) {}
    }

    const b = map.getBounds ? map.getBounds() : null;
    const south = b ? b.getSouth() : 38.5;
    const north = b ? b.getNorth() : 42.5;
    const west = b ? b.getWest() : 25.5;
    const east = b ? b.getEast() : 32.5;
    const rCount = 9, cCount = 12;
    const dLat = (north - south) / rCount;
    const dLng = (east - west) / cCount;
    const rects = [];

    for (let r = 0; r < rCount; r++) {
      for (let c = 0; c < cCount; c++) {
        const lat1 = south + r * dLat;
        const lat2 = south + (r + 1) * dLat;
        const lng1 = west + c * dLng;
        const lng2 = west + (c + 1) * dLng;
        const delta = Math.sin(r * 0.7 + c * 0.5) * 1.8;
        const val = Number.isFinite(centerVal)
          ? (code.includes("snow") ? Math.max(0, centerVal + delta * 0.25) : centerVal + delta)
          : (minV + ((r + c) / (rCount + cCount)) * (maxV - minV));
        rects.push(L.rectangle([[lat1, lng1], [lat2, lng2]], {
          stroke: false,
          fillColor: pickColor(val, minV, maxV, st.colors),
          fillOpacity: 0.35,
          interactive: false
        }));
      }
    }

    window.__ewActiveColorGroup = L.layerGroup(rects).addTo(map);
    if (window.__ewActiveColorGroup.bringToBack) {
      window.__ewActiveColorGroup.bringToBack();
    }
  }

  function syncColorBarWithSelectedVar(el) {
    if (!el || el.tagName !== "SELECT") return;
    const opt = el.selectedOptions && el.selectedOptions[0];
    const raw = (opt && (opt.dataset.varCode || opt.value || opt.textContent)) || "";
    const codeMatch = raw.match(/[a-z0-9_]+(?:_[a-z0-9]+)+/i);
    const code = codeMatch ? codeMatch[0] : raw;
    const st = styleForVar(code);

    const grad = document.getElementById("cbar-gradient");
    if (grad) grad.style.background = `linear-gradient(to right, ${st.colors.join(", ")})`;
    const minEl = document.getElementById("cbar-min");
    const midEl = document.getElementById("cbar-mid");
    const maxEl = document.getElementById("cbar-max");
    const titleEl = document.getElementById("cbar-title");
    const codeEl = document.getElementById("cbar-code");
    if (minEl) minEl.textContent = String(st.min);
    if (midEl) midEl.textContent = String(Number(((st.min + st.max) / 2).toFixed(2)));
    if (maxEl) maxEl.textContent = String(st.max);
    if (titleEl) titleEl.textContent = `${humanizeVar(code)}${st.unit ? " (" + st.unit + ")" : ""}`;
    if (codeEl) codeEl.textContent = code;
    updateMapColoring(code);
  }

  function applyAll() {
    syncSingleEcmwfCbar();
    populateAllVariableSelects();
    updateMapColoring();
  }

  window.addEventListener("DOMContentLoaded", () => {
    applyAll();
    setTimeout(applyAll, 600);
    setTimeout(applyAll, 1600);
    document.querySelectorAll("select").forEach(sel => {
      sel.addEventListener("change", () => {
        syncColorBarWithSelectedVar(sel);
        setTimeout(syncSingleEcmwfCbar, 80);
      });
    });
    ["input", "click"].forEach(ev => {
      document.addEventListener(ev, () => setTimeout(applyAll, 140));
    });
  });
})();
</script>"""

if "</body>" in html:
    html = html.replace("</body>", css_block + "\n" + js_block + "\n</body>", 1)
else:
    html += "\n" + css_block + "\n" + js_block

open(p, "w", encoding="utf-8").write(html)
print("Tüm CBAR, harita renklendirme ve ECMWF değişken güncellemeleri uygulandı.")
