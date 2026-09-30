/* lib/v6-kit.js - v6 upgrade layer, GENERIC (no product text, no product numbers).
   ORIGIN: generalised from the ProfitBase v6 case (30/09/2026): v6 = the approved v5 cut + upgrades ON TOP (12 beat-locked 3D
   transitions, split-flap numbers, glass blocks, bloom/burst, tilt drift, parallax). The case-specific blocks (hook, dots+gauge,
   before/after, KPI strip, bento) are NOT shipped - build yours with the helpers below.
   STATUS: the case version was RENDERED (16:9) in the real case. THIS generalised file is SMOKE-TESTED AT BEST (node --check +
   see engine/README "Trang thai kiem chung"); it has not rendered a full video by itself.

   Rule it encodes (LESSON-16): once a cut is approved, keep its look and add upgrades that can be switched off - never restyle.

   Deterministic, like the rest of the engine: fixed values only (no Math.random), no per-frame callbacks, no runtime text writes
   (all markup is built once here, before the timeline plays), no blur filter, no CSS transition. Uses GSAP 3 on a paused timeline.

   Usage (index.html, AFTER your scenes are built and BEFORE the captions, so captions stay on top):
     <link rel="stylesheet" href="lib/v6.css">
     <div id="v6fx" class="layer" data-layout-allow-overlap data-layout-allow-overflow></div>   <!-- above b-roll, below captions -->
     <script src="lib/v6-kit.js"></script>
     const V6 = window.V6_KIT({ tl, $, $$, beat0, beatLen, duration, host: $("#v6fx") });
     V6.transitions([{ type: "flip", out: "#sc01", in: "#sc02", beat: 14, name: "sc01>sc02" }, ...]);

   ctx contract (build it from your own engine object; for engine/lib/engine.js: tl = HF.tl, $ = HF.$, $$ = HF.$$,
   beat0 = HF.G.t0, beatLen = HF.G.beat_s, duration = HF.G.duration):
     tl        GSAP timeline (paused)          $ / $$   querySelector / querySelectorAll helpers (string or element)
     beat0     time of beat 0 in seconds       beatLen  seconds per beat            duration  film length in seconds
     host      element that holds FX/blocks (a full-frame layer)
     log?      (type, t) => void - optional; otherwise entries go to window.FX_LOG / window.TX_LOG for the checks
   Scenes that take part in transitions are absolutely positioned siblings (any container); "out"/"in" are selectors or elements.
   Times are ALWAYS beat numbers or VO-word times you compute yourself (e.g. HF.W); never hand-typed seconds.
*/
window.V6_KIT = function (ctx) {
  const { tl, $, $$, beat0, beatLen, duration } = ctx;
  const host = ctx.host;
  if (!tl || !$ || !$$ || typeof beat0 !== "number" || typeof beatLen !== "number") throw new Error("V6_KIT: bad ctx (need tl, $, $$, beat0, beatLen)");
  const FX_LOG = (window.FX_LOG = window.FX_LOG || []);
  const TX_LOG = (window.TX_LOG = window.TX_LOG || []);
  const B = (n) => beat0 + n * beatLen;                                   // time of beat n
  const beatOf = (t) => Math.round((t - beat0) / beatLen);
  const log = (type, t) => { FX_LOG.push({ type, t: +t.toFixed(3) }); if (ctx.log) ctx.log(type, t); };
  const txlog = (type, t, scene) => {
    TX_LOG.push({ type, scene, t: +t.toFixed(3), beat: beatOf(t), dBeat: +(t - B(beatOf(t))).toFixed(3) });
    log("tx-" + type, t);
  };
  const OKA = ["data-layout-allow-overlap", "data-layout-allow-overflow", "data-layout-allow-occlusion"];
  const mk = (parent, cls, html = "", css = "", before = null) => {
    const d = document.createElement("div");
    d.className = cls;
    if (css) d.style.cssText = css;
    d.innerHTML = html;                                                    // build time only
    OKA.forEach((a) => d.setAttribute(a, ""));
    before ? parent.insertBefore(d, before) : parent.append(d);
    return d;
  };
  // words split into masked spans for a kinetic line-in (text comes from YOUR data; escape it yourself if it is user input)
  const kin = (txt) => txt.split(" ").map((w) => `<span class="w"><span class="wi">${w}</span></span>`).join(" ");

  // ================= effects =================
  const sweep = (el, t, w, h, d = 0.6) => {                                // light sweep across a card
    const s = mk(el, "v6-sweep", "", `height:${h * 1.5}px;top:${-h * 0.25}px`);
    tl.set(s, { visibility: "visible" }, t);
    tl.fromTo(s, { x: -300, skewX: -20 }, { x: w + 300, duration: d, ease: "power2.inOut", immediateRender: false }, t);
    tl.set(s, { visibility: "hidden" }, t + d + 0.01);
    log("sweep", t);
  };
  const lift = (el, t, a = 16) => {                                        // element pops out on Z (depth)
    tl.fromTo(el, { z: -260, rotationX: a, transformPerspective: 1600 },
      { z: 0, rotationX: 0, duration: 0.55, ease: "power3.out", immediateRender: false }, t);
    log("lift-z", t);
  };
  const bloom = (parent, x, y, t, col, size = 520, before = null) => {     // soft glow behind a hero number
    const el = mk(parent, "v6-bloom", "", `left:${x - size / 2}px;top:${y - size / 2}px;width:${size}px;height:${size}px;background:radial-gradient(circle, ${col} 0%, rgba(0,0,0,0) 66%)`, before);
    tl.fromTo(el, { autoAlpha: 0, scale: 0.55 }, { autoAlpha: 0.95, scale: 1, duration: 0.22, ease: "power2.out", immediateRender: false }, t);
    tl.to(el, { autoAlpha: 0, scale: 1.35, duration: 0.7, ease: "power1.out" }, t + 0.22);
    log("bloom", t);
  };
  const burst = (parent, x, y, t, col, r = 150) => {                       // 12 fixed particles (no random)
    const box = mk(parent, "v6-burst", "", `left:${x}px;top:${y}px`);
    for (let k = 0; k < 12; k++) {
      box.insertAdjacentHTML("beforeend", `<i style="border-radius:${k % 2 ? "3px" : "50%"};background:${k % 3 ? col : "#fff"}"></i>`);
      const d = box.lastElementChild, a = (Math.PI / 6) * k, rr = r * (k % 2 ? 0.8 : 1);
      tl.set(d, { visibility: "visible" }, t);
      tl.fromTo(d, { x: 0, y: 0, scale: 0 }, { x: Math.cos(a) * rr, y: Math.sin(a) * rr, duration: 0.55, ease: "power3.out", immediateRender: false }, t);
      tl.fromTo(d, { scale: 0 }, { scale: 1, duration: 0.16, ease: "power2.out", immediateRender: false }, t);
      tl.to(d, { scale: 0, duration: 0.36, ease: "power2.in" }, t + 0.18);
      tl.set(d, { visibility: "hidden" }, t + 0.56);
    }
    log("burst", t);
  };
  const blockIn = (el, t, type = "block-in", o = {}) => {
    tl.fromTo(el, { autoAlpha: 0, y: o.y ?? 30, z: -220, rotationX: o.rx ?? 20, transformPerspective: 1600 },
      { autoAlpha: 1, y: 0, z: 0, rotationX: 0, duration: o.d ?? 0.5, ease: "power3.out", immediateRender: false }, t);
    log(type, t);
  };
  const blockOut = (el, t) => tl.to(el, { autoAlpha: 0, y: 16, duration: 0.25, ease: "power1.in" }, t);
  const kinIn = (el, t, st = 0.05) => {
    tl.fromTo($$(".wi", el), { yPercent: 115 }, { yPercent: 0, duration: 0.42, ease: "power3.out", stagger: st, immediateRender: false }, t);
    log("kinetic", t);
  };
  const drawIn = (els, t, d = 0.5, st = 0) => {                            // SVG path with pathLength="1" and class v6-draw
    tl.fromTo(els, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: d, ease: "power2.inOut", stagger: st, immediateRender: false }, t);
    log("draw", t);
  };
  const stamp = (el, t) => {
    tl.fromTo(el, { autoAlpha: 0, scale: 1.9, rotation: -18 }, { autoAlpha: 1, scale: 1, rotation: -6, duration: 0.3, ease: "power3.out", immediateRender: false }, t);
    log("stamp", t);
  };

  // ================= split-flap: blank -> FINAL digit only =================
  // LESSON-16: never pass through a wrong in-between value. Each digit is 1 hinged flap from an empty tile to the final digit,
  // right-most digit leads, 35 ms stagger. Non-digits (",", ".", "%", "d") are static.
  const flapHTML = (str, cls = "") => {
    let h = `<span class="v6-fl ${cls}" data-num="${str}">`;
    for (const ch of String(str)) {
      if (!/\d/.test(ch)) { h += `<span class="fl-s">${ch === " " ? "&nbsp;" : ch}</span>`; continue; }
      const seq = ["&nbsp;", +ch];
      h += `<span class="fl-c" data-n="${seq.length}">${seq.map((x, k) => `<span class="fl-k k${k}">${x}</span>`).join("")}<i class="fl-line"></i></span>`;
    }
    return h + "</span>";
  };
  const flip = (el, t, dur = 0.5) => {
    $$(".fl-c", el).reverse().forEach((c, i) => {
      const n = +c.dataset.n, ks = $$(".fl-k", c);
      if (n < 2) return;
      const sd = Math.min(0.14, (dur - 0.08) / (n - 1));
      ks.forEach((k) => gsap.set(k, { transformPerspective: 420 }));
      for (let j = 1; j < n; j++) {
        const tj = t + i * 0.035 + (j - 1) * sd;
        tl.set(ks[j], { autoAlpha: 1, rotationX: -90, transformOrigin: "50% 0%", zIndex: j }, tj);
        tl.to(ks[j], { rotationX: 0, duration: sd, ease: "power2.in" }, tj);
        tl.set(ks[j - 1], { autoAlpha: 0 }, tj + sd);
      }
    });
    log("flip-counter", t);
  };
  // Put a split-flap over an SVG <text> value (chart labels). The SVG glyphs become fill-opacity 0 as a static attribute.
  const svgFlap = (card, textEl, str, t, o = {}) => {
    const svg = textEl.ownerSVGElement, keep = card.style.transform;
    card.style.transform = "none";
    const rs = svg.getBoundingClientRect(), rc = card.getBoundingClientRect();
    card.style.transform = keep;
    const x = +(textEl.getAttribute("x")), y = +(textEl.dataset.y || textEl.getAttribute("y"));
    const fs = +(textEl.getAttribute("font-size") || (textEl.parentNode && textEl.parentNode.getAttribute("font-size")) || 24);
    const fill = textEl.getAttribute("fill") || (textEl.parentNode && textEl.parentNode.getAttribute("fill")) || "#fff";
    textEl.setAttribute("fill-opacity", "0");
    const el = mk(card, "v6-svgfl", flapHTML(str),
      `left:${rs.left - rc.left - card.clientLeft + x}px;top:${rs.top - rc.top - card.clientTop + y - fs * 0.36}px;font:800 ${fs}px/1 ${o.font || "Inter"};color:${fill}`);
    flip(el, t, o.dur || 0.45);
    return el;
  };

  // ================= beat-locked 3D transitions =================
  // Each takes elements (out = leaving scene, inn = entering scene) and tc = the cut time (a beat). Lands ON the beat: the incoming
  // motion starts at tc; the outgoing anticipation finishes at tc. Outgoing clips that keep playing under a TX should be
  // freeze-extended (tpad clone) by your cut script so the last frame holds through the TX.
  const el$ = (x) => (typeof x === "string" ? $(x) : x);
  const FLIP = (out, inn, tc, name, dir = 1) => {
    gsap.set(out, { transformPerspective: 2200 });
    tl.fromTo(out, { rotationY: 0, scale: 1 }, { rotationY: 90 * dir, scale: 0.9, duration: 0.24, ease: "power2.in", immediateRender: false }, tc - 0.24);
    tl.set(out, { autoAlpha: 0, rotationY: 0, scale: 1 }, tc);
    tl.set(inn, { autoAlpha: 1 }, tc);
    tl.fromTo(inn, { rotationY: -90 * dir, scale: 0.9 }, { rotationY: 0, scale: 1, duration: 0.46, ease: "power3.out", immediateRender: false }, tc);
    txlog("flip", tc, name);
  };
  const PUSH = (out, inn, tc, name, k = 1) => {
    tl.set(inn, { autoAlpha: 1 }, tc);
    tl.fromTo(out, { rotationY: 0, x: 0, scale: 1 }, { rotationY: 26 * k, x: -760 * k, scale: 0.86, duration: 0.55, ease: "power3.inOut", immediateRender: false }, tc);
    tl.fromTo(inn, { rotationY: -26 * k, x: 760 * k, scale: 0.86 }, { rotationY: 0, x: 0, scale: 1, duration: 0.55, ease: "power3.inOut", immediateRender: false }, tc);
    tl.set(out, { autoAlpha: 0, rotationY: 0, x: 0, scale: 1 }, tc + 0.56);
    txlog("push", tc, name);
  };
  const ZOOM = (out, inn, tc, name, showIn = true) => {                    // zoom-through: out scales up + fades, in settles from 1.22
    tl.fromTo(out, { scale: 1, autoAlpha: 1 }, { scale: 1.5, autoAlpha: 0, duration: 0.35, ease: "power3.in", immediateRender: false }, tc - 0.35);
    tl.set(out, { scale: 1 }, tc + 0.01);
    if (showIn) { tl.set(inn, { autoAlpha: 1 }, tc); tl.fromTo(inn, { scale: 1.22 }, { scale: 1, duration: 0.55, ease: "expo.out", immediateRender: false }, tc); }
    else tl.fromTo(inn, { scale: 1.22 }, { scale: 1, duration: 0.9, ease: "power3.out", immediateRender: false }, tc - 0.35);   // inn already under the fading out
    txlog("zoom", tc, name);
  };
  const DROP = (out, inn, tc, name) => {                                   // stack-drop: in drops from above, out sinks
    tl.set(inn, { autoAlpha: 1, transformOrigin: "50% 0%" }, tc);
    tl.fromTo(inn, { y: -300, rotationX: 20, scale: 0.96 }, { y: 0, rotationX: 0, scale: 1, duration: 0.5, ease: "back.out(1.3)", immediateRender: false }, tc);
    tl.fromTo(out, { scale: 1, y: 0 }, { scale: 0.9, y: 60, duration: 0.5, ease: "power2.out", immediateRender: false }, tc);
    tl.set(out, { autoAlpha: 0, scale: 1, y: 0 }, tc + 0.51);
    tl.set(inn, { transformOrigin: "50% 50%" }, tc + 0.52);
    txlog("drop", tc, name);
  };
  const TX = { flip: FLIP, push: PUSH, zoom: ZOOM, drop: DROP };
  // list: [{ type: "flip"|"push"|"zoom"|"drop", out, in, beat | t, name, dir?, k?, showIn? }]
  const transitions = (list) => list.forEach((c) => {
    if (!TX[c.type]) throw new Error("V6_KIT: unknown transition " + c.type);
    const tc = c.t != null ? c.t : B(c.beat);
    if (!isFinite(tc)) throw new Error("V6_KIT: transition needs beat or t");
    const o = el$(c.out), i = el$(c.in);
    if (c.type === "flip") FLIP(o, i, tc, c.name, c.dir || 1);
    else if (c.type === "push") PUSH(o, i, tc, c.name, c.k || 1);
    else if (c.type === "zoom") ZOOM(o, i, tc, c.name, c.showIn !== false);
    else DROP(o, i, tc, c.name);
    if (c.hideOutAtCut) tl.set(o, { autoAlpha: 0 }, tc);
  });

  // ================= 3D life =================
  // idle tilt drift on each app frame: wraps every element matching `sel` (inside each scene) in a .v6tw wrapper and swings it
  // +-2.2 deg / +-1.1 deg over 2 bars (8 beats), alternating direction per scene index.
  const tiltDrift = (sceneSels, frameSel = ".frame", origin) => {
    const per = beatLen * 8;
    sceneSels.forEach((sel, k) => {
      $$(frameSel, $(sel)).forEach((fr) => {
        const w = document.createElement("div");
        w.className = "v6tw";
        OKA.forEach((a) => w.setAttribute(a, ""));
        if (origin) w.style.transformOrigin = origin;
        fr.parentNode.insertBefore(w, fr);
        w.append(fr);
        const sg = k % 2 ? 1 : -1;
        tl.fromTo(w, { rotationY: -2.2 * sg, rotationX: 1.1, transformPerspective: 2000 },
          { rotationY: 2.2 * sg, rotationX: -1.1, duration: per, ease: "sine.inOut", yoyo: true, repeat: Math.ceil(duration / per) }, 0);
      });
    });
    log("tilt-drift", 0);
  };
  // slow parallax of a background screenshot per scene: items = [{ el, start, end }] (seconds; start clamped >= 0, GSAP shifts the
  // whole timeline for negative times)
  const parallax = (items) => items.forEach((it, k) => {
    const im = el$(it.el);
    if (!im) return;
    const sg = k % 2 ? 1 : -1, a0 = Math.max(0, it.start - 0.3);
    tl.fromTo(im, { x: -26 * sg, y: -12, scale: 1.08 }, { x: 26 * sg, y: 12, scale: 1.08, duration: it.end - a0 + 0.3, ease: "none", immediateRender: false }, a0);
    log("parallax", it.start);
  });
  // hero number moment: Z-lift + sweep on the card, bloom + burst behind it (hero = { card, x, y, t, color, host? })
  const hero = (h) => {
    const p = h.host || host;
    lift(h.card, h.t - 0.05, h.a || 20);
    sweep(h.card, h.t + 0.3, h.w || 400, h.h || 200);
    bloom(p, h.x, h.y, h.t + 0.1, h.glow || h.color, h.size || 560, h.before || null);
    burst(p, h.x, h.y, h.t + 0.1, h.color, h.r || 150);
  };

  // ================= generic block: lower third =================
  // number + name in the glass style, below the caption band. Place it with CSS var --v6-lt-top (see v6.css).
  const lowerThird = (n, name, a, b) => {
    const el = mk(host, "v6-g v6-lt", `<div class="bar"></div><span class="n">${n}</span><span class="t">${kin(name)}</span>`);
    blockIn(el, a, "lower-third", { y: 24, rx: 0 });
    tl.fromTo($(".bar", el), { scaleY: 0 }, { scaleY: 1, duration: 0.35, ease: "power3.out", immediateRender: false }, a + 0.05);
    kinIn(el, a + 0.1, 0.06);
    sweep(el, a + 0.35, 700, 88);
    blockOut(el, b);
    return el;
  };

  return { B, beatOf, mk, kin, sweep, lift, bloom, burst, blockIn, blockOut, kinIn, drawIn, stamp, flapHTML, flip, svgFlap, TX, transitions, tiltDrift, parallax, hero, lowerThird, FX_LOG, TX_LOG };
};
