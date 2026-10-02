# magentiz.com

Static marketing site for Magentiz (www.magentiz.com): HTML, CSS and vanilla JS with no runtime dependencies.

## Structure

```
src/layout.html      shared <head>, navbar and footer
src/pages/en/*.html  English pages  → /, /services, …
src/pages/vi/*.html  Vietnamese pages → /vi/, /vi/services, …
public/              deployable site (generated HTML + css/js/images/fonts)
build.py             renders src/ into public/, writes sitemap.xml and _headers
netlify.toml         publishes public/ only
```

## Languages (EN / VI)

- A page with the same file name in `en/` and `vi/` is automatically linked: hreflang tags,
  the EN/VI switcher in the navbar and alternates in `sitemap.xml`.
- Navbar/footer text for each language lives in `LANGS` in `build.py`.
- Links inside Vietnamese pages must use the `/vi/` prefix (e.g. `/vi/contact`).
- Both contact forms post to the same Netlify form (`contact`); the hidden `lang` field shows which version was used.
- Adding a language: add an entry to `LANGS`, create `src/pages/<lang>/` and add its font subset if needed.

## Edit and build

1. Edit a page in `src/pages/en/` or `src/pages/vi/` (or the shared layout in `src/layout.html`).
2. Run `python3 build.py` (Python 3 standard library only).
3. Preview with `npx serve public`. It supports the clean URLs like `/services`.

Commit the regenerated files in `public/` too. Netlify also runs `build.py` on deploy.

Styles live in `public/css/style.css`, scripts in `public/js/main.js`. The build adds a
content hash to their URLs, so browsers pick up changes right away.

## Preview (GitHub Pages)

`./deploy-preview.sh` builds with `BASE_PATH=/<repo>` and `PREVIEW=1` (all pages
`noindex`) and force-pushes the result to the `gh-pages` branch, which GitHub Pages
serves at `https://<user>.github.io/<repo>/`. Run it after committing to update the
preview. The contact form only works on Netlify.

## Deploy (Netlify)

- Connect the repo. The publish directory and build command come from `netlify.toml`.
- Add `www.magentiz.com` as the primary domain and `magentiz.com` as an alias, which redirects to www.
- Contact form submissions: Netlify dashboard → Forms → `contact`. Add an email notification there.

## Vietnamese glossary

Use these terms consistently on `/vi/` pages. Keep product names (Magento, Varnish, AWS…),
common acronyms (API, SEO, KPI, B2B, CI/CD) and "DevOps" as they are.
Use a decimal comma in Vietnamese (99,9% · 0,4 ms).

| English | Tiếng Việt |
|---|---|
| audit | đánh giá |
| high availability | hoạt động liên tục |
| cache / full-page cache | bộ nhớ đệm / bộ nhớ đệm toàn trang |
| session | phiên làm việc |
| checkout | thanh toán |
| catalog | danh mục sản phẩm |
| production | cửa hàng thật / môi trường thật |
| staging | môi trường kiểm thử |
| deploy / release | cập nhật / phát hành |
| zero downtime | không gián đoạn |
| failover | chuyển đổi dự phòng |
| rollback | quay lại phiên bản cũ |
| load test | kiểm thử tải |
| end-to-end test | kiểm thử toàn luồng |
| synthetic monitoring | giám sát mô phỏng người dùng |
| profiling | phân tích hiệu năng |
| code / codebase | mã nguồn |
| code review | rà soát mã nguồn |
| extension / module / theme | tiện ích mở rộng / mô-đun / giao diện |
| dashboard | bảng theo dõi |
| database | cơ sở dữ liệu |
| cloud | đám mây |
| AI agent | trợ lý AI tự động |
