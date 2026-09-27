/* SAMPLE SCENE e02 - minimal chapter: card + title + slot + giant number + "by the numbers" strip, end on a circle wipe. */
(window.SCENES = window.SCENES || {}).e02 = function (HF, C) {
  const { bar, W } = HF;
  HF.card(C, { x: 700, y: 200, w: 1000, h: 520 });
  HF.title(C, "Gõ một con số,", "kết quả chạy theo.");
  HF.slot(C, "S02-editor", { url: "/items/new", note: "type the demo value fixed in capture-script.yaml" });
  const tG = W("tức", "E02");
  HF.giant(`<span class="gk">Về túi mỗi đơn</span><span class="g">312.000<small>₫</small></span>`, tG, bar(7), { style: { left: "110px", top: "430px", fontSize: "160px" } });
  HF.strip([["312.000 ₫", "về túi / đơn"], ["9", "đơn hoà vốn"]], bar(7), null);
  HF.circleWipe(1500, 180, bar(7.5), 0.6);
  HF.hero(C, tG + 0.4);
};
