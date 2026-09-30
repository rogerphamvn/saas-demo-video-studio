/* lib/engine.js - shared motion engine (window.HF contract) for the SaaS demo video studio.
   HyperFrames 0.8.x + GSAP 3, DETERMINISTIC: no Math.random, no onUpdate/onComplete callbacks, no runtime text writes (all text is
   written into the DOM ONCE at build time, before the timeline plays), no filter:blur, no CSS transitions, no bouncy eases
   (back/elastic/bounce) - see .claude/skills/saas-demo-video-studio/references/taste-and-banlist.md.
   Scene builders (scenes/eXX.js) only CALL these helpers + add their own tweens on HF.tl; they never edit this file,
   index.html, tokens.css or grid.js (1 writer per file). Every time comes from the grid (HF.bar / HF.beat) or a VO word (HF.W) -
   never a hand-typed second.
   ORIGIN: snapshot of the engine used for the ProfitBase v3 case (27-28/09/2026), taken DURING the v3.1 motion pass.
   The v3.1 motion pass was NOT finalised: v3 was rejected in the case and the approved look stayed v5. The maintained upgrade line is
   lib/v6-kit.js (v6 = approved cut + upgrades on top). This chapter-tour engine stays as an alternative layout: a SNAPSHOT, not re-synced.
   Project-specific values come from window.ENGINE_CFG (data/engine-cfg.js), never from this file:
     { keepCrop: ["e04", ...],       // clips whose crop is a RULE (privacy / label conflict) -> 9:16 keeps the crop instead of the full frame
       emphasis: ["lãi", "lỗ", ...], // caption words drawn in the accent colour
       stripLabel: "BY THE NUMBERS", // header of HF.strip()
       showCounter: true }           // "03 / 13" counter above chapter titles
*/
window.HF_ENGINE = function (tl, G, CAPS) {
  const $ = (s, r) => (typeof s === "string" ? (r || document).querySelector(s) : s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const BAR = G.bar_s, BEAT = G.beat_s;
  // 9:16 variant (project hf-v3-9x16, html.p916): app window fixed 1040x547 @ (20,365), camera 1.0 (whole 1920x1010 capture) except
  // clips whose crop is a RULE (label conflict, old records, modal backdrop, currency labels) come from ENGINE_CFG.keepCrop
  const P916 = document.documentElement.classList.contains("p916");
  const CFG = Object.assign({ keepCrop: [], emphasis: [], stripLabel: "BY THE NUMBERS", showCounter: true }, window.ENGINE_CFG || {});
  const KEEP_CROP = new Set(CFG.keepCrop);
  let stripN = 0;
  const bar = (n) => G.t0 + n * BAR;                       // downbeat of grid bar n (fractional allowed)
  const beat = (n) => n * BEAT;                            // duration of n beats
  const CH = {};
  G.chapters.forEach((c, i) => { CH["e" + String(i + 1).padStart(2, "0")] = Object.assign({ n: i + 1, key: "e" + String(i + 1).padStart(2, "0") }, c); });
  const HERO = (window.HERO = {});
  const WAIT = (window.WAIT_SLOTS = []);                   // every [CHỜ ĐO] placeholder registers here (report + stills sheet)
  const TODO_BBOX = (window.TODO_BBOX = []);
  const FOOT = (window.FOOT = {});
  const CARDS = (window.CARDS = []);                       // card rect per chapter (motion layer reads it)
  const FXL = (window.FX_LOG = []);                        // every FX/TX call {type, t} -> density check + SFX suggestions
  const FXLOG = (type, t, extra) => FXL.push(Object.assign({ type, t: +(+t).toFixed(3) }, extra || {}));                          // slot -> clip mapping (for map())
  // capture-log bbox (CSS px of the 1920x1010 viewport = clip px) -> frame px, for a slot with footage
  function map(slotKey, x, y) {
    const f = FOOT[slotKey];
    if (!f) throw new Error("HF.map: no footage in slot " + slotKey);
    return [f.ox + (x - f.vx) * f.sc, f.oy + (y - f.vy) * f.sc];
  }               // every target that must come from capture-log bbox

  // ---- VO word time (video seconds). W("chín", "E04") ; k-th occurrence (1-based) ----
  const clean = (w) => w.toLowerCase().normalize("NFC").replace(/[^\p{L}\p{N}]/gu, "");
  function W(word, line, k = 1) {
    const hits = CAPS.words.filter((w) => w[3] === line && clean(w[0]) === clean(word));
    if (hits.length < k) throw new Error(`HF.W: word "${word}" #${k} not in ${line}`);
    return hits[k - 1][1];
  }
  const WE = (word, line, k = 1) => {
    const hits = CAPS.words.filter((w) => w[3] === line && clean(w[0]) === clean(word));
    if (hits.length < k) throw new Error(`HF.WE: word "${word}" #${k} not in ${line}`);
    return hits[k - 1][2];
  };

  function el(tag, cls, html, parent, style) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;                  // build time only
    if (style) Object.assign(e.style, style);
    if (parent) $(parent).append(e);
    return e;
  }
  const hide0 = (e) => gsap.set(e, { autoAlpha: 0 });   // immediate (lint gsap_timeline_set_initial_hide)
  const win = (e, a, b) => { hide0(e); tl.set(e, { autoAlpha: 1 }, a); if (b != null) tl.set(e, { autoAlpha: 0 }, b); };

  // ---- chapter title: "0X / NN" + 2 lines (Inter 900 + Plex Serif italic violet), m7 clip-mask entry 1 beat after the downbeat ----
  const words = (txt) => txt.split(" ").map((w) => `<span class="w"><span class="wi">${w}</span></span>`).join(" ");
  // v3.1 kinetic title: words rise through a mask with a 6deg skew, the 2 lines staggered, italic line gets a drawn violet underline, counter flips
  function title(C, l1, l2, o = {}) {
    const size = P916 ? (o.size || 76) : (o.size ? Math.round(o.size * 0.8) : 60);
    const t = el("div", "ttl" + (o.dark ? " dark" : ""), null, "#titles");
    t.id = "ttl-" + C.key;
    t.dataset.chapter = C.id;
    t.innerHTML = `<div class="ln"><span class="cnt">${CFG.showCounter ? String(C.n).padStart(2, "0") + " / " + String(G.chapters.length).padStart(2, "0") : ""}</span></div>` +
      `<div class="ln"><span class="t1" style="font-size:${size}px">${words(l1)}</span></div>` +
      `<div class="ln"><span class="t2" style="font-size:${size}px">${words(l2)}<i class="ul"></i></span></div>`;
    const tin = o.t != null ? o.t : C.t_in + beat(1);
    const tout = o.tout != null ? o.tout : C.t_out;
    hide0(t);
    tl.set(t, { autoAlpha: 1 }, tin);
    gsap.set($(".cnt", t), { transformPerspective: 500 });
    tl.fromTo($(".cnt", t), { rotationX: 90 }, { rotationX: 0, duration: 0.4, ease: "expo.out" }, tin);
    tl.fromTo($$(".t1 .wi", t), { yPercent: 115, skewY: 6 }, { yPercent: 0, skewY: 0, duration: 0.55, ease: "expo.out", stagger: 0.06 }, tin + 0.05);
    tl.fromTo($$(".t2 .wi", t), { yPercent: 115, skewY: 6 }, { yPercent: 0, skewY: 0, duration: 0.55, ease: "expo.out", stagger: 0.06 }, tin + 0.2);
    tl.fromTo($(".ul", t), { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: "power3.out" }, tin + 0.5);
    FXLOG("title-kinetic", tin);
    if (o.keep) return t;
    if (o.cutOut) tl.set(t, { autoAlpha: 0 }, tout);
    else {
      tl.to($$(".wi", t), { yPercent: -115, duration: 0.3, ease: "power2.in", stagger: 0.02 }, tout - 0.42);
      tl.set(t, { autoAlpha: 0 }, tout);
    }
    return t;
  }

  // ---- the UI card (m6 morph one-take; hard cut only where the storyboard allows) ----
  let cardRect = null;
  function card(C, r, o = {}) {
    const t = o.t != null ? o.t : C.t_in;
    if (P916) r = { x: 20, y: 365, w: 1040, h: 547, r: 28 };
    else if (!o.raw) {                                   // v3.1: right-anchored card, width 1060-1160 (>= 55% of 1920), height <= 660
      const asp = r.h / r.w;
      let w = Math.min(1160, Math.max(1060, r.w * 1.3)), h = w * asp;
      if (h > 660) { h = 660; w = h / asp; }
      r = { x: Math.round(1850 - w), y: Math.round(422 - h / 2), w: Math.round(w), h: Math.round(h), r: r.r };
    }
    const v = { left: r.x, top: r.y, width: r.w, height: r.h, borderRadius: r.r != null ? r.r : 22 };
    if (!cardRect) gsap.set("#card", v);
    else if (o.cut) tl.set("#card", v, t);
    else tl.to("#card", Object.assign({ duration: 0.6, ease: "power3.inOut" }, v), t - 0.3);
    cardRect = Object.assign({}, r);
    CARDS.push({ key: C.key, t, cut: !!o.cut, r: cardRect });
    return r;
  }

  // ---- FOOTAGE SLOT: grey panel labelled with the capture-script shot id; later: put <video> into .vwrap (same box, same timing) ----
  function slot(C, shot, o = {}) {
    const s = el("div", "slot", null, "#card");
    s.id = "slot-" + C.key + (o.suffix || "");
    s.dataset.shot = shot;
    s.dataset.chapter = C.id;
    const a = o.tIn != null ? o.tIn : C.t_in, b = o.tOut != null ? o.tOut : C.t_out;
    s.dataset.tIn = a.toFixed(3);
    s.dataset.tOut = b.toFixed(3);
    s.innerHTML = `<div class="cam"><div class="vwrap"></div><div class="ph">` +
      `<div class="phk">FOOTAGE SLOT</div><div class="phid">${shot}</div>` +
      `<div class="phs">${C.id} · ô ${C.bar_in}–${C.bar_out} · ${a.toFixed(2)}–${b.toFixed(2)} s${o.url ? " · " + o.url : ""}</div>` +
      (o.note ? `<div class="phn">${o.note}</div>` : "") + `</div></div>`;
    s.dataset.rect = JSON.stringify(cardRect);
    // real footage (data/cuts.json -> static <video id="v-<clip>">): fit the clip's view box into the card, hide the placeholder
    const clipId = o.clip || C.key;
    const cut = window.CUTS && window.CUTS[clipId];
    const v = document.getElementById("v-" + clipId);
    if (cut && v) {
      const [vx, vy, vw, vh] = P916 && !KEEP_CROP.has(clipId) ? [0, 0, 1920, 1010] : cut.view, r = cardRect;
      const sc = Math.min(r.w / vw, r.h / vh);
      const box = el("div", "vbox", null, s.querySelector(".vwrap"),
        { left: ((r.w - vw * sc) / 2).toFixed(1) + "px", top: ((r.h - vh * sc) / 2).toFixed(1) + "px", width: (vw * sc).toFixed(1) + "px", height: (vh * sc).toFixed(1) + "px" });
      box.append(v);
      v.style.transform = `scale(${sc.toFixed(5)}) translate(${-vx}px, ${-vy}px)`;
      s.querySelector(".ph").style.display = "none";
      s.classList.add("has-footage");
      FOOT[C.key + (o.suffix || "")] = { clipId, vx, vy, sc, ox: r.x + (r.w - vw * sc) / 2, oy: r.y + (r.h - vh * sc) / 2, rx: r.x, ry: r.y, slot: s };
    }
    hide0(s);
    tl.set(s, { autoAlpha: 1 }, a);                        // v3.1: instant swap (a fade showed ~0.25 s of empty card); the TX layer covers it
    if (o.fadeOut) tl.to(s, { autoAlpha: 0, duration: 0.2, ease: "power1.in" }, b - 0.2);
    else tl.set(s, { autoAlpha: 0 }, b);
    return s;
  }
  // target marker inside a slot = where a capture-log bbox will go (chip landing, punch focus, highlight)
  function target(s, id, x, y, label) {
    if (s.classList.contains("has-footage")) return null;     // dev marker only while the slot is a placeholder
    const m = el("div", "tgt", `<i></i><span>TODO bbox · ${label}</span>`, $(".cam", s), { left: x + "px", top: y + "px" });
    m.dataset.tgt = id;
    TODO_BBOX.push({ chapter: s.dataset.chapter, shot: s.dataset.shot, id, label, x, y });
    return m;
  }

  // ---- callout card popping from the card edge (B: tooltip-like, number lives here, not across the whole frame) ----
  function callout(r, html, a, b, o = {}) {
    const c = el("div", "callout" + (o.cls ? " " + o.cls : ""), html, "#callouts", { left: r.x + "px", top: r.y + "px", width: r.w + "px" });
    if (r.h) c.style.height = r.h + "px";
    if (o.id) c.id = o.id;
    hide0(c);
    if (!P916) { c.style.left = "60px"; c.style.width = Math.min(r.w, 640) + "px"; c.style.top = Math.max(r.y, 350) + "px"; }
    gsap.set(c, { transformPerspective: 1400, transformOrigin: "100% 50%" });
    tl.fromTo(c, { autoAlpha: 0, x: -60, rotationY: -28, z: -160, scale: 0.9 }, { autoAlpha: 1, x: 0, rotationY: 0, z: 0, scale: 1, duration: 0.55, ease: "expo.out" }, a);
    FXLOG("callout-3d", a);
    if (b != null) tl.to(c, { autoAlpha: 0, rotationY: 18, z: -120, duration: 0.25, ease: "power2.in" }, b - 0.25);
    return c;
  }
  const pill = (txt, cls) => `<span class="pill ${cls || ""}">${txt}</span>`;
  // grey [CHỜ ĐO] placeholder: a number that is NOT measured yet - never invent it
  function wait(label, where) {
    WAIT.push({ where, label });
    return `<span class="wait">[CHỜ ĐO]<small>${label}</small></span>`;
  }

  // ---- odometer (m3): digits are in the markup at build time; only yPercent is tweened. data-num = the settled value ----
  // v3.1 split-flap counter (replaces the odometer, same API). data-num = settled value (check_numbers reads it)
  function odoHTML(from, to) {
    const L = to.length;
    const f = (from == null ? "" : from).padStart(L, " ");
    const up = from == null || +to.replace(/\D/g, "") >= +f.replace(/\D/g, "");
    let h = `<span class="odo num" data-num="${to}">`;
    for (let i = 0; i < L; i++) {
      const b = to[i], a = f[i];
      if (!/\d/.test(b)) { h += `<span class="fl-s">${b}</span>`; continue; }
      let seq;
      if (from == null || a === " ") seq = ["&nbsp;", (+b + 8) % 10, (+b + 9) % 10, +b];
      else seq = up ? rangeUp(+a, +b) : rangeDown(+a, +b);
      if (seq.length > 4) seq = [seq[0]].concat(seq.slice(-3));
      h += `<span class="fl-c" data-n="${seq.length}">${seq.map((d, k) => `<span class="fl-k k${k}">${d}</span>`).join("")}<i class="fl-line"></i></span>`;
    }
    return h + "</span>";
  }
  function rangeUp(a, b) { const r = [a]; let d = a; while (d !== b) { d = (d + 1) % 10; r.push(d); } return r; }
  function rangeDown(a, b) { const r = [a]; let d = a; while (d !== b) { d = (d + 9) % 10; r.push(d); } return r; }
  function odo(host, t, dur = 0.8) {
    const cells = $$(".fl-c", host).reverse();                 // right-most digit leads, 35 ms stagger
    cells.forEach((c, i) => {
      const n = +c.dataset.n, ks = $$(".fl-k", c);
      if (n < 2) return;
      const sd = Math.min(0.16, (dur - 0.1) / (n - 1));
      ks.forEach((k) => gsap.set(k, { transformPerspective: 420 }));
      for (let j = 1; j < n; j++) {
        const tj = t + i * 0.035 + (j - 1) * sd;
        tl.to(ks[j - 1], { rotationX: -90, duration: sd / 2, ease: "power2.in" }, tj);
        tl.set(ks[j - 1], { autoAlpha: 0 }, tj + sd / 2);
        tl.fromTo(ks[j], { autoAlpha: 1, rotationX: 90 }, { rotationX: 0, duration: sd / 2, ease: "power2.out", immediateRender: false }, tj + sd / 2);
      }
    });
    FXLOG("flip-counter", t);
  }

  // ---- giant number (use sparingly: only at the drop moments of the grid) ----
  function giant(html, a, b, o = {}) {
    const g = el("div", "giant " + (o.cls || ""), html, "#giants", o.style || {});
    if (o.id) g.id = o.id;
    g.dataset.t = a;                                     // motion.js flips the giant's digits from here
    hide0(g);
    tl.fromTo(g, { autoAlpha: 0, scale: 1.06 }, { autoAlpha: 1, scale: 1, duration: 0.35, ease: "expo.out" }, a);
    if (b != null && !o.keep) tl.to(g, { autoAlpha: 0, duration: 0.25, ease: "power2.in" }, b - 0.25);
    return g;
  }

  // ---- ambient light behind the card: red-light -> green-light, never a flash ----
  function light(color, a, dur = 0.6, to = 1) {
    tl.to(color === "r" ? "#glowR" : "#glowG", { autoAlpha: to, duration: dur, ease: "power1.inOut" }, a);
  }

  // ---- punch-in (m11) on a slot camera: 1 -> s around a focus point ----
  function punch(s, a, o = {}) {
    const cam = $(".cam", s);
    tl.set(cam, { transformOrigin: `${o.fx || 50}% ${o.fy || 50}%` }, a);
    tl.to(cam, { scale: o.s || 1.4, duration: 0.5, ease: "power4.out" }, a);
    if (o.out != null) tl.to(cam, { scale: 1, duration: 0.35, ease: "power2.inOut" }, o.out);
  }
  // macro -> pull-back (m2): source ZN 1.8x frame -> 1.0 in 1.0 s expo.out (footage: dissolve to 1x capture once <= 1.05 - P12)
  function macro(s, a, o = {}) {
    const cam = $(".cam", s);
    gsap.set(cam, { transformOrigin: `${o.fx || 50}% ${o.fy || 50}%`, scale: o.s || 1.8 });
    tl.to(cam, { scale: 1, duration: 1.0, ease: "expo.out" }, a);
  }

  // ---- hand-drawn curve arrow (m15): SVG stroke-dashoffset 0.5 s power2.out, head appears at the end ----
  function curve(d, a, o = {}) {
    const svg = el("div", "curve", `<svg width="1920" height="1080" viewBox="0 0 1920 1080"><path d="${d}" pathLength="1" class="cv"/>` +
      `<circle class="cvh" cx="${o.hx}" cy="${o.hy}" r="9"/></svg>`, "#callouts");
    hide0(svg);
    tl.set(svg, { autoAlpha: 1 }, a);
    tl.fromTo($(".cv", svg), { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.5, ease: "power2.out" }, a);
    tl.fromTo($(".cvh", svg), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.15 }, a + 0.45);
    if (o.b != null) tl.to(svg, { autoAlpha: 0, duration: 0.25 }, o.b - 0.25);
    return svg;
  }

  // ---- bridge chip (m1): ONE element through the film; moves tween to coordinates in frame px (from capture-log bbox later) ----
  function chipTo(a, x, y, o = {}) {
    const d = o.dur || 0.5;                              // v3.1: the chip crosses in a 3D arc
    tl.to("#chip", Object.assign({ left: x, duration: d, ease: "power1.inOut" }, o.v || {}), a);
    tl.to("#chip", { top: "-=" + (o.arc != null ? o.arc : 110), scale: 1.22, rotationY: 28, duration: d / 2, ease: "power2.out" }, a);
    tl.to("#chip", { top: y, scale: (o.v && o.v.scale) || 1, rotationY: 0, duration: d / 2, ease: "power2.in" }, a + d / 2);
    FXLOG("chip-arc", a);
  }
  function chipShow(a, x, y, o = {}) {
    tl.set("#chip", { left: x, top: y }, a);
    tl.fromTo("#chip", { autoAlpha: 0, scale: 0.9 }, { autoAlpha: 1, scale: 1, rotation: o.rot || 0, duration: 0.3, ease: "power2.out" }, a);
  }
  const chipHide = (a, d = 0.1) => tl.to("#chip", { autoAlpha: 0, duration: d, ease: "power1.in" }, a);
  const chipDot = (a, col) => tl.to("#chip i", { backgroundColor: col, duration: 0.25, ease: "power1.inOut" }, a);

  // ---- "by the numbers" strip (m13): numbers shrink into a row at the bottom of the left column ----
  function strip(items, a, b) {
    const s = el("div", "strip", `<div class="sk">${CFG.stripLabel}</div><div class="sr">` +
      items.map((it) => `<div class="si"><b class="num">${it[0]}</b><small>${it[1]}</small></div>`).join("") + `</div>`, "#titles");
    s.id = "strip-" + ++stripN;
    hide0(s);
    tl.set(s, { autoAlpha: 1 }, a);
    tl.fromTo($$(".si", s), { autoAlpha: 0, y: 24, scale: 1.6 }, { autoAlpha: 1, y: 0, scale: 1, duration: 0.45, ease: "power3.out", stagger: 0.1 }, a);
    if (b != null) tl.to(s, { autoAlpha: 0, duration: 0.25 }, b - 0.25);
    return s;
  }

  // ---- circle opening from the pressed button (m14) ----
  function circleWipe(x, y, a, dur = 0.6) {
    tl.set("#dark", { autoAlpha: 1, clipPath: `circle(0px at ${x}px ${y}px)` }, a);
    tl.to("#dark", { clipPath: `circle(2300px at ${x}px ${y}px)`, duration: dur, ease: "power3.inOut" }, a);
    if (P916) tl.to("#heroslot", { backgroundColor: "#1A1730", duration: 0.4 }, a + 0.2);   // 9:16 hero slot follows the dark theme
  }

  // v3.1 post camera push-in on a capture-log bbox (clip px) of a footage slot, pull-back before b
  function push(key, x, y, a, b, s = 1.3) {
    const f = FOOT[key];
    if (!f || P916) return;
    const cam = f.slot.querySelector(".cam");
    const lx = f.ox - f.rx + (x - f.vx) * f.sc, ly = f.oy - f.ry + (y - f.vy) * f.sc;
    tl.set(cam, { transformOrigin: `${lx.toFixed(1)}px ${ly.toFixed(1)}px` }, a);
    tl.to(cam, { scale: s, duration: 0.6, ease: "power3.out" }, a);
    tl.to(cam, { scale: 1, duration: 0.45, ease: "power2.inOut" }, b - 0.45);
    FXLOG("push-in", a); FXLOG("pull-back", b - 0.45);
  }
  const hero = (C, t) => { HERO[C.id] = +t.toFixed(3); };

  // ---- captions: approved .cap2 (92 px, 2-4-word groups by meaning, always on while VO speaks). Pop = power2/expo, NO back.out ----
  const EMPH = new Set(CFG.emphasis.map((w) => clean(w)));
  function captions() {
    const groups = CAPS.groups;
    groups.forEach((g, k) => {
      const [txt, t0, t1w, line] = g;
      const nxt = groups[k + 1] ? groups[k + 1][1] : t1w + 0.9;
      const t1 = nxt - t1w > 1.4 ? t1w + 0.9 : nxt;
      const words = txt.split(/\s+/).filter((w) => w && w !== "—");
      const e = el("div", "cap2", words.map((w) => `<span class="${EMPH.has(clean(w)) ? "em" : ""}">${w}</span>`).join(""), "#captions");
      e.dataset.line = line;
      e.dataset.t0 = t0; e.dataset.t1 = t1;
      hide0(e);
      const pd = Math.max(0.05, Math.min(0.2, t1 - t0 - 0.03));
      tl.fromTo(e, { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, duration: pd, ease: "power2.out" }, t0);
      tl.set(e, { autoAlpha: 0 }, t1);
    });
  }

  return { tl, G, CAPS, map, FOOT, push, FXLOG, P916, CARDS, $, $$, BAR, BEAT, bar, beat, CH, W, WE, el, win, hide0, title, card, slot, target, callout, pill, wait, odoHTML, odo,
           giant, light, punch, macro, curve, chipTo, chipShow, chipHide, chipDot, strip, circleWipe, hero, captions,
           PAL: { p: "#6952E0", g: "#1FAD53", r: "#DD3C3C", ink: "#16132B", mute: "#8C889D" } };
};
