# 06 · VO VieNeu + phát âm + lưới + căn chữ (agent `sdv-voiceover`, song song với 05)

**Input:** `vo/script.txt` (`E1|câu…`), lưới + bảng chương trong `project.json`, `VIENEU_PY`, (tuỳ chọn) `OPENAI_API_KEY`.

```bash
python scripts/vo/gen_tts.py --config project.json                    # 1 take/câu (--fake-tts: thử pipeline không cần model)
python scripts/vo/asr_check.py vo/raw/wav/000.wav vo/raw/wav/001.wav  # 2 ASR nghe lại từ khó (cần OPENAI_API_KEY)
python scripts/vo/gen_var.py --config project.json vo/variants1.json  # biến thể phiên âm cho câu sai (chữ script KHÔNG đổi)
python scripts/vo/select_takes.py --config project.json               # chọn take theo bảng trong config
python scripts/vo/measure.py --config project.json                    # onset/offset từng câu
python scripts/vo/assemble.py --config project.json                   # ghép dòng, đặt lên ô chương -> voiceover.wav, placements.json, fit.md
python scripts/vo/align.py --config project.json                      # whisper theo dòng + offset -> captions.json + cụm 2–4 từ
```

Đường đơn giản (không lưới): `python scripts/vo/tts_vn.py vo/script.txt --out vo/simple --engine vieneu --align whisper --align-strict`.

**Output:** `vo/voiceover.wav`, `vo/placements.json`, `vo/captions.json`, `vo/fit.md`.

**Cổng G1/G1b:** ratio ≥ 0.8 · diff chữ 0 · 0 cặp từ ghép bị tách · dòng tràn ô > 0,3 s → báo người dùng bớt chữ (không nén giọng).
