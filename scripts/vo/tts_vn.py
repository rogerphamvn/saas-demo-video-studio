#!/usr/bin/env python3
"""Voice over tieng Viet (Gemini 3.8 Flash TTS hoac VieNeu-TTS local) + captions.json cho Remotion.

Pipeline:
  script.txt (moi cau 1 dong)
    -> sinh audio TUNG CAU (tranh gioi han 8,192 input token, va biet chinh xac cau nao bat dau luc nao)
       * --engine gemini (mac dinh): Gemini 3.8 Flash TTS, WAV 24 kHz mono 16-bit
       * --engine vieneu: VieNeu-TTS chay local trong venv rieng (subprocess vieneu_worker.py), 48 kHz -> PCM 16-bit
    -> noi WAV + chen khoang lang giua cau -> voiceover.wav
    -> captions.json theo dung kieu `Caption` cua @remotion/captions
       * mac dinh: timing tu doan theo do dai chu trong tung cau (source = "estimate")
       * --align whisper: OpenAI whisper-1 word timestamps, ghep vao CHU CUA SCRIPT bang difflib
         (source = "aligned-whisper", kem matched_ratio). Tu khong khop (vd "bon muoi" <-> "40") -> noi suy.
       * --align elevenlabs: ElevenLabs Forced Alignment (source = "elevenlabs-forced-alignment")
       * --align-strict: aligner khong dat (whisper matched_ratio < 0.8, elevenlabs lech so tu) -> exit 2,
         KHONG ghi captions.json (ghi captions.rejected.json de soi). Khong im lang roi ve estimate (LESSON-04).

Chu hien tren man hinh LUON la chu trong script (nguon su that), khong phai chu ASR nghe lai.

STATUS: TESTED (vendored from the hub voiceover tool used in the 26-27/09 ProfitBase case: gen_tts.py / align.py import
        split_sentences, whisper_words, align_script_to_asr, to_captions from it). Changed here: keys come from the environment
        or ./.env (no hub credential loader), VieNeu python from env VIENEU_PY / --vieneu-python. --fake-tts re-run here.

Key: bien moi truong hoac file ./.env (KEY=VALUE). KHONG hardcode, khong in key ra man hinh.
  GEMINI_API_KEY (hoac GOOGLE_API_KEY)   - khi --engine gemini (tru --fake-tts)
  OPENAI_API_KEY                          - khi --align whisper
  ELEVENLABS_API_KEY                      - khi --align elevenlabs

Vi du:
  python scripts/vo/tts_vn.py script.txt --out vo/simple --engine gemini --voice Kore --style "am ap, ke chuyen, toc do vua"
  python scripts/vo/tts_vn.py script.txt --out vo/simple --align whisper --align-strict
  python scripts/vo/tts_vn.py script.txt --out vo/simple --engine vieneu --vieneu-voice "Ngoc Huyen" --align whisper
  python scripts/vo/tts_vn.py script.txt --out tmp --fake-tts      # test pipeline khong ton tien, khong can key
  (the grid-first v3 pipeline uses gen_tts.py -> measure.py -> assemble.py -> align.py, which import this file)

Nguon API (doc 2026-09-25): https://ai.google.dev/gemini-api/docs/speech-generation (Last updated 2026-09-24)
                            https://elevenlabs.io/docs/api-reference/forced-alignment/create
                            https://developers.openai.com/api/docs/guides/speech-to-text (whisper-1 word timestamps)
"""
from __future__ import annotations

import argparse
import base64
import difflib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/ (for lib.config)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
ELEVEN_ALIGN_URL = "https://api.elevenlabs.io/v1/forced-alignment"
OPENAI_STT_URL = "https://api.openai.com/v1/audio/transcriptions"
GEMINI_RATE = 24000  # Gemini 3.8 TTS: WAV 24 kHz mono 16-bit (docs, muc "Audio output formats")
VIENEU_PY_DEFAULT = os.environ.get("VIENEU_PY", "")  # python.exe of the VieNeu venv (env VIENEU_PY or --vieneu-python)
WORKER = Path(__file__).resolve().parent / "vieneu_worker.py"
WHISPER_MAX_BYTES = 25 * 1024 * 1024  # gioi han file cua OpenAI transcriptions
STRICT_MIN_RATIO = 0.8


def get_key(*names: str) -> str:
    from lib.config import get_key as _get  # noqa: E402  (env first, then ./.env; never prints the value)

    return _get(*names)


def split_sentences(text: str) -> list[str]:
    """1 dong = 1 cau. Dong dai bi tach them theo dau . ! ? de moi request ngan."""
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        out += [s.strip() for s in re.split(r"(?<=[.!?…])\s+", line) if s.strip()]
    return out


def tts_gemini(sentence: str, key: str, model: str, voice: str, style: str | None) -> bytes:
    import requests

    content: dict = {"type": "text", "text": sentence}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    body = {
        "model": model,
        "input": [{"type": "user_input", "content": [content]}],
        "response_format": {"type": "audio"},  # unary -> audio/wav co RIFF header
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    for attempt in range(6):
        r = requests.post(GEMINI_URL, headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                          json=body, timeout=120)
        if r.status_code != 429:
            break
        # Free Tier = 3 request/phut; 1 cau = 1 request -> cho dung so giay API bao roi thu lai
        m = re.search(r"retry in (\d+(?:\.\d+)?)s", r.text)
        wait_s = float(m.group(1)) + 2 if m else 25
        print(f"  429 rate limit - cho {wait_s:.0f}s (lan {attempt + 1}/6)", file=sys.stderr)
        time.sleep(wait_s)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini TTS HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    audio = [c for s in data.get("steps", []) if s.get("type") == "model_output"
             for c in s.get("content", []) if c.get("type") == "audio"]
    if not audio:
        raise RuntimeError(f"Response khong co audio block: {json.dumps(data)[:500]}")
    return base64.b64decode(audio[-1]["data"])


def tts_vieneu(sentences: list[str], py: str, voice: str | None) -> tuple[list[bytes], dict]:
    """Goi vieneu_worker.py bang python cua venv VieNeu. Load model 1 lan cho ca kich ban."""
    if not py or not Path(py).exists():
        raise RuntimeError(f"Khong thay python cua venv VieNeu: '{py}' - set env VIENEU_PY or pass --vieneu-python "
                           "(install VieNeu-TTS in its own venv, see the repo docs)")
    with tempfile.TemporaryDirectory(prefix="vieneu_") as td:
        inp = Path(td) / "sentences.json"
        inp.write_text(json.dumps(sentences, ensure_ascii=False), encoding="utf-8")
        cmd = [py, str(WORKER), "--in", str(inp), "--outdir", str(Path(td) / "wav")]
        if voice:
            cmd += ["--voice", voice]
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        if p.returncode != 0:
            raise RuntimeError(f"vieneu_worker exit {p.returncode}: {p.stderr[-800:]}")
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
        if not lines:
            raise RuntimeError(f"vieneu_worker khong in manifest JSON. stdout: {p.stdout[-500:]}")
        meta = json.loads(lines[-1])
        if len(meta["files"]) != len(sentences):
            raise RuntimeError(f"vieneu_worker tra {len(meta['files'])} file, can {len(sentences)}")
        return [Path(f).read_bytes() for f in meta["files"]], meta


def fake_wav(sentence: str, rate: int) -> bytes:
    """Im lang dai ~ 0.28s/am tiet - chi de test pipeline, KHONG phai giong that."""
    n = int(rate * max(0.6, 0.28 * len(sentence.split())))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n)
    return buf.getvalue()


def read_pcm(wav_bytes: bytes) -> tuple[bytes, int]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise RuntimeError("WAV khong phai mono 16-bit - doc lai muc Audio output formats")
        return w.readframes(w.getnframes()), w.getframerate()


def estimate_words(sentence: str, t0: float, t1: float) -> list[dict]:
    """Chia [t0,t1] (giay) cho tung tu theo trong so do dai. Tieng Viet 1 tu = 1 am tiet nen sai so nho,
    nhung van la UOC LUONG - highlight co the lech ~100-300ms o cau co so / tu muon."""
    words = sentence.split()
    weights = [len(w) + 2 for w in words]
    total = sum(weights)
    out, cur = [], t0
    for w, wt in zip(words, weights):
        d = (t1 - t0) * wt / total
        out.append({"text": w, "start": cur, "end": cur + d})
        cur += d
    return out


def align_elevenlabs(wav_path: Path, full_text: str, key: str) -> list[dict]:
    import requests

    with open(wav_path, "rb") as f:
        r = requests.post(ELEVEN_ALIGN_URL, headers={"xi-api-key": key},
                          files={"file": (wav_path.name, f, "audio/wav")}, data={"text": full_text}, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs forced-alignment HTTP {r.status_code}: {r.text[:500]}")
    words = [w for w in r.json().get("words", []) if w.get("text", "").strip()]
    return [{"text": w["text"].strip(), "start": w["start"], "end": w["end"]} for w in words]


def whisper_words(wav_path: Path, key: str) -> list[dict]:
    """OpenAI whisper-1, verbose_json + timestamp_granularities[]=word, language=vi."""
    import requests

    if wav_path.stat().st_size > WHISPER_MAX_BYTES:
        raise RuntimeError(f"{wav_path} > 25 MB - whisper-1 tu choi. Cat nho audio hoac dung --align elevenlabs")
    with open(wav_path, "rb") as f:
        r = requests.post(OPENAI_STT_URL, headers={"Authorization": "Bearer " + key},
                          files={"file": (wav_path.name, f, "audio/wav")},
                          data={"model": "whisper-1", "response_format": "verbose_json",
                                "timestamp_granularities[]": "word", "language": "vi"}, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"OpenAI whisper-1 HTTP {r.status_code}: {r.text[:500]}")
    return [{"text": w["word"], "start": float(w["start"]), "end": float(w["end"])}
            for w in r.json().get("words", []) if str(w.get("word", "")).strip()]


def norm_token(t: str) -> str:
    """lower + bo dau cau (giu chu cai co dau tieng Viet va chu so)."""
    return re.sub(r"[^\w]", "", t.lower(), flags=re.UNICODE)


def _spread(words: list[dict], idx: list[int], t0: float, t1: float) -> None:
    """Chia [t0,t1] cho cac tu script idx theo trong so do dai chu."""
    t1 = max(t1, t0)
    weights = [len(words[i]["text"]) + 2 for i in idx]
    total = sum(weights) or 1
    cur = t0
    for i, wt in zip(idx, weights):
        d = (t1 - t0) * wt / total
        words[i]["start"], words[i]["end"] = cur, cur + d
        cur += d


def align_script_to_asr(words: list[dict], asr: list[dict], duration: float) -> tuple[float, list[int]]:
    """Ghep timing ASR vao tu script (giu CHU script). Tra (matched_ratio, index tu script KHONG khop).

    - equal: lay thang start/end cua tu ASR tuong ung.
    - replace (vd script "bon muoi" <-> ASR "40", "nen" <-> "den"): chia khoang thoi gian cua cac tu ASR bi thay.
    - delete (script co, ASR bo sot): noi suy trong khoang [end tu khop truoc, start tu khop sau].
    - insert (ASR thua tu): bo qua.
    """
    a = [norm_token(w["text"]) for w in words]
    b = [norm_token(w["text"]) for w in asr]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    matched, unmatched, pending = 0, [], []  # pending: (i1, i2, span|None)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                words[i1 + k]["start"], words[i1 + k]["end"] = asr[j1 + k]["start"], asr[j1 + k]["end"]
            matched += i2 - i1
        elif tag in ("replace", "delete"):
            unmatched += list(range(i1, i2))
            span = (asr[j1]["start"], asr[j2 - 1]["end"]) if tag == "replace" else None
            pending.append((i1, i2, span))
    # tu khong khop: can 2 ben lay tu tu script da co timing (sau vong tren)
    for i1, i2, span in pending:
        prev_end = words[i1 - 1]["end"] if i1 > 0 and (i1 - 1) not in unmatched else None
        next_start = words[i2]["start"] if i2 < len(words) and i2 not in unmatched else None
        if span:
            t0, t1 = span
        else:
            t0 = prev_end if prev_end is not None else 0.0
            t1 = next_start if next_start is not None else duration
        if prev_end is not None:
            t0 = max(t0, prev_end)
        if next_start is not None:
            t1 = min(t1, next_start)
        _spread(words, list(range(i1, i2)), t0, t1)
    fix_short_words(words, duration)
    clamp_words(words, duration)  # SAU fix_short_words (Fable #238: clamp truoc -> fix co the tao start > end)
    return (matched / len(words) if words else 0.0), unmatched


def clamp_words(words: list[dict], duration: float) -> None:
    """Bat bien cuoi: 0 <= start <= end <= duration va start khong lui ve truoc end cua tu truoc."""
    prev_end = 0.0
    for w in words:
        w["end"] = min(max(w["end"], 0.0), duration)
        w["start"] = min(max(w["start"], prev_end, 0.0), w["end"])
        prev_end = w["end"]


MIN_WORD_S = 0.08


def fix_short_words(words: list[dict], duration: float | None = None) -> int:
    """whisper-1 hay tra tu start == end (do that 2026-09-26: "hom" 1360->1360 ms sau khoang nghi dau phay)
    -> tu do KHONG BAO GIO duoc highlight. Keo start lui vao khoang lang truoc, thieu nua thi keo end toi."""
    fixed = 0
    for i, w in enumerate(words):
        if w["end"] - w["start"] >= MIN_WORD_S:
            continue
        prev_end = words[i - 1]["end"] if i > 0 else 0.0
        # min(...,w["end"]): ASR chong lan (prev_end > end) khong duoc day start vuot end
        w["start"] = min(max(prev_end, w["end"] - MIN_WORD_S), w["end"])
        if w["end"] - w["start"] < MIN_WORD_S:
            if i + 1 < len(words):
                w["end"] = max(w["end"], min(words[i + 1]["start"], w["start"] + MIN_WORD_S))
            elif duration is not None:  # tu cuoi: keo end toi toi da duration
                w["end"] = max(w["end"], min(duration, w["start"] + MIN_WORD_S))
        fixed += 1
    return fixed


def to_captions(words: list[dict]) -> list[dict]:
    """Kieu Caption cua @remotion/captions: text co DAU CACH PHIA TRUOC (tru tu dau)."""
    caps = []
    for i, w in enumerate(words):
        s, e = round(w["start"] * 1000), round(w["end"] * 1000)
        caps.append({"text": w["text"] if i == 0 else " " + w["text"], "startMs": s, "endMs": e,
                     "timestampMs": (s + e) // 2, "confidence": None})
    return caps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--out", default="public/voiceover")
    ap.add_argument("--engine", choices=["gemini", "vieneu"], default="vieneu",
                    help="mac dinh vieneu (user chon 26/09 sau khi nghe so sanh: local, 0 phi API, Apache-2.0); "
                         "gemini = Gemini 3.8 Flash TTS (can GEMINI_API_KEY, tinh phi)")
    ap.add_argument("--model", default="gemini-3.8-flash-tts", help="hoac gemini-3.8-flash-lite-tts (re hon)")
    ap.add_argument("--voice", default="Kore", help="giong Gemini")
    ap.add_argument("--style", default=None, help="speech_metadata.style (Gemini), vd 'am ap, toc do vua'")
    ap.add_argument("--vieneu-voice", default=None, help="giong preset VieNeu, vd 'Ngoc Huyen' (mac dinh: giong mac dinh)")
    ap.add_argument("--vieneu-python", default=VIENEU_PY_DEFAULT, help="python.exe cua venv VieNeu (default env VIENEU_PY)")
    ap.add_argument("--gap-ms", type=int, default=250, help="khoang lang chen giua cac cau")
    ap.add_argument("--align", choices=["none", "whisper", "elevenlabs"], default="none")
    ap.add_argument("--align-strict", action="store_true",
                    help=f"aligner khong dat (whisper matched_ratio < {STRICT_MIN_RATIO}, elevenlabs lech so tu) -> exit 2")
    ap.add_argument("--fake-tts", action="store_true", help="khong goi API - test pipeline")
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    sentences = split_sentences(Path(a.script).read_text(encoding="utf-8"))
    if not sentences:
        sys.exit("Script rong")

    t_start = time.time()
    extra: dict = {}
    if a.fake_tts:
        chunks = [fake_wav(s, GEMINI_RATE) for s in sentences]
    elif a.engine == "vieneu":
        chunks, meta = tts_vieneu(sentences, a.vieneu_python, a.vieneu_voice)
        extra["vieneu"] = {k: meta[k] for k in ("load_s", "infer_s", "peak_abs") if k in meta}
        print(f"VieNeu: load {meta.get('load_s')}s, infer {meta.get('infer_s')}s, rate {meta.get('rate')}")
    else:
        key = get_key("GEMINI_API_KEY", "GOOGLE_API_KEY")
        chunks = [tts_gemini(s, key, a.model, a.voice, a.style) for s in sentences]

    pcm_all, words, cursor, rate = bytearray(), [], 0.0, None
    for i, (s, wav_bytes) in enumerate(zip(sentences, chunks)):
        pcm, r = read_pcm(wav_bytes)
        if rate is None:
            rate = r
        elif r != rate:
            raise RuntimeError(f"Cau {i + 1}: sample rate {r} != {rate} - khong noi thang duoc, can resample")
        dur = len(pcm) / 2 / rate
        words += estimate_words(s, cursor, cursor + dur)
        pcm_all += pcm; cursor += dur
        if i < len(sentences) - 1:
            pcm_all += b"\x00\x00" * int(rate * a.gap_ms / 1000); cursor += a.gap_ms / 1000
        print(f"[{i + 1}/{len(sentences)}] {dur:5.2f}s  {s[:60]}")
    tts_wall = time.time() - t_start

    wav_path = out / "voiceover.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(pcm_all))

    source, reject = "estimate", None
    if a.align == "whisper":
        asr = whisper_words(wav_path, get_key("OPENAI_API_KEY"))
        ratio, unmatched = align_script_to_asr(words, asr, cursor)
        source = "aligned-whisper"
        extra.update(matched_ratio=round(ratio, 3), asr_word_count=len(asr),
                     unmatched_words=[{"i": i, "text": words[i]["text"]} for i in unmatched],
                     asr_text=" ".join(w["text"] for w in asr))
        print(f"whisper-1: {len(asr)} tu ASR, script {len(words)} tu, matched_ratio={ratio:.3f}, "
              f"noi suy {len(unmatched)} tu")
        if ratio < STRICT_MIN_RATIO:
            msg = f"matched_ratio {ratio:.3f} < {STRICT_MIN_RATIO}"
            if a.align_strict:
                reject = msg
            else:
                source = "aligned-whisper-lowconf"  # Fable #238: khong gan nhan "aligned-whisper" cho ratio thap
                print(f"CANH BAO: {msg} - timing nhieu tu la noi suy, nghe/soi lai truoc khi dung", file=sys.stderr)
    elif a.align == "elevenlabs":
        aligned = align_elevenlabs(wav_path, " ".join(sentences), get_key("ELEVENLABS_API_KEY"))
        if len(aligned) == len(words):
            for w_est, w_al in zip(words, aligned):  # giu CHU cua script, lay TIMING cua aligner
                w_est["start"], w_est["end"] = w_al["start"], w_al["end"]
            source = "elevenlabs-forced-alignment"
        elif a.align_strict:
            reject = f"aligner tra {len(aligned)} tu, script co {len(words)} tu"
        else:
            print(f"CANH BAO: aligner tra {len(aligned)} tu, script co {len(words)} tu -> giu timing uoc luong",
                  file=sys.stderr)

    engine = "fake" if a.fake_tts else a.engine
    result = {"durationMs": round(cursor * 1000), "source": source, "engine": engine,
              "model": a.model if engine == "gemini" else None,
              "voice": a.voice if engine == "gemini" else a.vieneu_voice,
              "sampleRate": rate, "ttsWallS": round(tts_wall, 1), **extra, "captions": to_captions(words)}
    cap_path = out / "captions.json"
    if reject:
        # khong de captions.json CU nam lai lam nguoi sau tuong la ket qua moi
        if cap_path.exists():
            cap_path.unlink()
        result["rejected"] = reject
        (out / "captions.rejected.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"FAIL --align-strict: {reject}. Da ghi captions.rejected.json, KHONG ghi captions.json", file=sys.stderr)
        sys.exit(2)
    cap_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {wav_path} ({cursor:.2f}s, {rate} Hz) + captions.json ({len(words)} tu, source={source})")


if __name__ == "__main__":
    main()
