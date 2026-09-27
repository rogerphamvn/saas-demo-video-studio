/* lib/motion-kit.js - generic motion/graphics layer (v2 "KINETIC SLAB" TX/FX ported onto the single #card of the v3 engine).
   Runs AFTER scenes/eXX.js and BEFORE HF.captions(). Adds ONLY motion: timing, VO, captions, footage cuts, numbers are untouched.
   Deterministic: fixed angles, no Math.random, no onUpdate, no runtime text, no filter, no CSS transition, no bouncy ease.
   ORIGIN: generic half of lib/motion.js from the ProfitBase v3.1 motion pass (snapshot 28/09/2026 00:05, pass NOT finished).
   The case-specific half (one illustration per chapter with the app's real numbers) is NOT shipped - write your own in scenes/.
   TODO(sync-v3.1): re-sync with the final v3.1 motion engine once it is approved (see README ROADMAP).

   Usage (index.html, after all scenes):
     window.MOTION_KIT(HF, window.MOTION_CFG)
   MOTION_CFG (data/motion-cfg.js):
     { tilt: true,                                   // idle 3D drift of the card (rotY +-7, rotX +-3, period 2 bars)
       transitions: [["e03", "push"], ["e04", "flip"], ...],   // clip id (window.CUTS key) -> flip | push | zoom | slab | drop
       pushes: [["e01", 1317, 409, 1.5, "e02", 1.28], ...],    // [slot, x, y (capture px, from capture-log bbox), at bar, until clip t_in, scale]
       drops: [[360, 560, "#6952E0"], ...] }         // bloom + burst at each grid drop (x, y frame px, colour); same order as GRID.drops
*/
window.MOTION_KIT = function (HF, CFG) {
  const { tl, bar, $$, el, FXLOG, P916 } = HF;
  CFG = Object.assign({ tilt: true, transitions: [], pushes: [], drops: [] }, CFG || {});
  const CUTS = window.CUTS || {}, D = HF.G.duration;
  const tIn = (k) => {
    if (!CUTS[k]) throw new Error("MOTION_KIT: clip " + k + " not in window.CUTS");
    return CUTS[k].t_in;
  };

  // ---------- 1. idle 3D life on the card (on #cardtilt so TX transforms on #card stay free) ----------
  if (CFG.tilt) {
    const amp = P916 ? 0.4 : 1;
    gsap.set("#cardtilt", { transformOrigin: P916 ? "540px 640px" : "1320px 422px" });
    const per = HF.BAR * 2;
    tl.fromTo("#cardtilt", { rotationY: -7 * amp, rotationX: 3 * amp }, { rotationY: 7 * amp, rotationX: -3 * amp, duration: per, ease: "sine.inOut",
      yoyo: true, repeat: Math.ceil(D / per) }, 0);
    FXLOG("tilt-drift", 0);
    tl.fromTo("#gridlines", { x: 0, y: 0 }, { x: -80, y: -40, duration: D, ease: "none" }, 0);   // slow parallax of the dot grid
  }

  // ---------- 2. chapter transitions on the grid (swap happens while the card is edge-on / pushed / covered) ----------
  function sweep(t) {
    tl.fromTo("#sweep", { xPercent: -120, autoAlpha: 1 }, { xPercent: 320, duration: 0.7, ease: "power2.inOut" }, t);
    FXLOG("sweep", t);
  }
  function bump(t) { tl.fromTo("#gridlines", { scale: 1.04 }, { scale: 1, duration: 0.6, ease: "expo.out", immediateRender: false }, t); }
  const TX = {
    flip(t) {
      tl.to("#card", { rotationY: 90, duration: 0.2, ease: "power2.in" }, t - 0.2);
      tl.set("#card", { rotationY: -90 }, t);
      tl.to("#card", { rotationY: 0, duration: 0.45, ease: "expo.out" }, t);
    },
    push(t) {
      tl.to("#card", { x: -240, rotationY: 32, z: -220, duration: 0.24, ease: "power2.in" }, t - 0.24);
      tl.set("#card", { x: 300, rotationY: -32, z: -220 }, t);
      tl.to("#card", { x: 0, rotationY: 0, z: 0, duration: 0.5, ease: "expo.out" }, t);
    },
    zoom(t) {
      tl.to("#card", { scale: 1.16, z: 140, duration: 0.24, ease: "power2.in" }, t - 0.24);
      tl.set("#card", { scale: 0.84, z: -160 }, t);
      tl.to("#card", { scale: 1, z: 0, duration: 0.5, ease: "expo.out" }, t);
    },
    slab(t) {
      tl.fromTo("#slab", { xPercent: -130, autoAlpha: 1 }, { xPercent: 130, duration: 0.56, ease: "power2.inOut" }, t - 0.28);
      tl.set("#slab", { autoAlpha: 0 }, t + 0.3);
      tl.fromTo("#card", { scale: 1.05 }, { scale: 1, duration: 0.5, ease: "expo.out", immediateRender: false }, t);
    },
    drop(t) {
      tl.to("#card", { y: 36, scale: 0.94, duration: 0.24, ease: "power2.in" }, t - 0.24);
      tl.set("#card", { y: -150, rotationX: 24, scale: 1 }, t);
      tl.to("#card", { y: 0, rotationX: 0, duration: 0.55, ease: "expo.out" }, t);
    },
  };
  CFG.transitions.forEach(([k, type]) => {
    if (!TX[type]) throw new Error("MOTION_KIT: unknown transition " + type);
    const t = tIn(k);
    TX[type](t);
    FXLOG("tx-" + type, t);
    sweep(t + 0.25);
    bump(t);
  });

  // ---------- 3. post camera push-in on a capture-log bbox, pull-back before the next clip ----------
  CFG.pushes.forEach(([slot, x, y, atBar, untilClip, s]) => HF.push(slot, x, y, bar(atBar), tIn(untilClip), s || 1.3));

  // ---------- 4. bloom + burst at the grid drops ----------
  function bloom(x, y, t, col, size = 700) {
    const b = el("div", "bloom", null, "#fxlayer", { left: x - size / 2 + "px", top: y - size / 2 + "px", width: size + "px", height: size + "px",
      background: `radial-gradient(circle, ${col} 0%, rgba(255,255,255,0) 65%)` });
    HF.hide0(b);
    tl.fromTo(b, { autoAlpha: 0, scale: 0.5 }, { autoAlpha: 0.9, scale: 1, duration: 0.25, ease: "power2.out" }, t);
    tl.to(b, { autoAlpha: 0, scale: 1.3, duration: 0.7, ease: "power1.out" }, t + 0.25);
    FXLOG("bloom", t);
  }
  function burst(x, y, t, col) {
    const b = el("div", "burst", Array.from({ length: 12 }, (_, i) => `<i style="transform:rotate(${i * 30}deg)"><b style="background:${col}"></b></i>`).join(""),
      "#fxlayer", { left: x + "px", top: y + "px" });
    HF.hide0(b);
    tl.set(b, { autoAlpha: 1 }, t);
    tl.fromTo($$("b", b), { x: 20, scaleX: 0.2, autoAlpha: 1 }, { x: 150, scaleX: 1, autoAlpha: 0, duration: 0.6, ease: "expo.out" }, t);
    tl.set(b, { autoAlpha: 0 }, t + 0.65);
    FXLOG("burst", t);
  }
  (HF.G.drops || []).forEach((d, i) => {
    const spec = CFG.drops[i];
    if (!spec) return;
    const [x, y, col] = P916 ? [540, 1170, spec[2]] : spec;
    bloom(x, y, bar(d), col.startsWith("#") ? col + "4D" : col);   // 30% alpha for the bloom
    burst(x, y, bar(d), col);
  });

  // helpers for scene-specific illustrations
  const svgDraw = (path, t, d = 0.6) => tl.fromTo(path, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: d, ease: "power2.out" }, t);
  const pop = (e, t, fx = "pop") => { tl.fromTo(e, { autoAlpha: 0, scale: 0.6, y: 8 }, { autoAlpha: 1, scale: 1, y: 0, duration: 0.35, ease: "expo.out" }, t); FXLOG(fx, t); };
  return { TX, sweep, bump, bloom, burst, svgDraw, pop };
};
