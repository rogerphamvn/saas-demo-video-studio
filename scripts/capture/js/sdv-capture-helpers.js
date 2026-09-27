// sdv-capture-helpers.js - inject ONCE per page load (after the sdv-clean block) with the browser tool's javascript_tool.
// STATUS: SMOKE-TESTED - the 27/09 ProfitBase v3 helpers, run for real in capture shifts 1-3. Changed here: the case-specific
//   pre-fill function (fixed field labels + values) became the generic __sdvFillByLabels(map, expandText) - values now come
//   from project.json capture.prefill. Whole file re-run here on a synthetic page (headless Chromium), see scripts/README.md.
// Every logging helper returns ONE capture-log line (JSON string) -> the agent appends it to footage/capture-log.jsonl AT ONCE.
// Selectors: text= / aria= / role=button:Name / CSS; fallback_text when the selector breaks. Never call helpers in parallel
// (no Promise.all): one line per call keeps the log ordered.
(() => {
  // SVG elements (chart axis labels) have no innerText/offsetParent -> textContent + getClientRects for SVG.
  const txt = (e) => ((e.innerText ?? e.textContent) || e.getAttribute('aria-label') || '').trim();
  const vis = (e) => e.offsetParent || (e instanceof SVGElement && e.getClientRects().length > 0);
  const byText = (t) => { const m = [...document.querySelectorAll('body *')].filter((e) => vis(e) && txt(e).includes(t));
    return m.find((e) => ![...e.children].some((c) => m.includes(c))) || null; };
  const find = (s) => { if (!s) return null;
    if (s.startsWith('text=')) return byText(s.slice(5));
    if (s.startsWith('aria=')) return document.querySelector(`[aria-label="${s.slice(5)}"]`);
    if (s.startsWith('testid=')) return document.querySelector(`[data-testid="${s.slice(7)}"]`);
    if (s.startsWith('role=')) { const [r, n] = s.slice(5).split(':');
      return [...document.querySelectorAll(`[role="${r}"],${r}`)].find((e) => !n || txt(e).includes(n)) || null; }
    try { return document.querySelector(s); } catch (e) { return null; } };
  const line = (o, el, used) => { const r = el ? el.getBoundingClientRect() : null;
    return JSON.stringify({ ...o, t_epoch: Date.now() / 1000, selector_used: used,
      bbox: r ? { x: r.x, y: r.y, w: r.width, h: r.height } : null, viewport: { w: innerWidth, h: innerHeight },
      dpr: devicePixelRatio, scrollY, zoom: window.__sdvZ || 1, ...(el ? {} : { error: 'not found' }) }); };
  const get = (sel, fb) => { let el = find(sel), used = sel; if (!el && fb) { el = byText(fb); used = 'text=' + fb; } return [el, used]; };
  // log 1 selector (action "measure", or right BEFORE a click/type)
  window.__sdvLog = (shot, step, action, sel, fb) => { const [el, used] = get(sel, fb); return line({ shot, step, action, selector: sel }, el, used); };
  // SOURCE zoom = CSS transform on document.body (a transform on #root does NOT scale portal dialogs/popovers - measured
  // 27/09); Chrome re-rasterises text sharp once still. Level <= 2.0 (lint). Never add will-change:transform (froze WGC capture).
  window.__sdvZoom = (shot, step, sel, level = 1.8, ms = 700, fb) => { const [el, used] = get(sel, fb); if (!el) return line({ shot, step, action: 'zoom', selector: sel, level }, null, used);
    const r = el.getBoundingClientRect(), root = document.body;
    root.style.transformOrigin = `${r.x + r.width / 2}px ${r.y + r.height / 2 + scrollY}px`;
    root.style.transition = `transform ${ms}ms cubic-bezier(.65,0,.35,1)`; root.style.transform = `scale(${level})`; window.__sdvZ = level;
    return line({ shot, step, action: 'zoom', selector: sel, level }, el, used); };
  window.__sdvZoomOut = (shot, step, ms = 700) => { const root = document.body;
    root.style.transition = `transform ${ms}ms cubic-bezier(.65,0,.35,1)`; root.style.transform = ''; window.__sdvZ = 1;
    return JSON.stringify({ shot, step, action: 'zoom_out', t_epoch: Date.now() / 1000 }); };
  // deterministic smooth scroll (page = document.scrollingElement; a self-scrolling dialog = pass its selector)
  window.__sdvScroll = (containerSel, toY, ms = 1200) => new Promise((res) => {
    const el = containerSel ? document.querySelector(containerSel) : document.scrollingElement, y0 = el.scrollTop, t0 = performance.now();
    const e = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    (function f(now) { const p = Math.min(1, (now - t0) / ms); el.scrollTop = y0 + (toY - y0) * e(p);
      p < 1 ? requestAnimationFrame(f) : res({ y: el.scrollTop, t_epoch: Date.now() / 1000 }); })(t0); });
  // set a React-controlled input (native value setter + input/change/blur). On camera, type char by char instead.
  window.__sdvSet = (el, v) => { const p = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(p, 'value').set.call(el, v); ['input', 'change', 'blur'].forEach((t) => el.dispatchEvent(new Event(t, { bubbles: true }))); };
  // input found by its LABEL text (walks up to 5 parents from the label looking for an <input>) - forms without name=
  window.__sdvField = (label) => { const lab = byText(label); let n = lab, inp = null;
    for (let k = 0; k < 5 && n && !inp; k++) { n = n.parentElement; inp = n && n.querySelector('input'); } return inp; };
  // OFF-CAMERA pre-fill: set many fields by label. map = {"Label": "value", ...} (from project.json capture.prefill.labels);
  // expandText = text of a collapsed section header to click first if its fields are not rendered yet (capture.prefill.expand).
  // Measured 27/09: the first call opened the section and set 11/13, the second call set 13/13 -> CALL TWICE, go on only
  // when it returns ok:true.
  window.__sdvFillByLabels = (map, expandText, probeLabel) => { const set = (l, v) => { const i = __sdvField(l); if (i) __sdvSet(i, String(v)); return !!i; };
    if (expandText) { const c = byText(expandText); if (c && !(probeLabel && byText(probeLabel))) c.click(); }
    const r = Object.entries(map).map(([l, v]) => set(l, v));
    return JSON.stringify({ ok: r.every(Boolean), set: r.filter(Boolean).length, of: r.length }); };
  return 'sdv-capture-helpers on';
})()
