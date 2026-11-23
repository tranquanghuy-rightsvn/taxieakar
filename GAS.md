# GAS.md — Guideline CMS Xe Taxi Eakar

> Nguồn quyết định CHỐT cho toàn bộ `gas/`. Đọc TOÀN BỘ file này trước khi sửa bất kỳ dòng
> nào trong `gas/Code.js`, `gas/app.html`, `gas/js.html`, `gas/css.html`, `gas/index.html`,
> `gas/email.html`. Không tự suy đoán thêm field/quy tắc nào không có ở đây.
>
> Theo playbook skill `free-cms-static-site-pipeline`, copy từ dự án `taxigocong` (23/11/2026).
> Sửa code xong phải đồng bộ ngược lại file này trong CÙNG một lượt sửa.

## 0. Phạm vi — ĐÚNG 4 tab quản lý, không làm rộng hơn

| Tab | Nguồn dữ liệu | Quyền tối thiểu |
|---|---|---|
| 1. Đặt xe | Sheet `Bookings` (widget Đặt xe nhanh + popup ghi vào) | `admin` |
| 2. Đăng ký tư vấn | Sheet `Contacts` (form "Đăng ký nhận tư vấn" ghi vào) | `admin` |
| 3. Tin tức | GitHub `data/posts.json` + `data/blog/<slug>.json` | `editor` |
| 4. Người dùng | Sheet `Users` | `admin` |

Đặt xe và Đăng ký tư vấn là **dữ liệu khách hàng** → `editor` cố ý KHÔNG thấy 2 tab này.

Domain thật: **https://taxieakar.com.vn**. Trang quản trị: **https://taxieakar.com.vn/admin/**.

## I. Đăng nhập

1. Luồng: nhập email → nhận OTP qua email → xác nhận → vào Admin. Không mật khẩu.
2. Chỉ email đã có trong sheet `Users` mới được gửi OTP.
3. **Account chủ script (người deploy) LUÔN hợp lệ và LUÔN là `root`** — không cần khai trong
   `Users`, không hiện trong UI quản lý người dùng (`ownerEmail_()`).
4. **Phân quyền 3 cấp: `root` > `admin` > `editor`**:
   - `editor` — chỉ tab **Tin tức**.
   - `admin` — thêm **Đặt xe**, **Đăng ký tư vấn**, **Người dùng** (quản lý được `admin`+`editor`).
   - `root` — chủ script, toàn quyền. Chỉ set được bằng cách sửa tay Sheet `Users`.
5. OTP sống **10 phút**, cooldown **60 giây**/email, tối đa **5 lần** nhập sai. Token phiên sống
   **30 ngày**, lưu `localStorage`.
6. Server luôn `requireRole_` ở MỌI hàm. Ẩn nút/tab trên giao diện KHÔNG phải là bảo mật.

## II. Tin tức (bài viết)

1. **Field có ô nhập:** Tiêu đề (bắt buộc), URL/slug (tự sinh, bất biến sau lần Lưu đầu),
   Danh mục (danh sách cố định II.5, để trống được), Mô tả ngắn, Ảnh bìa (bắt buộc), Nội dung
   (TinyMCE: heading, bold/italic, list, link, bảng, blockquote, **chèn ảnh**).
2. **Chèn ảnh trong nội dung**: nút `quickimage` mở thẳng file picker, chọn nhiều ảnh. alt =
   caption, rơi về tiêu đề nếu caption rỗng/placeholder. Lúc Lưu xoá `<figcaption>` placeholder.
3. **Server tự suy lúc Lưu:** `seo_title` = `"<Tiêu đề> - Xe Taxi Eakar"`, `breadcrumb` = tiêu
   đề, `cover` = `"<slug>-cover.jpg"` (kiểm tra file đã có trên GitHub), `cover_alt` = tiêu đề,
   `date` = ngày Lưu lần đầu (giữ nguyên khi sửa), `updated_at` = thời điểm Lưu (UTC ISO).
4. Danh sách trong Admin đọc qua GitHub Contents API (`data/posts.json`).
5. **Danh mục CỐ ĐỊNH** — PHẢI khớp y hệt `POST_CATEGORIES` trong `gas/Code.js` VÀ
   `scripts/build.py` (sửa 1 bên phải sửa bên kia):
   - `Cẩm nang du lịch` → `/tin-tuc/danh-muc/cam-nang-du-lich/`
   - `Kinh nghiệm đi lại` → `/tin-tuc/danh-muc/kinh-nghiem-di-lai/`
   - `Bảng giá` → `/tin-tuc/danh-muc/bang-gia/`
   - `Tin tức` → `/tin-tuc/danh-muc/tin-tuc/`
6. **Ảnh:** nén client bằng `<canvas>` (cạnh dài ≤ **1600px**, JPEG **0.85**), đẩy **thẳng lên
   GitHub** ngay khi chọn. Tên tất định theo slug:
   - ảnh bìa: `html/assets/images/blog/<slug>-cover.jpg`
   - ảnh nội dung: `html/assets/images/blog/<slug>-content-<N>.jpg` (đánh số bất biến)
7. Đường dẫn ảnh trong `content_html` là **tuyệt đối** (`/assets/images/blog/...`).
8. URL công khai của bài: **`/tin-tuc/<slug>/`**.

## III. Sửa bài viết

- Slug bất biến sau lần Lưu đầu — chặn ở server (`savePost`) và client (`disabled`, nhớ bật lại
  khi mở form tạo mới). Muốn đổi URL: xoá bài, tạo bài mới.
- Ảnh khi sửa hiển thị qua `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>`.

## IV. Xoá bài viết

- Xoá đủ trong 1 thao tác: `data/blog/<slug>.json` + ảnh bìa + mọi `<slug>-content-*` + gỡ khỏi
  `data/posts.json` (ghi SAU CÙNG). Bắt buộc modal xác nhận.
- `scripts/build.py` tự xoá thư mục `html/tin-tuc/<slug>/` mồ côi.

## V. Form công khai 1 — Đăng ký nhận tư vấn (`#dangkyForm`)

Có ở: `/`, `/gia-dich-vu/`, `/lien-he/`, `/di-noi-thanh/`, `/di-cac-tinh/`,
`/dua-don-san-bay/`, `/hop-dong-du-lich-tron-goi/`.

- Field HTML: `full_name`, `phone_number`, `address` → gửi lên `name`, `phone`, `address`.
- Bắt buộc: `name` + `phone` (SĐT VN hợp lệ). `address` tuỳ chọn.
- `formType: "contact"`, `source` = thư mục đầu của URL (mục IX `SOURCE_LABELS`).
- Honeypot `_hp` (ẩn bằng `.hp-field` trong `html/style.css` — **hỏng thì hỏng IM LẶNG**, sau mọi
  lần sửa CSS kiểm `grep -c hp-field html/style.css` khác 0). Rate-limit **20 giây**/SĐT.
- **CÓ gửi email báo** về `NOTIFY_EMAIL`. Tiêu đề `[Tư vấn] <Họ tên> - <SĐT>`.
- Gửi qua `fetch()` với `Content-Type: text/plain;charset=utf-8` (né CORS preflight).
- Code: `html/forms.js`.

## VI. Form công khai 2 — Đặt xe

Widget "ĐẶT XE NHANH" (`#quickBookingForm`) ở `/` + 4 trang dịch vụ. **Chốt 23/11/2026:** widget
CHỈ có Điểm đón / Điểm đến / Thời gian. Bấm "ĐẶT XE NGAY" → mở **popup "Xác nhận đặt xe"** hỏi
**Họ tên + Số điện thoại** (kèm tóm tắt hành trình) → bấm "XÁC NHẬN ĐẶT XE" mới gửi đơn hoàn chỉnh.

- Field gửi: `name` (bắt buộc), `phone` (bắt buộc), `pickup`, `dropoff`, `pickup_time`
  (`datetime-local`), `source`. `formType: "booking"`.
- Lỗi nhập liệu / lỗi server hiện NGAY TRONG popup (không đóng popup, khách khỏi nhập lại).
  Thành công → đóng popup, reset widget, hiện popup kết quả.
- Honeypot `_hp` (trong popup) + rate-limit **20 giây**/SĐT. **LockService** khi ghi Sheet.
- **CÓ gửi email báo**, tiêu đề `[Đặt xe] <Họ tên> - <SĐT>`.

### VI-A. Trạng thái bản ghi

- `Bookings.status`: `Mới` → `Đã xác nhận` → `Hoàn thành`, hoặc `Huỷ`.
- `Contacts.status`: `Mới` → `Đã xử lý`.
- Server kiểm giá trị nằm trong enum.

## VII. UX chung trong Admin

- 2 loại pop-up riêng: **Xác nhận** (Huỷ/Đồng ý, trước khi xoá) và **Thông báo kết quả** (1 nút
  Đóng, không tự ẩn). Không `alert()`/`confirm()` native.
- Mọi nút async: `disabled` + spinner, phục hồi trong `finally`.
- Sau Lưu/Xoá: quay về danh sách của chính entity đó, cập nhật ngay. Mutation tin tức kèm ghi
  chú *"Website sẽ được cập nhật sau 1-2 phút!"*.
- Chuyển tab chỉ ẩn/hiện; mỗi tab cache trong **localStorage** (stale-while-revalidate).
- Key localStorage (trừ token) mang hậu tố phiên bản client băm từ `app.html` + `js.html`
  (`clientBuild_()`). Tiền tố `tea_cms_`.
- TinyMCE chỉ `init` SAU KHI tab chứa nó đã hiện. TinyMCE **tự host** ở
  `html/vendor/tinymce/` (nạp từ `https://taxieakar.com.vn/vendor/tinymce/tinymce.min.js`).
- Không `.catch(() => {})` — luôn `console.warn`/`console.error`.

## VIII. Email thông báo — `gas/email.html`

- 1 template cho cả Đặt xe và Đăng ký tư vấn. Nhận diện bằng chữ `Taxieakar.com.vn`, màu
  `#0745be`, layout `<table>`, CSS inline. Có nút **"Gọi lại ngay"** (`tel:`).
- Gửi `htmlBody` + `body` (text thuần).
- Gửi mail lỗi/thiếu cấu hình **TUYỆT ĐỐI không làm hỏng việc đã lưu bản ghi** (try/catch).
- ⚠️ Quota **100 mail/ngày**, dùng CHUNG với OTP đăng nhập.

## IX. Kiến trúc lưu trữ

### Google Sheet `Taxi Eakar CMS Data` (code tự tạo lần đầu, tự lưu `SPREADSHEET_ID`)

- `Users` — `email`, `role`
- `Bookings` — `id`, `created_at`, `name`, `phone`, `pickup`, `dropoff`, `pickup_time`, `source`, `status`
- `Contacts` — `id`, `created_at`, `name`, `phone`, `address`, `source`, `status`

`source` ∈ `trang-chu` | `gia-dich-vu` | `di-noi-thanh` | `di-cac-tinh` | `dua-don-san-bay` |
`hop-dong-du-lich-tron-goi` | `lien-he` | `tin-tuc` | `khac` (giá trị lạ → `khac`). PHẢI khớp
`SOURCE_LABELS` trong `gas/Code.js` và `gas/js.html`.

**KHÔNG bao giờ đẩy `Bookings`/`Contacts` lên GitHub.** Thêm cột mới: đặt ở CUỐI.

### GitHub (`tranquanghuy-rightsvn/taxieakar`, branch `master`)

| Đường dẫn | Vai trò |
|---|---|
| `data/posts.json` | index nhẹ — **commit CHỐT, trigger CI**, luôn ghi SAU CÙNG |
| `data/blog/<slug>.json` | nội dung đầy đủ 1 bài |
| `html/assets/images/blog/<slug>-cover.jpg` | ảnh bìa |
| `html/assets/images/blog/<slug>-content-<N>.jpg` | ảnh trong nội dung |

### Pipeline build

| File | Vai trò |
|---|---|
| `templates/layout.html` | Khung trang Tin tức (header/footer copy từ `/gioi-thieu/`) — **sửa tay** |
| `scripts/build.py` | data/ + template → `html/tin-tuc/**` + mục `/tin-tuc/` trong `html/sitemap.xml` |
| `.github/workflows/build.yml` | CI: trigger khi `data/posts.json` / `templates/**` / `scripts/build.py` đổi |
| `scripts/check_gas_client.mjs` | Chạy thử `gas/js.html` bằng DOM giả trước khi `clasp push` |

- `html/tin-tuc/**` do CI ghi đè — **không sửa tay**.
- Chưa có bài: `/tin-tuc/` vẫn sinh (menu trỏ vào) nhưng `noindex` và không vào sitemap.
- Chỉ sinh trang chuyên mục CÓ bài. Bài/chuyên mục bị xoá thì thư mục bị dọn.
- Sitemap: giữ nguyên mục trang tĩnh viết tay, chỉ sinh lại mục `/tin-tuc/`.
- `html/admin/index.html` là file tĩnh sửa tay, `noindex` (+ `_headers`), không vào sitemap.

Độ trễ từ lúc Lưu tới lúc thấy trên site: ~1–2 phút (CI build + deploy).

## X. Cấu hình (Script Properties)

| Biến | Bắt buộc | Ghi chú |
|---|---|---|
| `GITHUB_TOKEN` | ✅ | PAT `contents:write` trên repo `taxieakar` — **phải điền tay**, không có mặc định |
| `GITHUB_OWNER` | ⬜ | Mặc định trong code: `tranquanghuy-rightsvn` |
| `GITHUB_REPO` | ⬜ | Mặc định trong code: `taxieakar` |
| `GITHUB_BRANCH` | ⬜ | Mặc định trong code: `master` |
| `NOTIFY_EMAIL` | ⬜ | Mặc định trong code: `abcsok085437331@gmail.com` (chốt 23/11/2026) |
| `SPREADSHEET_ID` | ⬜ | **KHÔNG tự điền** — code tự tạo Sheet lần đầu và tự lưu |

Giá trị không bí mật có mặc định ở `CFG_DEFAULTS` (Code.js, chỉ chạy server — không xuống trình
duyệt); Script Property cùng tên vẫn được ưu tiên nếu điền. `SPREADSHEET_ID` đã có mà mở thất bại
→ throw lỗi rõ ràng, KHÔNG tự tạo mới.

## XI. Giấu hạ tầng khỏi người dùng cuối

Không nhắc Sheet/Drive/Apps Script/GitHub trong chuỗi nào gửi xuống trình duyệt (kể cả comment
trong `app.html`/`js.html`/`index.html`/`css.html` và thông báo lỗi `throw` từ `Code.js`).

```bash
grep -niE 'sheet|spreadsheet|drive|apps script|github' gas/app.html gas/js.html gas/index.html gas/css.html
```

Ngoại lệ DUY NHẤT: `gas/js.html` hàm `repoRawUrl_` (URL `raw.githubusercontent.com` để xem ảnh vừa
tải lên trước khi CI deploy xong — ràng buộc chức năng).

## XII. Deploy

- Script ID: `1fLYxOcpfzAb-f36VXID79Fp9i4Q0aWrGdhbT0NAc_SAp5UQUgzv5uabB` (`gas/.clasp.json`).
- Web app `/exec` (deployment cố định, dán ở `html/admin/index.html` + `html/forms.js`):
  `https://script.google.com/macros/s/AKfycbzwzz_Iqlxki0UAy6MI5FEE2AIVyR3ccKNru5Kw1BSQQrs3Tv0-aew9IY2Py6wN6sg6pA/exec`
- Cập nhật code: `node scripts/check_gas_client.mjs && cd gas && clasp push -f && clasp create-deployment -i <deploymentId>`
  (clasp 3.x; deploymentId = đoạn `AKfycb…` trong URL). **Không** tạo deployment mới không có `-i` — sẽ đổi URL `/exec`.
- `gas/.claspignore` chỉ cho push `Code.js`, `*.html`, `appsscript.json` (README không lên).
- **Lần đầu (bắt buộc, làm tay trong trình soạn Apps Script):** chọn hàm `setup` → Run → cấp quyền.
  Chưa làm thì `/exec` trả "Truy cập bị từ chối" cho mọi người và form công khai không gửi được.
  `setup()` tự tạo kho dữ liệu, in ra email root, mail nhận báo, và kiểm tra `GITHUB_TOKEN`.

## XIII. Bug đã gặp ở chính dự án này

*(cập nhật dần khi thực sự gặp)*

- *(chưa có)*
