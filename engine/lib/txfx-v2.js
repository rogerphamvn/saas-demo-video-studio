/* lib/txfx-v2.js - "KINETIC SLAB" transitions + effects from the v2 build (ProfitBase 26/09/2026), multi-scene layout.
   Use it when the film is a sequence of full-frame scenes (#sc01, #sc02 ...) rather than the single #card of the v3 engine
   (for the v3 card layout use lib/motion-kit.js, which ports T1/T2/flip + sweep/bloom/burst onto #card).
   Deterministic GSAP only. STATUS: rendered in the v2 film (user-approved 16:9 v2); extracted here unchanged except the wrapper.
   TASTE WARNING: FX.burst (particles) and FX.kinetic (back.out ease) are on the v3 ban-list - keep them for the v2 style only.

   const K = window.TXFX_V2(tl, { beat0, beatLen, colors: {ink, violet, lilac, electric} })
     K.TX.T1(scIn, tc, {dir:"rl"|"lr"|"bt"|"tb", color, echo, keep})   slab wipe, covers the frame exactly at tc
     K.TX.T2(scOut, scIn, tc, {dir:+1|-1})                              3D card push, rotY +-18, x +-260, 0.55 s
     K.TX.T5(scIn, tc, {color, logo})                                   logo slab: logo 3->1, slab splits open
     K.FX.sweep(host, t, {w,h})  K.FX.bloom(host, t, {x,y,size,color})  K.FX.burst(host, t, {x,y,color,r})
     K.FX.edge(host, t, {x,y,w,h,r})  K.FX.tilt(el, t, {d,a})  K.FX.kinetic(el, t, i)  K.FX.parallax(t, cx, cy, d)
   Every TX call is logged in window.TX_LOG {tx, t, beat, dBeat} (check that transitions sit on the beat: |dBeat| <= 0.04 s).
*/
window.TXFX_V2 = function (tl, o) {
  o = o || {};
  const C = Object.assign({ ink: "#07061A", violet: "#6952E0", lilac: "#C9BCFF", electric: "#35E5FF" }, o.colors || {});
  const INK = C.ink, VIOLET = C.violet, LILAC = C.lilac, ELECTRIC = C.electric;
  const $ = (s, r) => (typeof s === "string" ? (r || document).querySelector(s) : s);
  const OK = "data-layout-allow-overlap data-layout-allow-overflow data-layout-allow-occlusion";
  const beat0 = o.beat0 || 0, beatLen = o.beatLen || 0.5;
  const beatOf = (t) => Math.round((t - beat0) / beatLen);
  window.TX_LOG = window.TX_LOG || [];
  const add = (host, html) => { host.insertAdjacentHTML("beforeend", html); return host.lastElementChild; };
  const clipOf = (host) => {
    let c = Array.from(host.children).find((e) => e.classList && e.classList.contains("fxclip"));
    if (!c) c = add(host, `<div class="fxclip" ${OK} style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:hidden;border-radius:inherit;pointer-events:none;z-index:40"></div>`);
    return c;
  };
  // ============================ local TX (used when A's TX.<name> is missing) ============================
  const LTX = {
    // T1 SLAB-WIPE: incoming scene is revealed by a slab that covers the frame at tc (in 0.22 s power3.in),
    // then the slab leaves (0.30 s power3.out) with a 60 % echo 40 px behind; scene settles 1.06→1 expo.out 0.35 s.
    T1(scIn, tc, o = {}) {
      const dir = o.dir || "rl", color = o.color || VIOLET, echoC = o.echo || color;
      const IN = { rl: ["0% 0% 0% 100%", "0% 0% 0% 0%"], lr: ["0% 100% 0% 0%", "0% 0% 0% 0%"],
                   bt: ["100% 0% 0% 0%", "0% 0% 0% 0%"], tb: ["0% 0% 100% 0%", "0% 0% 0% 0%"] }[dir];
      const OUT = { rl: "0% 100% 0% 0%", lr: "0% 0% 0% 100%", bt: "0% 0% 100% 0%", tb: "100% 0% 0% 0%" }[dir];
      const off = { rl: { x: -40 }, lr: { x: 40 }, bt: { y: -40 }, tb: { y: 40 } }[dir];
      const echo = add(scIn, `<div class="bslab echo" ${OK} style="position:absolute;left:0;top:0;width:1920px;height:1080px;background:${echoC};opacity:.6;z-index:60;pointer-events:none"></div>`);
      const slab = add(scIn, `<div class="bslab" ${OK} style="position:absolute;left:0;top:0;width:1920px;height:1080px;background:${color};z-index:61;pointer-events:none"></div>`);
      const t0 = tc - 0.22;
      // the incoming scene must already be on screen while the slab travels in (A's window may open it later)
      tl.set(scIn, { clipPath: `inset(${IN[0]})` }, 0);
      if (o.early !== false) tl.set(scIn, { autoAlpha: 1 }, t0);
      tl.to(scIn, { clipPath: `inset(${IN[1]})`, duration: 0.22, ease: "power3.in" }, t0);
      tl.set([slab, echo], { clipPath: "inset(0% 0% 0% 0%)", x: 0, y: 0 }, 0);
      tl.set(echo, off, 0);
      if (!o.keep) {
        tl.to(slab, { clipPath: `inset(${OUT})`, duration: 0.30, ease: "power3.out" }, tc);
        tl.to(echo, { clipPath: `inset(${OUT})`, duration: 0.30, ease: "power3.out" }, tc + 0.05);
      } else {                      // slab stays and becomes the end-card background: echo leaves, slab dissolves into #outroBg
        tl.to(echo, { clipPath: `inset(${OUT})`, duration: 0.30, ease: "power3.out" }, tc + 0.05);
        tl.to(slab, { autoAlpha: 0, duration: 0.5, ease: "power1.inOut" }, tc + 0.15);
      }
      tl.fromTo(scIn, { scale: 1.06 }, { scale: 1, duration: 0.35, ease: "expo.out", immediateRender: false }, tc);
      return slab;
    },
    // T2 CARD-PUSH-3D: outgoing card leaves, incoming card arrives, rotationY ±18, x ±260, 0.55 s power3.inOut from tc
    T2(scOut, scIn, tc, o = {}) {
      const s = o.dir || 1;        // +1: new card from the right (s03) · −1: mirror, new card from the left (s07)
      tl.set([scOut, scIn], { transformPerspective: 2200 }, 0);
      tl.fromTo(scIn, { x: 260 * s, rotationY: -18 * s }, { x: 0, rotationY: 0, duration: 0.55, ease: "power3.inOut", immediateRender: false }, tc);
      tl.fromTo(scOut, { x: 0, rotationY: 0 }, { x: -260 * s, rotationY: 18 * s, duration: 0.55, ease: "power3.inOut", immediateRender: false }, tc);
    },
    // T5 LOGO-SLAB: two slab halves close on the beat, logo 3→1 expo.out 0.3 s, halves split open and reveal the scene
    T5(scIn, tc, o = {}) {
      const c = o.color || VIOLET;
      const top = add(scIn, `<div class="bslab" ${OK} style="position:absolute;left:0;top:0;width:1920px;height:540px;background:${c};z-index:61"></div>`);
      const bot = add(scIn, `<div class="bslab" ${OK} style="position:absolute;left:0;top:540px;width:1920px;height:540px;background:${c};z-index:61"></div>`);
      const logo = o.logo;
      tl.set(scIn, { autoAlpha: 1 }, tc - 0.18);
      tl.fromTo(top, { y: -540 }, { y: 0, duration: 0.18, ease: "power3.in" }, tc - 0.18);
      tl.fromTo(bot, { y: 540 }, { y: 0, duration: 0.18, ease: "power3.in" }, tc - 0.18);
      if (logo) tl.fromTo(logo, { scale: 3 }, { scale: 1, duration: 0.3, ease: "expo.out", immediateRender: false }, tc);
      tl.to(top, { y: -560, duration: 0.4, ease: "power3.inOut" }, tc + 0.32);
      tl.to(bot, { y: 560, duration: 0.4, ease: "power3.inOut" }, tc + 0.32);
    },
  };

  // ============================ local FX ============================
  const LFX = {
    // light sweep: 110° gradient band, skew −20°, x −600 → host width + 200, 0.6 s, blend screen
    sweep(host, t, o = {}) {
      const w = o.w || 1920, h = o.h || 1080;
      const el = add(clipOf(host), `<div class="bfx-sweep" ${OK} style="position:absolute;left:0;top:${-h * 0.25}px;width:420px;height:${h * 1.5}px;mix-blend-mode:screen;background:linear-gradient(110deg,rgba(255,255,255,0) 0%,rgba(255,255,255,0) 32%,rgba(255,255,255,.34) 50%,rgba(255,255,255,0) 68%,rgba(255,255,255,0) 100%)"></div>`);
      tl.fromTo(el, { x: -600, skewX: -20 }, { x: w + 200, duration: o.d || 0.6, ease: "power2.inOut" }, t);
    },
    // bloom behind a number: radial glow scale .6→1.4, opacity .9→0, 0.6 s
    bloom(host, t, o = {}) {
      const s = o.size || 380, c = o.color || LILAC;
      const el = add(host, `<div class="bfx-bloom" ${OK} style="position:absolute;left:${(o.x ?? 0) - s / 2}px;top:${(o.y ?? 0) - s / 2}px;width:${s}px;height:${s}px;border-radius:50%;pointer-events:none;mix-blend-mode:screen;z-index:${o.z ?? 0};background:radial-gradient(circle, ${c} 0%, rgba(0,0,0,0) 66%)"></div>`);
      tl.fromTo(el, { autoAlpha: 0, scale: 0.6 }, { autoAlpha: 0.9, duration: 0.06, ease: "none" }, t);
      tl.to(el, { scale: 1.4, duration: 0.6, ease: "power2.out" }, t);
      tl.to(el, { autoAlpha: 0, duration: 0.54, ease: "power2.in" }, t + 0.06);
    },
    // number burst: 12 particles at 30°·k, radius 140, 0.5 s
    burst(host, t, o = {}) {
      const r = o.r || 140, c = o.color || ELECTRIC;
      const box = add(host, `<div class="bfx-burst" ${OK} style="position:absolute;left:${o.x ?? 0}px;top:${o.y ?? 0}px;width:0;height:0;z-index:${o.z ?? 30};pointer-events:none"></div>`);
      const dots = [];
      for (let k = 0; k < 12; k++)
        dots.push(add(box, `<i ${OK} style="position:absolute;left:-7px;top:-7px;width:14px;height:14px;border-radius:${k % 2 ? "3px" : "50%"};background:${k % 3 ? c : "#fff"}"></i>`));
      tl.fromTo(dots, { autoAlpha: 0, x: 0, y: 0, scale: 1 }, { autoAlpha: 1, duration: 0.02, ease: "none" }, t);
      dots.forEach((d, k) => {
        const a = (Math.PI / 6) * k, rr = r * (k % 2 ? 0.8 : 1);
        tl.to(d, { x: Math.cos(a) * rr, y: Math.sin(a) * rr, scale: 0.35, rotation: 90, duration: 0.5, ease: "power3.out" }, t);
      });
      tl.to(dots, { autoAlpha: 0, duration: 0.28, ease: "power1.in" }, t + 0.22);
    },
    // electric edge: conic highlight running once around a rounded box (1.2 s); ring = mask-composite, no blur
    edge(host, t, o = {}) {
      const { x = 0, y = 0, w = 400, h = 200, r = 24 } = o, d = Math.ceil(Math.hypot(w, h)) + 40;
      const ring = add(host, `<div class="bfx-edge" ${OK} style="position:absolute;left:${x - 3}px;top:${y - 3}px;width:${w + 6}px;height:${h + 6}px;border-radius:${r + 3}px;padding:4px;box-sizing:border-box;overflow:hidden;pointer-events:none;z-index:${o.z ?? 35};-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask:linear-gradient(#000 0 0) content-box exclude,linear-gradient(#000 0 0)"><div ${OK} style="position:absolute;left:${(w + 6 - d) / 2}px;top:${(h + 6 - d) / 2}px;width:${d}px;height:${d}px;background:conic-gradient(from 0deg, rgba(53,229,255,0) 0deg, rgba(53,229,255,0) 250deg, ${ELECTRIC} 320deg, #fff 348deg, rgba(53,229,255,0) 360deg)"></div></div>`);
      const spin = ring.firstElementChild;
      tl.fromTo(ring, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.15, ease: "power1.out" }, t);
      tl.fromTo(spin, { rotation: 0 }, { rotation: 360, duration: o.d || 1.2, ease: "none", immediateRender: false }, t);
      tl.to(ring, { autoAlpha: 0, duration: 0.3, ease: "power1.in" }, t + (o.d || 1.2) - 0.3);
    },
    // tilt: ±a° rotationY, sine.inOut, ends back at 0
    tilt(el, t, o = {}) {
      const a = o.a ?? 4, d = o.d ?? 1.8;
      tl.set(el, { transformPerspective: 1800 }, 0);
      tl.to(el, { rotationY: a, rotationX: -a * 0.4, duration: d * 0.35, ease: "sine.inOut" }, t);
      tl.to(el, { rotationY: -a, rotationX: a * 0.4, duration: d * 0.4, ease: "sine.inOut" }, t + d * 0.35);
      tl.to(el, { rotationY: 0, rotationX: 0, duration: d * 0.25, ease: "sine.inOut" }, t + d * 0.75);
    },
    // kinetic type: rotationZ ±2° by parity
    kinetic(el, t, i = 0) {
      tl.fromTo(el, { rotation: 0 }, { rotation: i % 2 ? 2 : -2, duration: 0.4, ease: "back.out(2)", immediateRender: false }, t);
    },
    // parallax: dot grid follows the camera, x = (cx − 800)·0.08
    parallax(t, cx, cy, d = 0.7) {
      const g = $("#grid");
      if (g) tl.to(g, { x: (cx - 800) * 0.08, y: (cy - 421) * 0.05, duration: d, ease: "power3.inOut" }, t);
    },
  };
  const TX = {};
  ["T1", "T2", "T5"].forEach((k) => (TX[k] = (...a) => {
    const t = k === "T2" ? a[2] : a[1];
    window.TX_LOG.push({ tx: k, t: +t.toFixed(3), beat: beatOf(t), dBeat: +(t - (beat0 + beatOf(t) * beatLen)).toFixed(3) });
    return LTX[k](...a);
  }));
  void INK;
  return { TX, FX: LFX };
};
