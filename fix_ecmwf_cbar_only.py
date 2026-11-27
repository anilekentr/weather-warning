import re

p = "index.html"
html = open(p, encoding="utf-8").read()

for tag_id in ["ew-single-cbar-fix", "ew-cbar-format-sync", "ew-cbar-format-sync-js", "ew-cbar-keep-pos-css", "ew-cbar-keep-pos-js", "ew-ecmwf-cbar-only-css", "ew-ecmwf-cbar-only-js"]:
    html = re.sub(rf'<(?:style|script)[^>]*id="{tag_id}"[^>]*>.*?</(?:style|script)>', '', html, flags=re.DOTALL | re.IGNORECASE)

style_block = """<style id="ew-ecmwf-cbar-only-css">
  .ecmwf-cbar-duplicate,
  [data-ew-dup-cbar="1"] {
    display: none !important;
  }
</style>"""

script_block = """<script id="ew-ecmwf-cbar-only-js">
(function () {
  const styleProps = [
    'background', 'background-color', 'background-image',
    'color', 'border', 'border-color', 'border-radius',
    'font-family', 'font-size', 'font-weight', 'letter-spacing',
    'line-height', 'padding', 'box-shadow'
  ];

  function fixEcmwfCbar() {
    const nodes = Array.from(document.querySelectorAll('*')).filter(el => {
      const tag = (el.tagName || '').toLowerCase();
      if (['script', 'style', 'html', 'body', 'head'].includes(tag)) return false;
      const meta = ((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : '') + ' ' + (el.textContent || '')).toLowerCase();
      return meta.includes('cbar');
    });

    const leaves = nodes.filter(el => !nodes.some(other => other !== el && el.contains(other)));
    if (leaves.length === 0) return;

    const playerBar = leaves.find(el => /oynat/i.test(((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : '') + ' ' + (el.textContent || '')))) || leaves[0];
    const ecmwfBars = leaves.filter(el => el !== playerBar && /ecmwf/i.test(((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : '') + ' ' + (el.textContent || ''))));

    if (ecmwfBars.length === 0) return;

    const primaryEcmwf = ecmwfBars[0];
    for (let i = 1; i < ecmwfBars.length; i++) {
      ecmwfBars[i].setAttribute('data-ew-dup-cbar', '1');
      ecmwfBars[i].style.setProperty('display', 'none', 'important');
    }

    if (playerBar) {
      const pStyle = window.getComputedStyle(playerBar);
      for (const prop of styleProps) {
        const val = pStyle.getPropertyValue(prop);
        if (val) {
          primaryEcmwf.style.setProperty(prop, val, 'important');
        }
      }
    }

    const hasLabel = /ecmwf\s*cbar/i.test(primaryEcmwf.textContent || '');
    if (!hasLabel) {
      const span = document.createElement('span');
      span.textContent = ' ECMWF CBAR';
      primaryEcmwf.appendChild(span);
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    fixEcmwfCbar();
    setTimeout(fixEcmwfCbar, 700);
    setTimeout(fixEcmwfCbar, 1800);
  });
})();
</script>"""

if "</body>" in html:
    html = html.replace("</body>", style_block + "\n" + script_block + "\n</body>", 1)
else:
    html += "\n" + style_block + "\n" + script_block

open(p, "w", encoding="utf-8").write(html)
print("4e4e484 tabaninda ECMWF CBAR tekil ve oynatici biciminde ayarlandi.")
