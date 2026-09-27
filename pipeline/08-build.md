# 08 · Dựng HyperFrames song song (agent `sdv-builder` ×1–3) → cổng U2

**Input:** `<comp>/` (copy của `engine/`), `data/grid.js` (bước 07), `vo/captions.json`, `footage/*.mkv` + `capture-log.jsonl`,
storyboard đã chọn, `footage/web-data.md`. `data/cuts.json` = bảng clip (id chương → take, đoạn nguồn, tốc độ, crop, view)
do integrator viết từ capture log + ghi chú cắt của agent quay.

```bash
python scripts/capture/capture_log_to_edit.py build --script capture-script.yaml --log footage/capture-log.jsonl \
       --markers footage/markers.txt --out <comp>/data/        # bbox -> toạ độ khung (con trỏ/camera/highlight/privacy)
python scripts/build/cut_clips.py --config project.json         # cuts.json -> assets/footage/<id>.mp4 + cuts.js + <video> giữa FOOTAGE markers
python scripts/build/erase_pointer.py --config project.json e01 e02 e03   # xoá chấm con trỏ của extension (--probe: chỉ đếm)
python scripts/build/make_captions_js.py --config project.json  # captions.json dịch t0 -> data/captions.js (0 cụm 1 từ)
# builder song song: mỗi người chỉ ghi scenes/eXX.js của mình (engine/scenes/e01.js là mẫu)
cd <comp> && npx --yes hyperframes@0.8.78 lint
npx --yes hyperframes@0.8.78 render -o ../review/draft.mp4 --quality draft   # CHỈ bản nháp khi sửa; full render ở bước 10
cd .. && python scripts/qa/check_numbers.py --config project.json   # G3 — đọc MARKUP: số do scene JS sinh lúc chạy KHÔNG thấy -> soát thêm trên sheet
```

Stills cho U2: seek từng chương giữa khoảng (Playwright headless mở `index.html`, gọi `window.__timelines.main.seek(t)`, chụp PNG)
→ 1 sheet; cảnh thử 15–20 s = chương có nhiều cử chỉ nhất.

**Output:** `<comp>/index.html`, `scenes/*.js`, `data/{cuts,captions,engine-cfg,motion-cfg}.js`, `stills/sheet.png`, cảnh thử.

**Cổng U2:** người dùng duyệt stills + cảnh thử (hoặc `duyệt U2: auto`). **G3** số khớp web-data · **G5** chấm con trỏ đã xoá ·
**G5b** chip/push đúng bbox (crop) · **G9** sheet · lint 0 lỗi (trừ thiếu mix) · ban-list grep 0 hit.
