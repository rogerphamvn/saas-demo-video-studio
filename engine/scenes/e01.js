/* SAMPLE SCENE e01 - shows the whole HF contract on one chapter (bars 0-4 of the sample grid).
   Pattern for every real scene (write one file per chapter, parallel-buildable, never touch index.html / engine / tokens):
     1. HF.card(C, viewRect)          -> the right-hand UI card (morphs from the previous chapter's card)
     2. HF.title(C, line1, line2)     -> 2-line kinetic title in the left column
     3. HF.slot(C, "<shot id>", ...)  -> footage slot (placeholder until data/cuts.json has this chapter's clip)
     4. ONE number gesture per chapter (odometer / bite bar / dots / giant) - numbers ONLY from footage/web-data (never invented)
     5. times from HF.bar(n) / HF.beat(n) / HF.W("word", "E01") - never a hand-typed second
   R = the crop of the 1920x1010 capture that the card shows (x, y, w, h in capture px). */
(window.SCENES = window.SCENES || {}).e01 = function (HF, C) {
  const { tl, bar, beat, W } = HF;
  const R = { x: 880, y: 120, w: 900, h: 560 };
  HF.card(C, R);
  HF.title(C, "Mở app lên,", "thấy ngay lãi lỗ.");
  const s = HF.slot(C, "S01-dashboard", { url: "/dashboard", note: "shot id = capture-script.yaml id" });
  HF.target(s, "e01-kpi", 420, 260, "KPI card - replace with the capture-log bbox");

  // number gesture: split-flap counter 0 -> 12.500.000 on the word "lãi" (the digits are in the markup at build time)
  const tNum = W("lãi", "E01") - 0.2;
  const c = HF.callout({ x: 640, y: 440, w: 520 },
    `<div class="k">Lợi nhuận tháng này</div><div class="v"><b class="odov">${HF.odoHTML(null, "12.500.000")} ₫</b></div>` +
    `<div class="s">${HF.pill("+18% so với tháng trước", "g")}</div>`, tNum - 0.3, C.t_out, { id: "e01-kpi" });
  HF.odo(c.querySelector(".odov"), tNum, 0.8);

  // bridge chip: appears on the card, flies to the left column on the downbeat of bar 3
  HF.chipShow(bar(2), 1200, 300);
  HF.chipTo(bar(3), 700, 620, { dur: 0.5 });
  HF.chipHide(C.t_out - beat(1));

  // drop moment (GRID.drops) gets the ambient light + a hero timestamp for stills
  HF.light("g", bar(3.5), 0.6);
  HF.light("g", C.t_out - 0.4, 0.3, 0);
  HF.hero(C, tNum + 0.8);
};
