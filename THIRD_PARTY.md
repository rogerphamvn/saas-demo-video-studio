# Third-party components

This repository's own code and docs are MIT (see `LICENSE`). It **does not bundle** any of the components below:
each one is installed or fetched by the user at run time and stays under its own licence. Read each licence yourself
before you sell a video or a service built on it. Checked on 2026-09-28 unless stated otherwise.

| Component | Used for | How it reaches your machine | Licence (as checked) | What you must do |
|---|---|---|---|---|
| **HyperFrames** (HeyGen) | HTML + GSAP composition → MP4 renderer (`npx hyperframes@0.8.78 render/lint`) | npm, at run time | Apache-2.0 | keep the licence + attribution if you redistribute it; if you modify its files, mark them as modified (Apache-2.0 §4) |
| **GSAP** (GreenSock / Webflow) | every animation in `engine/` | CDN `<script>` in `engine/index.html`, at render time | GSAP Standard License — https://gsap.com/standard-license ; the site states "GSAP is now free for everyone". Not an OSI open-source licence | read the licence terms yourself before commercial use; do not vendor-copy GSAP into this repo |
| **Inter** (Rasmus Andersson) | UI / title / caption font | you download it (Google Fonts, `ofl/inter`) into `engine/assets/fonts/` | SIL Open Font License 1.1 | keep the OFL notice if you redistribute the font files (this repo does not) |
| **IBM Plex Serif** Italic + Bold Italic | italic second line of chapter titles | you download it (Google Fonts, `ofl/ibmplexserif`) | SIL Open Font License 1.1 | as above |
| **ffmpeg / ffprobe** | capture (gfxcapture / gdigrab), cutting, mixing, loudness | you install it | LGPL-2.1+ or GPL-2+ depending on the build | not shipped here; follow the licence of the build you install |
| **VieNeu-TTS** (pnnbao97) | local Vietnamese TTS (default voice engine, 0 API cost) | you install it in its own virtualenv | Apache-2.0 (code + model card, as read on the project pages) | credit the project; check the terms of each preset voice before commercial use (not verified here) |
| **OpenAI whisper-1 / gpt-4o-transcribe** (optional) | word-level caption alignment, 2nd-ASR pronunciation check | HTTPS API with **your** key | OpenAI terms | your key, your account, your cost |
| **Gemini TTS** (optional) | alternative voice | HTTPS API with **your** key | Google terms | as above |
| **Python packages** numpy, scipy, Pillow, PyYAML, requests (+ Playwright optional for stills) | scripts | `pip install -r requirements.txt` | BSD / MIT / HPND / Apache-2.0 | none beyond keeping their notices if you redistribute them |
| **Claude Code + Claude in Chrome** | the agent team + driving the logged-in Chrome | you install them | Anthropic terms | — |

## Not included on purpose

- **No footage, audio, renders or stills** of the reference case (they show a real, logged-in product and were
  generated with the author's paid accounts).
- **No music / SFX / b-roll files.** In the reference case they were generated on Magnific (ElevenLabs music, Kling
  video) under the author's account; check the provider's terms before you reuse any generated asset commercially.
- **No motion-reference videos or third-party prompts.** The research notes that inspired the motion vocabulary
  (launch films on whatships.com, posts on X, the `awesome-opus-5-5-videos` collection) were used for learning only
  and are neither copied nor linked as assets here; one reference skill in that ecosystem is CC BY-NC and was not used.
  The method behind `references/director-notes.md` and `templates/prompt-launch-video.md` (named reference style, stop for approval before code, stills per
  scene, director notes as address + phrase + number) comes from the 6-step post by `rexan_wong` (x.com/rexan_wong/status/2103707054108299437); the 12-step course post
  by `0xMovez` (x.com/0xMovez/status/2104216919033192746) embeds and extends it. Both files are our own wording; no prompt or code of either author is copied.
- **No skill from another author is bundled.** `code-rendered-video` (MIT, (c) 2026 viettran) is only *mentioned* in README as an optional companion; get it from its author.
- **No font files.**
