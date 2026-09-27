// sdv-clean.template.js - privacy + UI clean-up AT THE SOURCE for screen capture, driven by a config object.
// STATUS: SMOKE-TESTED - rewritten from the 27/09 ProfitBase sdv-clean v3.1 (which had the app's selectors, account greeting
//   and old item names baked in). Every rule kind of v3.1 is kept, but the values now come from project.json "privacy".
//   Re-run here on a synthetic page in headless Chromium (capture/tests/test_clean_js.py); NOT yet run on a real app.
// Build the paste-ready block:  python scripts/capture/clean_js.py --config project.json --out footage/sdv-clean.js
// Paste the WHOLE block into javascript_tool after EVERY new tab / hard reload (SPA route changes are re-applied by the
// MutationObserver). Display-only: no DB write, no localStorage change. Undo: window.__sdvClean.off()
// Verify after injecting (P11): get_page_text on every route must not contain the account email/name, admin labels,
// AI vendor/model names or old item names. React may split one sentence into several text nodes (27/09: the greeting
// "Good evening, <account>!" was 5 nodes) -> rule `split_text` replaces the node AFTER a matching node.
(() => {
  const CFG = /*SDV_CFG*/{}/*END_SDV_CFG*/;
  if (window.__sdvClean) window.__sdvClean.off();
  const RX = (s, f) => (s ? new RegExp(s, (f || '').replace('g', '')) : null);   // no 'g': .test() must stay stateless
  const label = CFG.label || 'Demo';
  const esc = (s) => String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  let css = '*{scrollbar-width:none!important} *::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}\n';
  (CFG.hide_visibility || []).forEach((s) => { css += `${s}{visibility:hidden!important}\n`; });   // keep layout (floating buttons, toasts)
  (CFG.hide_selectors || []).forEach((s) => { css += `${s}{display:none!important}\n`; });        // remove (admin menu items, forbidden pages)
  (CFG.mask_selectors || []).forEach((m) => {                                                        // hide children, draw a label instead
    const s = typeof m === 'string' ? m : m.selector, t = (typeof m === 'string' ? null : m.label) || label;
    css += `${s} > *{visibility:hidden!important} ${s}{position:relative!important}\n` +
      `${s}::after{content:"${esc(t)}";visibility:visible;position:absolute;left:16px;top:50%;transform:translateY(-50%);font:600 14px/1.2 inherit;color:inherit}\n`; });
  css += (CFG.css || []).join('\n') + '\n[data-sdv-hide]{display:none!important}\n[data-sdv-blank]{visibility:hidden!important}';
  const st = document.createElement('style'); st.id = 'sdv-clean'; st.textContent = css; document.head.appendChild(st);

  const OLD = RX(CFG.old_names_re, 'i');            // names of old/real records that must not appear
  const KEEP = RX(CFG.keep_re);                      // ...unless the text also matches the demo marker (e.g. "Demo ·")
  const isOld = (t) => OLD && OLD.test(t || '') && !(KEEP && KEEP.test(t || ''));
  const leaves = (root, re) => (root ? [...root.querySelectorAll('*')].filter((e) => e.children.length === 0 && re.test(e.textContent || '')) : []);
  const q1 = (s) => (s ? document.querySelector(s) : document);
  const EMAIL = /[\w.+-]+@[\w-]+\.[\w.]+/g;
  const onRoute = (r) => !r.path_prefix || location.pathname.startsWith(r.path_prefix);

  const apply = () => {
    // 1. groups hidden by a leaf label (e.g. an "ADMIN DASHBOARD" sidebar group: hide the whole group)
    (CFG.hide_groups || []).forEach((g) => leaves(q1(g.root), RX(g.leaf_re, g.flags)).forEach((e) => {
      const n = (g.closest && e.closest(g.closest)) || e.parentElement; if (n) n.setAttribute('data-sdv-hide', '1'); }));
    // 2. leaves hidden by their text (badges like NEW, dev notes)
    (CFG.hide_leaf_text || []).forEach((re) => leaves(document, RX(re)).forEach((e) => e.setAttribute('data-sdv-hide', '1')));
    // 3. text replaced inside leaves (e.g. drop an AI vendor/model suffix); hidden if the pattern survives
    (CFG.replace_text || []).forEach((r) => { const re = RX(r.re, r.flags), reg = new RegExp(r.re, re.flags + 'g');
      leaves(document, re).forEach((e) => {
      if (!e.dataset.sdvTxt) { e.dataset.sdvTxt = '1'; e.textContent = e.textContent.replace(reg, r.with ?? ''); }
      if (r.hide_if_left !== false && re.test(e.textContent)) e.setAttribute('data-sdv-hide', '1'); }); });
    // 4. any e-mail address in a leaf -> label (outside the masked selectors, which already show the label)
    if (CFG.replace_emails !== false) leaves(document, /@[a-z0-9.-]+\.[a-z]{2,}/i).forEach((e) => {
      if (!(CFG.mask_selectors || []).some((m) => e.closest(typeof m === 'string' ? m : m.selector))) e.textContent = e.textContent.replace(EMAIL, label); });
    // 5. split text nodes: in containers whose text starts with `starts_re`, the text node AFTER the node matching `after_re`
    //    is replaced by the label (a greeting "Hi, " + "<account name>" + "!" rendered as separate nodes)
    (CFG.split_text || []).forEach((r) => document.querySelectorAll(r.container || 'h1,h2,h3,p').forEach((h) => {
      if (!RX(r.starts_re).test(h.textContent || '')) return;
      const t = [...h.childNodes].filter((n) => n.nodeType === 3), k = t.findIndex((n) => RX(r.after_re || ',\\s*$').test(n.nodeValue));
      const rep = r.with || label, stop = RX(r.stop_re || '^\\s*!');
      if (k >= 0 && t[k + 1] && t[k + 1].nodeValue !== rep && !stop.test(t[k + 1].nodeValue)) t[k + 1].nodeValue = rep; }));
    // 6. rows that mention an OLD name are hidden (e.g. "today's tips" rows about old records)
    (CFG.old_rows || []).forEach((r) => leaves(q1(r.root), RX(r.leaf_re)).forEach((e) => { if (isOld(e.textContent)) {
      const row = (r.closest && e.closest(r.closest)) || e.parentElement?.parentElement || e.parentElement; row.setAttribute('data-sdv-hide', '1'); } }));
    // 7. chart labels (SVG text) with an OLD name are blanked, the bar/column itself stays
    if (CFG.svg_blank_old !== false && OLD) document.querySelectorAll('svg text, svg tspan').forEach((t) => {
      if (isOld(t.textContent)) t.setAttribute('data-sdv-blank', '1'); });
    // 8. route-scoped rules
    (CFG.routes || []).filter(onRoute).forEach((r) => {
      if (r.hide_rows) document.querySelectorAll(r.hide_rows.selector).forEach((tr) => {
        if (!RX(r.hide_rows.keep_re).test(tr.innerText || tr.textContent || '')) tr.setAttribute('data-sdv-hide', '1'); });
      if (r.hide_blocks) leaves(q1(r.hide_blocks.root || 'main'), RX(r.hide_blocks.leaf_re)).forEach((e) => {
        let n = e; const cre = RX(r.hide_blocks.container_class_re);
        while (n.parentElement && !cre.test(n.parentElement.className || '')) n = n.parentElement;
        if (n.parentElement) n.setAttribute('data-sdv-hide', '1'); });
    });
  };
  // 9. dropdown options (route-scoped, NOT debounced: runs in the observer microtask before paint so no frame leaks).
  //    Only listboxes whose trigger (aria-controls = listbox id, or an open combobox) matches trigger_text_re [inside a dialog].
  const hideOptions = () => (CFG.routes || []).filter((r) => r.listbox && onRoute(r)).forEach((r) => {
    const L = r.listbox, TR = RX(L.trigger_text_re), KP = RX(L.keep_re);
    document.querySelectorAll('[role="listbox"]').forEach((lb) => {
      // window.CSS: a local variable named CSS once shadowed it and CSS.escape threw inside the observer (27/09)
      const trg = (lb.id && document.querySelector(`[aria-controls="${window.CSS.escape(lb.id)}"]`))
        || document.querySelector((L.in_dialog ? '[role="dialog"] ' : '') + '[role="combobox"][aria-expanded="true"]');
      if (!trg || (L.in_dialog && !trg.closest('[role="dialog"]')) || (TR && !TR.test(trg.textContent || ''))) return;
      lb.querySelectorAll('[role="option"]').forEach((o) => { if (!KP.test(o.textContent || '')) o.setAttribute('data-sdv-hide', '1'); });
    }); });
  apply(); hideOptions();
  const mo = new MutationObserver(() => { hideOptions(); clearTimeout(window.__sdvT); window.__sdvT = setTimeout(apply, 120); });
  mo.observe(document.body, { childList: true, subtree: true, characterData: true });
  window.__sdvClean = { apply, cfg: CFG, off() { mo.disconnect(); st.remove();
    document.querySelectorAll('[data-sdv-hide],[data-sdv-blank]').forEach((e) => { e.removeAttribute('data-sdv-hide'); e.removeAttribute('data-sdv-blank'); }); } };
  return 'sdv-clean on';
})()
