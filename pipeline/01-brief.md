# 01 · Brief (phiên chính, ~5 phút)

**Input:** prompt người dùng (`PROMPT.md`), URL app.

**Làm:** điền `brief.md` theo `.claude/skills/saas-demo-video-studio/templates/brief-template.md`: loại video A–E, độ dài,
3–5 chức năng đắt nhất + URL, trang cấm, được tạo dữ liệu demo không, giọng, màu, CTA, nhạc, đầu ra. Thiếu gì → hỏi **1 lượt duy nhất**.
Lên PLAN 6 mục (mục tiêu · lộ trình · phân công agent · SOP · KPI · cách nộp) và tạo thư mục dự án (SKILL.md §6):

```bash
mkdir -p <project>/footage <project>/vo <project>/storyboard <project>/deliver
cp -r engine <project>/comp          # = paths.comp_dir trong project.json
cp scripts/project.example.json <project>/project.json      # sửa tên + đường dẫn
```

**Output:** `brief.md`, `project.json`, plan.

**Cổng:** người dùng trả lời tối đa 1 lượt câu hỏi; mọi câu có mặc định.
