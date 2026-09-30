# PROMPT-LAUNCH-VIDEO — mẫu prompt "video ra mắt sản phẩm" (2 bản: EN + VI)

> Nguồn: prompt gốc của user (30/09/2026) + 6 ràng buộc ProfitBase đã chứng minh (số thật · privacy · macro-mode · lưới nhịp · phụ đề tiếng Việt live · 3 cổng user)
> + bài học từ 2 bài X: `rexan_wong` (6 bước, x.com/rexan_wong/status/2103707054108299437) và `0xMovez` (khoá 12 bước có nhúng 6 bước đó, x.com/0xMovez/status/2104216919033192746): ref phải có TÊN; dừng chờ duyệt storyboard trước khi viết code; tự chấm trên ảnh. Template do ta tự viết, không chép prompt của tác giả nào.
> Đây là **template**: thay mọi `{{...}}`. Không có chỗ nào được để trống mà vẫn chạy — chỗ nào chưa có, agent phải HỎI ở cổng U1, không tự bịa.
> Đường ống áp dụng: `saas-demo-video-studio` (quay màn hình THẬT) và/hoặc `code-rendered-video` (thuần motion; tuỳ chọn, xem README). Chọn bằng `{{MODE}}`.
> Trạng thái: template CHƯA chạy trên ca thật (30/09/2026). Chưa đo thời gian các bước mới (3 cổng, storyboard 3 phương án, khung tĩnh/cảnh).

## A. Bảng placeholder

| Placeholder | Ý nghĩa | Ví dụ / giá trị mặc định |
|---|---|---|
| `{{PRODUCT}}` | Tên sản phẩm/thương hiệu | — (bắt buộc) |
| `{{URL}}` | Website chính thức | — (bắt buộc) |
| `{{APP_URL}}` + `{{DEMO_ACCOUNT}}` | Web app + tài khoản DEMO **đã đăng nhập sẵn** trên Chrome thật (chỉ khi MODE = SCREEN/HYBRID) | — |
| `{{MODE}}` | `SCREEN` (quay màn hình thật) · `CODE` (motion thuần, không footage) · `HYBRID` | `SCREEN` cho web app/SaaS |
| `{{REF_VIDEO}}` | 1–2 video/khung ref (file hoặc link) | — ; **không có ⇒ agent dừng ở U1 và đề xuất 3 style có tên** |
| `{{STYLE_NAME}}` | Tên style của ref (gọi tên, đừng mô tả) | vd "Mercury quiet-copper", "UI-morph one-shape" — đặt tên bằng 1–2 từ mô tả; không có ref thì agent đề xuất 3 tên |
| `{{LOGO_SVG}}` | Logo **vector** (SVG) | — |
| `{{BRAND_COLORS}}` `{{BRAND_FONTS}}` | Màu + font (font phải có tiếng Việt nếu chữ VI) | — |
| `{{DURATION}}` · `{{ASPECT}}` · `{{FPS}}` | Độ dài · tỉ lệ · fps | `60 s` · `16:9` · `30` |
| `{{LANG}}` | Ngôn ngữ VO + phụ đề | `vi` |
| `{{VOICE}}` | Giọng VO (user nghe thử và chọn) | VieNeu "Hải Đăng" |
| `{{MUSIC_BPM}}` | Nhịp nhạc | `120–128`, instrumental |
| `{{PAGES_OFF_LIMITS}}` | Trang cấm quay | — |
| `{{MASK_LIST}}` | Thông tin phải che | email · role/badge admin · mục ADMIN sidebar · tên vendor/model AI · API key |
| `{{NEVER_CLICK}}` | Nút không được bấm | Lưu · Xoá · Thanh toán · Gửi |
| `{{KEY_FEATURES}}` | 3–5 chức năng, xếp theo độ "đắt", mỗi cái 1 URL | — |
| `{{CTA}}` | Lời kêu gọi + link | — |
| `{{BANNED_WORDS}}` | Từ cấm | — |

---

## B. BẢN TIẾNG ANH (English)

```
Create a polished launch video for {{PRODUCT}} ({{URL}}), using the attached video {{REF_VIDEO}} as a style
reference — the named style is "{{STYLE_NAME}}". Follow its visual and editing style: dark backgrounds, warm
lighting, bold contrasting text, animated product UI cards, smooth transitions, and cinematic pacing.
Adapt colors ({{BRAND_COLORS}}), logo ({{LOGO_SVG}}) and typography ({{BRAND_FONTS}}) to the brand.
Take the GRAMMAR of the reference (shot length, transitions, how text enters and leaves), never its content,
logos, characters or footage.

MODE: {{MODE}}.
- SCREEN: record the REAL web app ({{APP_URL}}, demo account {{DEMO_ACCOUNT}}) with the skill
  `saas-demo-video-studio`. HYBRID: add motion intros/outros with `code-rendered-video`. CODE: motion only.
- Render with HyperFrames (pinned version in the skill) — name the framework explicitly; deterministic
  seek(t) rendering; no Math.random, no timers, no CSS transitions at render time.

TRUTH FIRST
1. Research the official website first. Use only verified information and real product assets from official
   sources. Any third-party asset must be suitable for commercial use and credited in the sources list.
2. Do not invent features, statistics, prices, dates, testimonials or customer names.
3. EVERY number that appears on screen (and in the voiceover) must be read from the live app/site during a
   read-only pass and written to footage/web-data-<date>.md. If the brief and the web disagree, trust the web
   and tell me. Never round "for looks". The automated check (check_numbers) must pass.
4. Empty screens/empty states: do not record them. Replace with a text card on a blurred real screenshot.

PRIVACY (fail = stop and report)
5. Mask or avoid: {{MASK_LIST}}. Never open {{PAGES_OFF_LIMITS}}. Never click {{NEVER_CLICK}}.
   Use the demo account only; no production customer data; no API keys, tokens, or names of other AI vendors.
6. Scan the contact sheet of the raw footage for leaks before editing (privacy checklist).

FORMAT
7. {{DURATION}} seconds, {{ASPECT}}, {{FPS}} fps (state the real captured fps; do not claim 60 if the screen
   recorder gives ~29). A 9:16 version, if requested, is RECOMPOSED (split layout, centered), never cropped.

STRUCTURE (one idea per scene, concise text, clear visuals; default budget for 60 s — adjust to {{DURATION}})
 a. Attention-grabbing opening        0–5 s    (the hook lands inside the first 2 s)
 b. Customer problem                  5–15 s
 c. Product introduction              15–22 s
 d. Key features {{KEY_FEATURES}}     22–38 s  (one route, one wow element, one real number per feature)
 e. Real product demonstration        38–50 s  (real cursor path, real click, real result)
 f. Benefits                          50–56 s
 g. Logo and call to action {{CTA}}   56–60 s  (hold ≥1.5 s of stillness on the last frame)
Every scene gets a written line: goal · footage source (route) · the number that must be visible · camera
move · caption · SFX. No scene may show more than one main element on a mostly empty ground.

CAPTURE (MODE = SCREEN / HYBRID)
8. Write a capture script BEFORE recording (one shot per voiceover line: URL · steps with selectors · camera ·
   highlight · number that must be visible · areas to avoid). It must pass the G0 lint against web-data.
9. Environment gate E0 before the first shot: no other AI agent attached to Chrome; Chrome started with the
   anti-occlusion flags; the MCP tab is visible; motion gate ≥25 changed frames/s over 10 s.
10. MACRO MODE: one JavaScript macro per shot (click, type char by char at 60–90 ms, smooth scroll, body
    transform for zoom, expect_value at every step; throw on mismatch). Log every action with the element bbox
    into capture-log.jsonl; the virtual cursor, camera cues and highlight boxes are generated from that log.
    Do not keep retrying a shot for more than 5 minutes: skip it and note it.

SOUND, RHYTHM, CAPTIONS
11. Natural voiceover in {{LANG}} ({{VOICE}}), word-aligned (forced alignment, strict), numbers spoken as words.
12. Background music at {{MUSIC_BPM}} BPM, instrumental, MEASURED to a beat grid (beats.json). Cuts, camera
    moves and text entrances land on beats; SFX are tied to a specific motion (typing, pop, whoosh, chart-rise,
    logo hit) and are audibly above the music (check mono and stereo). Music sits ≥18 dB under the voice.
    Master −14 LUFS, true peak ≤ −1 dBFS, re-measured on every delivered file.
13. LIVE CAPTIONS in {{LANG}}: groups of 2–4 words by meaning, never splitting a compound word, the spoken word
    highlighted in the accent colour, always on while the voice speaks; export a matching .srt from the same timing.
14. Music and SFX must be generated or licensed for commercial use; log every source (name, URL/tool, licence).

DIRECTOR'S PROCESS — 3 USER GATES (do not pass a gate without my written YES in chat; silence is not a yes)
15. Before any code: extract 1 frame per 0.5 s of the reference, write docs/style_guide.md (palette · type ·
    shot lengths · transition types · camera moves · how text enters/exits) and docs/shotlist.md on the beat grid.
    If I gave no reference: stop, propose 3 named styles, wait.
16. GATE U1 — STORYBOARD: give me 3 storyboards (different rhythm and layout, same facts and order). I pick one.
17. GATE READY — before recording: tell me exactly what to close/stop so the machine stays still, and wait for
    my "ready".
18. Record according to the script. Then build ONE still frame per scene + a 15–20 s test scene.
19. GATE U2 — I review the stills and the test scene. I will give notes as "address + camera phrase + number",
    e.g. "shot R05 3.2 s: slow every zoom to 0.7x", "hard cut here", "push in on the button". Change only that.
20. Build. Before showing me anything: contact sheet (1 fps + a 12-frame strip around each fast move + a 360 px
    phone test), score yourself 1–10 on: hook in the first 2 s · legibility at phone size · motion quality ·
    variety · composition · brand accuracy and real numbers · sound sync. List the 3 worst problems with
    timestamps, fix them, repeat (max 3 rounds) until all scores ≥ 8. Re-render only the failing segments at 720p;
    one full 1080p render at the end.

DELIVER
21. The finished video (+ .srt), the voiceover script, the scene outline, the list of asset sources (with
    licences), web-data-<date>.md, the QA report with MEASURED values (loudness, peak, shot lengths, numbers
    check, privacy scan), the contact sheet, and a "what I would improve / known gaps" list.
    Never say "done" without the measurements attached.
```

---

## C. BẢN TIẾNG VIỆT

```
Làm một video ra mắt {{PRODUCT}} ({{URL}}) thật trau chuốt, lấy video đính kèm {{REF_VIDEO}} làm chuẩn phong cách —
style có tên là "{{STYLE_NAME}}". Theo đúng cách nhìn và cách dựng của nó: nền tối, ánh sáng ấm, chữ đậm tương phản,
thẻ UI sản phẩm chuyển động, chuyển cảnh mượt, nhịp điện ảnh. Đổi màu ({{BRAND_COLORS}}), logo ({{LOGO_SVG}}) và
kiểu chữ ({{BRAND_FONTS}}) theo thương hiệu. Chỉ lấy NGỮ PHÁP của ref (độ dài shot, kiểu chuyển cảnh, cách chữ
vào/ra), tuyệt đối không lấy nội dung, logo, nhân vật hay footage của nó.

CHẾ ĐỘ: {{MODE}}.
- SCREEN: quay MÀN HÌNH THẬT của web app ({{APP_URL}}, tài khoản demo {{DEMO_ACCOUNT}}) bằng skill
  `saas-demo-video-studio`. HYBRID: thêm phần intro/outro motion bằng `code-rendered-video`. CODE: chỉ motion.
- Render bằng HyperFrames (đúng phiên bản pin trong skill) — gọi tên framework rõ ràng; render tất định theo
  seek(t); cấm Math.random, timer, CSS transition lúc render.

SỰ THẬT TRƯỚC
1. Nghiên cứu website chính thức trước. Chỉ dùng thông tin đã kiểm chứng và tài sản thật từ nguồn chính thức.
   Tài sản bên thứ ba phải dùng được thương mại và được ghi nguồn trong danh sách nguồn.
2. Không bịa chức năng, số liệu, giá, ngày, lời chứng thực hay tên khách hàng.
3. MỌI con số hiện trên hình (và trong lời đọc) phải được đọc từ app/web đang chạy trong một lượt soát chỉ-đọc, ghi vào
   footage/web-data-<ngày>.md. Brief và web lệch nhau ⇒ tin web và báo tôi. Không làm tròn "cho đẹp".
   Cổng tự động check_numbers phải PASS.
4. Màn trống (empty state): không quay. Thay bằng thẻ chữ đặt trên ảnh chụp thật đã làm mờ.

QUYỀN RIÊNG TƯ (vi phạm = dừng và báo)
5. Che hoặc tránh: {{MASK_LIST}}. Không mở {{PAGES_OFF_LIMITS}}. Không bấm {{NEVER_CLICK}}. Chỉ dùng tài khoản demo;
   không dữ liệu khách thật; không API key/token; không tên hãng AI khác.
6. Soát contact sheet của footage thô để tìm rò rỉ TRƯỚC khi dựng (privacy checklist).

ĐỊNH DẠNG
7. {{DURATION}} giây, {{ASPECT}}, {{FPS}} fps (ghi fps quay thực tế; không ghi 60 nếu máy quay chỉ ~29).
   Bản 9:16 nếu có là bản DỰNG LẠI bố cục (chia đôi, căn giữa dọc), không crop.

CẤU TRÚC (mỗi cảnh 1 ý, chữ ngắn, hình rõ; ngân sách mặc định cho 60 s — chỉnh theo {{DURATION}})
 a. Mở đầu gây chú ý                  0–5 s    (hook phải vào trong 2 s đầu)
 b. Vấn đề của khách hàng             5–15 s
 c. Giới thiệu sản phẩm               15–22 s
 d. Chức năng chính {{KEY_FEATURES}}  22–38 s  (mỗi chức năng: 1 route · 1 phần tử "wow" · 1 con số thật)
 e. Demo sản phẩm thật                38–50 s  (đường con trỏ thật, cú bấm thật, kết quả thật)
 f. Lợi ích                           50–56 s
 g. Logo + kêu gọi hành động {{CTA}}  56–60 s  (khung cuối giữ tĩnh ≥1,5 s)
Mỗi cảnh phải có 1 dòng ghi sẵn: mục tiêu · nguồn footage (route) · con số phải thấy · chuyển động camera ·
caption · SFX. Không cảnh nào có hơn 1 phần tử chính trên nền gần trống.

QUAY (MODE = SCREEN / HYBRID)
8. Viết kịch bản quay TRƯỚC khi quay (mỗi câu VO 1 shot: URL · các bước có selector · camera · highlight · số phải
   thấy · vùng tránh). Phải qua lint G0 với web-data.
9. Cổng môi trường E0 trước shot đầu: không có agent AI khác gắn vào Chrome; Chrome chạy với cờ chống giảm vẽ khi
   bị che; tab MCP đang hiện; motion gate ≥25 khung đổi/s trong 10 s.
10. MACRO MODE: mỗi shot một lệnh JavaScript (bấm, gõ từng ký tự 60–90 ms, cuộn mượt, zoom bằng transform trên body,
    kiểm expect_value từng bước, sai thì throw). Ghi mọi thao tác + bbox phần tử vào capture-log.jsonl; con trỏ ảo,
    camera, khung highlight sinh từ log đó. Không thử lại 1 shot quá 5 phút: bỏ qua và ghi chú.

ÂM THANH, NHỊP, PHỤ ĐỀ
11. Lời đọc tự nhiên bằng {{LANG}} ({{VOICE}}), căn theo từng từ (forced alignment, strict); số đọc thành chữ.
12. Nhạc nền {{MUSIC_BPM}} BPM, không lời, ĐO ra lưới nhịp (beats.json). Cắt cảnh, chuyển động camera, chữ vào đều
    rơi trên phách; SFX gắn với 1 chuyển động cụ thể (gõ phím, pop, whoosh, chart-rise, logo hit) và nghe rõ trên nhạc
    (đo cả mono và stereo). Nhạc thấp hơn lời ≥18 dB. Master −14 LUFS, đỉnh thật ≤ −1 dBFS, đo lại trên MỌI file giao.
13. PHỤ ĐỀ TIẾNG VIỆT LIVE: cụm 2–4 từ theo nghĩa, không tách từ ghép (vd "định mức", "nhà cung cấp"), từ đang đọc đổi
    màu accent, luôn hiện khi lời đang nói; xuất .srt khớp từ cùng file timing.
14. Nhạc và SFX phải do máy sinh hoặc có giấy phép thương mại; ghi nguồn từng cái (tên, URL/công cụ, giấy phép).

QUY TRÌNH ĐẠO DIỄN — 3 CỔNG USER (không qua cổng nếu chưa có chữ "OK" của tôi trong chat; im lặng KHÔNG phải đồng ý)
15. Trước khi viết code: trích 1 khung/0,5 s của ref, viết docs/style_guide.md (bảng màu · chữ · độ dài shot · kiểu
    chuyển cảnh · camera · cách chữ vào/ra) và docs/shotlist.md trên lưới nhịp. Tôi không đưa ref ⇒ dừng, đề xuất
    3 style có tên, chờ tôi chọn.
16. CỔNG U1 — STORYBOARD: đưa 3 storyboard (khác nhịp và bố cục, cùng dữ kiện và thứ tự). Tôi chọn 1.
17. CỔNG SẴN SÀNG — trước khi quay: nói rõ tôi cần đóng/dừng gì để máy đứng yên, rồi chờ tôi nói "sẵn sàng".
18. Quay theo kịch bản. Sau đó dựng MỖI CẢNH 1 KHUNG TĨNH + 1 cảnh thử 15–20 s.
19. CỔNG U2 — tôi duyệt khung tĩnh + cảnh thử. Tôi ghi chú theo kiểu "địa chỉ + câu camera + con số", ví dụ
    "shot R05 3,2 s: làm chậm mọi zoom xuống 0,7×", "cắt cứng ở đây", "đẩy vào nút bấm". Chỉ sửa đúng chỗ đó.
20. Dựng. Trước khi đưa tôi xem: contact sheet (1 khung/s + dải 12 khung quanh mỗi cú chuyển động nhanh + bài test điện
    thoại rộng 360 px), tự chấm 1–10 trên: hook 2 s đầu · đọc được ở cỡ điện thoại · chất lượng chuyển động · đa dạng ·
    bố cục · đúng brand và số thật · khớp âm. Nêu 3 lỗi tệ nhất kèm timestamp, sửa, lặp (tối đa 3 vòng) đến khi mọi điểm
    ≥ 8. Chỉ render lại đoạn lỗi ở 720p; 1080p đầy đủ đúng 1 lần cuối.

BÀN GIAO
21. Video hoàn chỉnh (+ .srt), kịch bản lời đọc, dàn ý cảnh, danh sách nguồn tài sản (kèm giấy phép), web-data-<ngày>.md,
    báo cáo QA với số ĐO THẬT (loudness, đỉnh, độ dài shot, kiểm số, quét privacy), contact sheet, và danh sách
    "điều em sẽ cải thiện / còn thiếu". Không nói "xong" khi chưa kèm số đo.
```

---

## D. Đối chiếu yêu cầu gốc của user ↔ dòng trong template (để không rơi mất ý)

| Ý trong prompt gốc user | Dòng template |
|---|---|
| ref video + dark/warm/bold text/UI cards/smooth/cinematic; đổi màu-logo-chữ | mở đầu |
| Research official website first; chỉ thông tin verified + asset thật; asset bên thứ 3 thương mại + credit | 1 |
| Không bịa feature/thống kê/testimonial | 2 (+ giá/ngày/tên khách) |
| 60 s · 16:9 · 30 fps | 7 |
| Cấu trúc 7 phần (opening → … → CTA) | STRUCTURE a–g (thêm ngân sách giây — [ĐX]) |
| Voiceover tự nhiên · nhạc · SFX tinh tế · phụ đề đồng bộ | 11–14 |
| Mỗi cảnh 1 ý, chữ ngắn, hình rõ | STRUCTURE (dòng cuối) |
| Giao: video · kịch bản VO · dàn ý cảnh · nguồn asset | 21 |
| **Thêm từ ProfitBase:** số thật từ web-data | 3, 4 |
| privacy | 5, 6 |
| macro-mode + cổng E0 | 9, 10 |
| lưới nhịp | 12 |
| phụ đề tiếng Việt live | 13 |
| 3 cổng user (U1 · SẴN SÀNG = U0 của repo · U2) | 15–19 |
| **Thêm từ bài 0xMovez/rexan:** ref có TÊN, dừng chờ style_guide/storyboard, 3 storyboard, 1 khung/cảnh, ghi chú đạo diễn có địa chỉ, tự chấm ≥8, phone test 360 px | mở đầu, 15, 16, 18, 19, 20 |

Ghi chú vận hành: (1) "ngân sách giây" ở STRUCTURE là đề xuất chia theo tỉ lệ 60 s, chưa kiểm với 1 ca thật. (2) Dòng 20 dùng thang điểm lấy ý từ bài 0xMovez (mục phê bình, do ta viết lại); tối đa 3 vòng khớp luật A4b (3 vòng rồi báo user). (3) Nếu MODE = CODE thì bỏ dòng 8–10 và 3–4 chỉ áp cho số lấy từ nguồn chính thức. (4) Prompt này dài ~1,5 trang — đó là chủ ý: bài 0xMovez và repo yihui cho thấy prompt sản xuất tốt thường 2.000–16.000 ký tự; prompt 1 câu chỉ kiểm được engine, không kiểm được ý.
