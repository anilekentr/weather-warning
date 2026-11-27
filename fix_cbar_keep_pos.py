import re

p = "index.html"
html = open(p, encoding="utf-8").read()

for tag_id in ["ew-single-cbar-fix", "ew-cbar-format-sync", "ew-cbar-format-sync-js", "ew-cbar-keep-pos-css", "ew-cbar-keep-pos-js"]:
    html = re.sub(rf'<(?:style|script)[^>]*id="{tag_id}"[^>]*>.*?</(?:style|script)>', '', html, flags=re.DOTALL | re.IGNORECASE)

style_block = """<style id="ew-cbar-keep-pos-css">
  [class*="cbar"] ~ [class*="cbar"],
  [id*="cbar"] ~ [id*="cbar"],
  .ecmwf-cbar ~ .ecmwf-cbar {
    display: none !important;
  }
</style>"""

script_block = """<script id="ew-cbar-keep-pos-js">
(function () {
  const posProps = ['position', 'top', 'left', 'right', 'bottom', 'transform', 'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right', 'z-index', 'float'];
  const styleProps = [
    'background', 'background-color', 'background-image',
    'color', 'border', 'border-color', 'border-radius',
    'font-family', 'font-size', 'font-weight', 'letter-spacing',
    'line-height', 'padding', 'box-shadow'
  ];

  function applySingleCbarFormat() {
    const candidates = Array.from(document.querySelectorAll('*')).filter(el => {
      const tag = (el.tagName || '').toLowerCase();
      if (['script', 'style', 'html', 'body', 'head'].includes(tag)) return false;
      const meta = ((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : '') + ' ' + (el.textContent || '')).toLowerCase();
      return meta.includes('cbar');
    });

    if (candidates.length === 0) return;

    const leafCbars = candidates.filter(el => !candidates.some(other => other !== el && el.contains(other)));
    const pool = leafCbars.length > 0 ? leafCbars : candidates;

    const playerBar = pool.find(el => /oynat/i.test(((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : '') + ' ' + (el.textContent || '')))) || pool[0];
    const ecmwfBar = pool.find(el => el !== playerBar && /ecmwf/i.test(((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : '') + ' ' + (el.textContent || '')))) || pool.find(el => el !== playerBar);

    if (!playerBar || !ecmwfBar) return;

    const savedPos = {};
    const eStyleBefore = window.getComputedStyle(ecmwfBar);
    for (const prop of posProps) {
      savedPos[prop] = eStyleBefore.getPropertyValue(prop);
    }

    const pStyle = window.getComputedStyle(playerBar);
    for (const prop of styleProps) {
      const val = pStyle.getPropertyValue(prop);
      if (val) {
        ecmwfBar.style.setProperty(prop, val, 'important');
      }
    }

    const playerNums = (playerBar.textContent || '').match(/-?\d+(?:[.,]\d+)?/g);
    if (playerNums && playerNums.length > 0) {
      const walker = document.createTreeWalker(ecmwfBar, NodeFilter.SHOW_TEXT);
      let idx = 0;
      let node;
      while ((node = walker.nextNode())) {
        if (/-?\d+(?:[.,]\d+)?/.test(node.nodeValue || '')) {
          node.nodeValue = node.nodeValue.replace(/-?\d+(?:[.,]\d+)?/g, () => {
            const val = playerNums[idx % playerNums.length];
            idx += 1;
            return val;
          });
        }
      }
    }

    for (const prop of posProps) {
      if (savedPos[prop]) {
        ecmwfBar.style.setProperty(prop, savedPos[prop], 'important');
      }
    }

    for (const item of pool) {
      if (item !== playerBar && item !== ecmwfBar) {
        item.style.setProperty('display', 'none', 'important');
      }
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    applySingleCbarFormat();
    setTimeout(applySingleCbarFormat, 600);
    setTimeout(applySingleCbarFormat, 1800);
  });
})();
</script>"""

if "</body>" in html:
    html = html.replace("</body>", style_block + "\n" + script_block + "\n</body>", 1)
else:
    html += "\n" + style_block + "\n" + script_block

open(p, "w", encoding="utf-8").write(html)
print("Konum korunarak tek CBAR ve oynatici bicimi uygulandi.")
