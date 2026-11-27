import re

p = "index.html"
html = open(p, encoding="utf-8").read()

for tag_id in [
    "ew-single-cbar-fix", "ew-cbar-format-sync", "ew-cbar-format-sync-js",
    "ew-cbar-keep-pos-css", "ew-cbar-keep-pos-js",
    "ew-ecmwf-cbar-only-css", "ew-ecmwf-cbar-only-js",
    "ew-real-cbar-css", "ew-real-cbar-js"
]:
    html = re.sub(rf'<(?:style|script)[^>]*id="{tag_id}"[^>]*>.*?</(?:style|script)>', '', html, flags=re.DOTALL | re.IGNORECASE)

style_block = """<style id="ew-real-cbar-css">
  #ew-cbar ~ #ew-cbar,
  .ew-ecmwf-cbar-muted ~ .ew-ecmwf-cbar-muted {
    display: none !important;
  }
</style>"""

script_block = """<script id="ew-real-cbar-js">
(function () {
  function syncEcmwfToPlayerCbar() {
    const ecmwfBars = Array.from(document.querySelectorAll('#ew-cbar'));
    if (ecmwfBars.length > 1) {
      for (let i = 1; i < ecmwfBars.length; i++) {
        ecmwfBars[i].style.setProperty('display', 'none', 'important');
      }
    }

    const ecmwfCbar = ecmwfBars[0];
    const playerWrap = document.getElementById('ew-player-cbar-wrap') || document.getElementById('ew-player-cbar');
    if (!ecmwfCbar || !playerWrap) return;

    // Oynatici CBAR stil ve tipografi ozelliklerini #ew-cbar uzerine uygula
    const pStyle = window.getComputedStyle(playerWrap);
    const props = [
      'background', 'background-color', 'background-image',
      'border', 'border-color', 'border-radius',
      'color', 'font-family', 'font-size', 'font-weight',
      'letter-spacing', 'box-shadow'
    ];
    for (const prop of props) {
      const val = pStyle.getPropertyValue(prop);
      if (val) {
        ecmwfCbar.style.setProperty(prop, val, 'important');
      }
    }

    // Oynatici bar icindeki gradyan ve etiket bicimini bul
    const playerGradEl = playerWrap.querySelector('[id*="grad"], [class*="grad"], [id*="scale"], [class*="scale"], [style*="linear-gradient"]');
    const ecmwfGradEl = ecmwfCbar.querySelector('#cbar-gradient');
    if (playerGradEl && ecmwfGradEl) {
      const gStyle = window.getComputedStyle(playerGradEl);
      if (gStyle.backgroundImage && gStyle.backgroundImage !== 'none') {
        ecmwfGradEl.style.setProperty('background-image', gStyle.backgroundImage, 'important');
      }
      if (gStyle.height) {
        ecmwfGradEl.style.setProperty('height', gStyle.height, 'important');
      }
      if (gStyle.borderRadius) {
        ecmwfGradEl.style.setProperty('border-radius', gStyle.borderRadius, 'important');
      }
    }

    // Oynatici bar etiket rakamlarini ve yazi bicimini esitle
    const playerLabelEls = Array.from(playerWrap.querySelectorAll('span, div, label')).filter(el => {
      const t = (el.textContent || '').trim();
      return t.length > 0 && el.children.length === 0;
    });
    const playerNums = (playerWrap.textContent || '').match(/-?\\d+(?:[.,]\\d+)?/g) || [];

    const ecmwfLabelEls = Array.from(ecmwfCbar.querySelectorAll('#cbar-min, #cbar-mid, #cbar-max, .cbar-labels span, .cbar-title, .cbar-code'));
    if (playerLabelEls.length > 0) {
      const refStyle = window.getComputedStyle(playerLabelEls[0]);
      ecmwfLabelEls.forEach((el, idx) => {
        el.style.setProperty('color', refStyle.color, 'important');
        el.style.setProperty('font-family', refStyle.fontFamily, 'important');
        el.style.setProperty('font-size', refStyle.fontSize, 'important');
        el.style.setProperty('font-weight', refStyle.fontWeight, 'important');
        if (el.id === 'cbar-min' || el.id === 'cbar-mid' || el.id === 'cbar-max') {
          if (playerNums.length >= 3 && el.id === 'cbar-min') el.textContent = playerNums[0];
          if (playerNums.length >= 3 && el.id === 'cbar-mid') el.textContent = playerNums[Math.floor(playerNums.length / 2)];
          if (playerNums.length >= 3 && el.id === 'cbar-max') el.textContent = playerNums[playerNums.length - 1];
        }
        if (el.id === 'cbar-title' && !/ecmwf\s*cbar/i.test(el.textContent || '')) {
          el.textContent = (el.textContent || '').trim() + ' — ECMWF CBAR';
        }
      });
    }

    if (!/ecmwf\s*cbar/i.test(ecmwfCbar.textContent || '')) {
      const badge = document.createElement('div');
      badge.textContent = 'ECMWF CBAR';
      badge.style.fontSize = '11px';
      badge.style.fontWeight = '700';
      badge.style.marginTop = '4px';
      ecmwfCbar.appendChild(badge);
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    syncEcmwfToPlayerCbar();
    setTimeout(syncEcmwfToPlayerCbar, 600);
    setTimeout(syncEcmwfToPlayerCbar, 1600);
  });
})();
</script>"""

if "</body>" in html:
    html = html.replace("</body>", style_block + "\n" + script_block + "\n</body>", 1)
else:
    html += "\n" + style_block + "\n" + script_block

open(p, "w", encoding="utf-8").write(html)
print("Gerçek #ew-cbar ve #ew-player-cbar-wrap yapısına göre tekil ve biçim eşitlendi.")
