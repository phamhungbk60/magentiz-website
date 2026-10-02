#!/usr/bin/env python3
"""Build the static Magentiz site (English + Vietnamese).

Renders src/pages/<lang>/*.html into public/ using src/layout.html, then
writes sitemap.xml, _headers and _redirects. Standard library only, so it
runs anywhere (locally or as a Netlify build command).

  src/pages/en/services.html  ->  public/services.html     (/services)
  src/pages/vi/services.html  ->  public/vi/services.html  (/vi/services)

Pages with the same file name in both languages are linked to each other
(hreflang tags + the EN/VI switcher). Each page starts with front matter:

    ---
    title: Page title | Magentiz
    description: Meta description.
    breadcrumb: Services
    ---
    <section>...</section>

Optional keys: og_title, priority, robots, sitemap (yes/no).
"""

import base64
import datetime
import hashlib
import html
import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
PUBLIC = ROOT / "public"

SITE = "https://www.magentiz.com"
EMAIL = "info@magentiz.com"  # TODO: confirm the real contact address

# Preview builds (e.g. GitHub Pages at /magentiz-website/) set BASE_PATH so
# root-relative links still resolve, and PREVIEW=1 to keep them out of search.
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
PREVIEW = os.environ.get("PREVIEW") == "1"
DEFAULT_LANG = "en"

THEME_SCRIPT = (
    'try{if(localStorage.getItem("theme")==="light")'
    'document.documentElement.classList.add("light")}catch(e){}'
)

# Per-language settings and the strings used by src/layout.html ({{t_*}}).
LANGS = {
    "en": {
        "prefix": "",
        "label": "EN",
        "name": "English",
        "og_locale": "en_US",
        "og_image": "og-image.png",
        "strings": {
            "skip": "Skip to content",
            "nav_label": "Main navigation",
            "home_label": "Magentiz home",
            "nav_home": "Home",
            "nav_services": "Services",
            "nav_technology": "Technology",
            "nav_about": "About",
            "nav_cta": "Get a Magento Audit",
            "theme": "Toggle light/dark mode",
            "menu": "Toggle menu",
            "lang_group": "Language",
            "footer_about": "Magento engineering team for stores that cannot afford to be slow or offline. "
                            "Build, test, ship, monitor and optimize, with AI built into how we work.",
            "f_ha": "High-Availability Magento",
            "f_dev": "A–Z Magento Development",
            "f_ai": "AI-Applied Magento Team",
            "f_perf": "Performance &amp; Caching",
            "f_obs": "Monitoring &amp; Observability",
            "f_aitools": "AI Tooling",
            "f_company": "Company",
            "f_contact": "Contact",
            "rights": "All rights reserved.",
            "crumb_home": "Home",
            "org_description": "Magento engineering team: high-availability Magento infrastructure, "
                               "end-to-end Magento development, automation testing, DevOps, monitoring "
                               "and AI-assisted delivery.",
        },
    },
    "vi": {
        "prefix": "/vi",
        "label": "VI",
        "name": "Tiếng Việt",
        "og_locale": "vi_VN",
        "og_image": "og-image-vi.png",
        "strings": {
            "skip": "Chuyển đến nội dung",
            "nav_label": "Điều hướng chính",
            "home_label": "Trang chủ Magentiz",
            "nav_home": "Trang chủ",
            "nav_services": "Dịch vụ",
            "nav_technology": "Công nghệ",
            "nav_about": "Giới thiệu",
            "nav_cta": "Đánh giá miễn phí",
            "theme": "Chuyển chế độ sáng/tối",
            "menu": "Mở menu",
            "lang_group": "Ngôn ngữ",
            "footer_about": "Đội ngũ kỹ sư Magento cho những cửa hàng không thể chậm hay ngừng hoạt động. "
                            "Phát triển, kiểm thử, triển khai, giám sát và tối ưu, với AI trong cách chúng tôi làm việc hằng ngày.",
            "f_ha": "Magento hoạt động liên tục",
            "f_dev": "Phát triển Magento trọn gói",
            "f_ai": "Đội Magento ứng dụng AI",
            "f_perf": "Hiệu năng &amp; bộ nhớ đệm",
            "f_obs": "Giám sát hệ thống",
            "f_aitools": "Công cụ trí tuệ nhân tạo",
            "f_company": "Công ty",
            "f_contact": "Liên hệ",
            "rights": "Bảo lưu mọi quyền.",
            "crumb_home": "Trang chủ",
            "org_description": "Đội ngũ kỹ sư Magento: hạ tầng Magento hoạt động liên tục, phát triển Magento "
                               "trọn gói, kiểm thử tự động, DevOps, giám sát và quy trình làm việc có AI hỗ trợ.",
        },
    },
}


def file_version(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def page_path(lang, key):
    """URL path for a page: '/', '/services', '/vi/', '/vi/services'."""
    prefix = LANGS[lang]["prefix"]
    return (prefix + "/") if key == "index" else f"{prefix}/{key}"


def page_file(lang, key):
    prefix = LANGS[lang]["prefix"].lstrip("/")
    return f"{prefix}/{key}.html" if prefix else f"{key}.html"


def parse_page(path, lang):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if line.strip():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    meta["content"] = text[m.end():].rstrip()
    meta["lang"] = lang
    meta["key"] = path.stem
    meta["path"] = page_path(lang, path.stem)
    meta["file"] = page_file(lang, path.stem)
    meta["indexable"] = meta.get("sitemap", "yes") == "yes"
    return meta


def faq_entries(content):
    """(question, answer) pairs from <details class="faq-item"> blocks, for FAQPage data."""
    pairs = []
    for q, a in re.findall(r'<details class="faq-item">\s*<summary>(.*?)</summary>\s*'
                           r'<div class="faq-answer">(.*?)</div>', content, re.S):
        clean = lambda t: html.unescape(" ".join(re.sub(r"<[^>]+>", " ", t).split()))
        pairs.append((clean(q), clean(a)))
    return pairs


def jsonld(meta):
    lang = meta["lang"]
    org = {
        "@type": "Organization",
        "@id": f"{SITE}/#organization",
        "name": "Magentiz",
        "url": f"{SITE}/",
        "logo": f"{SITE}/images/favicon-192.png",
        "email": EMAIL,
        "description": LANGS[lang]["strings"]["org_description"],
        "knowsAbout": ["Magento 2", "Adobe Commerce", "Varnish", "Redis", "OpenSearch",
                       "Kubernetes", "AWS", "New Relic", "Tideways", "Grafana", "Checkly",
                       "Selenium", "Claude", "OpenAI", "Antigravity"],
        "sameAs": ["https://github.com/magentiz"],
    }
    page = {
        "@type": "WebPage",
        "@id": SITE + meta["path"] + "#webpage",
        "url": SITE + meta["path"],
        "name": html.unescape(meta["title"]),
        "inLanguage": lang,
        "isPartOf": {"@id": f"{SITE}/#website"},
    }
    website = {
        "@type": "WebSite",
        "@id": f"{SITE}/#website",
        "url": f"{SITE}/",
        "name": "Magentiz",
        "inLanguage": list(LANGS),
        "publisher": {"@id": f"{SITE}/#organization"},
    }
    graph = [org, website, page]
    faq = faq_entries(meta["content"])
    if faq:
        graph.append({
            "@type": "FAQPage",
            "@id": SITE + meta["path"] + "#faq",
            "inLanguage": lang,
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faq
            ],
        })
    if meta["key"] != "index" and meta.get("breadcrumb"):
        home = LANGS[lang]["strings"]["crumb_home"]
        page["breadcrumb"] = {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": home, "item": SITE + page_path(lang, "index")},
                {"@type": "ListItem", "position": 2, "name": html.unescape(meta["breadcrumb"]),
                 "item": SITE + meta["path"]},
            ],
        }
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      indent=2, ensure_ascii=False)


def alternates_html(meta, siblings):
    """hreflang links, only for indexable pages that exist in more than one language."""
    if not meta["indexable"] or len(siblings) < 2:
        return ""
    links = [f'  <link rel="alternate" hreflang="{lang}" href="{SITE}{p["path"]}">'
             for lang, p in siblings.items()]
    links.append(f'  <link rel="alternate" hreflang="x-default" href="{SITE}{siblings[DEFAULT_LANG]["path"]}">')
    return "\n".join(links)


def lang_switch_html(meta, siblings):
    strings = LANGS[meta["lang"]]["strings"]
    items = []
    for lang, conf in LANGS.items():
        if lang == meta["lang"]:
            items.append(f'          <span class="lang-opt active" lang="{lang}" aria-current="true">{conf["label"]}</span>')
        else:
            # Error pages switch to the other language's home page
            target = (siblings.get(lang, {}).get("path") if meta["key"] != "404" else None) \
                or page_path(lang, "index")
            items.append(f'          <a href="{target}" class="lang-opt" hreflang="{lang}" lang="{lang}" '
                         f'aria-label="{conf["name"]}">{conf["label"]}</a>')
    return (f'        <div class="lang-switch" role="group" aria-label="{strings["lang_group"]}">\n'
            + "\n".join(items) + "\n        </div>")


def render(layout, meta, siblings, versions):
    lang = meta["lang"]
    conf = LANGS[lang]
    values = {
        "lang": lang,
        "page_key": meta["key"],
        "og_image": conf["og_image"],
        "og_locale": conf["og_locale"],
        "p": conf["prefix"],
        "home": page_path(lang, "index"),
        "title": meta["title"],
        "og_title": meta.get("og_title", meta["title"]),
        "description": meta["description"],
        "robots": "noindex, nofollow" if PREVIEW else meta.get("robots", "index, follow"),
        "canonical": SITE + meta["path"],
        "alternates": alternates_html(meta, siblings),
        "lang_switch": lang_switch_html(meta, siblings),
        "site": SITE,
        "email": EMAIL,
        "year": str(datetime.date.today().year),
        "theme_script": THEME_SCRIPT,
        "jsonld": jsonld(meta),
        "content": meta["content"].replace("{{email}}", EMAIL),
        **{f"t_{k}": v for k, v in conf["strings"].items()},
        **versions,
    }
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], layout)
    leftover = re.findall(r"\{\{\w+\}\}", out)
    if leftover:
        raise SystemExit(f"{meta['path']}: unresolved placeholders {leftover}")
    return out


def soften_heading_breaks(page_html):
    """<br> inside headings becomes ' <br class="br-lg">': a line break on wide
    screens, a plain space on phones (see .br-lg in style.css)."""
    def fix(m):
        return re.sub(r"\s*<br>\s*", ' <br class="br-lg">', m.group(0))
    return re.sub(r'<(h[1-3])\b[^>]*>.*?</\1>|<p class="contact-display-title">.*?</p>',
                  fix, page_html, flags=re.S)


def with_base_path(page_html):
    """Prefix root-relative URLs (href="/…", src="/…", srcset, form action) with BASE_PATH."""
    if not BASE_PATH:
        return page_html
    page_html = re.sub(r'((?:href|src|action)=")/(?!/)', rf"\1{BASE_PATH}/", page_html)
    return re.sub(r'(srcset="|, )/(?!/)', rf"\1{BASE_PATH}/", page_html)


def write_sitemap(groups):
    today = datetime.date.today().isoformat()
    entries = []
    for key in sorted(groups, key=lambda k: (k != "index", k)):
        siblings = {l: p for l, p in groups[key].items() if p["indexable"]}
        for lang, p in siblings.items():
            alts = ""
            if len(siblings) > 1:
                alts = "".join(
                    f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{s["path"]}"/>'
                    for l, s in siblings.items())
                alts += (f'\n    <xhtml:link rel="alternate" hreflang="x-default" '
                         f'href="{SITE}{siblings[DEFAULT_LANG]["path"]}"/>')
            entries.append(
                f"  <url>\n    <loc>{SITE}{p['path']}</loc>{alts}\n    <lastmod>{today}</lastmod>\n"
                f"    <priority>{p.get('priority', '0.7')}</priority>\n  </url>")
    (PUBLIC / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(entries) + "\n</urlset>\n", encoding="utf-8")


def write_redirects(pages):
    """Canonical URLs have no .html extension; old-style links get a 301.
    Forced (!) so the existing .html files don't shadow the rule."""
    lines = ["# Generated by build.py. Do not edit by hand."]
    for p in sorted(pages, key=lambda p: p["file"]):
        if p["key"] == "404":
            continue
        lines.append(f'/{p["file"]:<24} {p["path"]:<16} 301!')
    # Language-specific 404 pages. Explicit 200 rewrites first so the real
    # pages never fall through to the catch-all, which must come last.
    for lang, conf in LANGS.items():
        if not conf["prefix"]:
            continue
        for p in sorted(pages, key=lambda p: p["file"]):
            if p["lang"] == lang and p["key"] not in ("index", "404"):
                lines.append(f'{p["path"]:<24} /{p["file"]:<16} 200')
        lines.append(f'{conf["prefix"] + "/*":<24} /{conf["prefix"].lstrip("/")}/404.html  404')
    (PUBLIC / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_robots(pages):
    (PUBLIC / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")


def write_headers():
    script_hash = base64.b64encode(hashlib.sha256(THEME_SCRIPT.encode()).digest()).decode()
    csp = "; ".join([
        "default-src 'self'",
        f"script-src 'self' 'sha256-{script_hash}'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "object-src 'none'",
    ])
    (PUBLIC / "_headers").write_text(f"""/*
  Content-Security-Policy: {csp}
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains

/fonts/*
  Cache-Control: public, max-age=31536000, immutable
""", encoding="utf-8")


def main():
    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    versions = {
        "css_version": file_version(PUBLIC / "css" / "style.css"),
        "js_version": file_version(PUBLIC / "js" / "main.js"),
    }

    pages = [parse_page(f, lang)
             for lang in LANGS
             for f in sorted((SRC / "pages" / lang).glob("*.html"))]
    groups = {}
    for p in pages:
        groups.setdefault(p["key"], {})[p["lang"]] = p

    for p in pages:
        out = PUBLIC / p["file"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(with_base_path(soften_heading_breaks(render(layout, p, groups[p["key"]], versions))), encoding="utf-8")
        print(f"built {out.relative_to(ROOT)}")

    for key, siblings in groups.items():
        missing = set(LANGS) - set(siblings)
        if missing:
            print(f"warning: '{key}' has no {', '.join(sorted(missing))} version")

    write_sitemap(groups)
    write_redirects(pages)
    write_robots(pages)
    write_headers()
    print("built public/sitemap.xml, _redirects, robots.txt, _headers")


if __name__ == "__main__":
    main()
