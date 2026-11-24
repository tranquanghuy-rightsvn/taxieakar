#!/usr/bin/env python3
"""Build trang Tin tức tĩnh từ data/ + templates/layout.html.

    python3 scripts/build.py

Sinh ra (CI chạy tự động mỗi khi trang quản trị Lưu/Xoá bài - .github/workflows/build.yml):
  html/tin-tuc/index.html                   danh sách tất cả bài
  html/tin-tuc/<slug>/index.html            trang chi tiết từng bài
  html/tin-tuc/danh-muc/<slug>/index.html   trang chuyên mục (chỉ chuyên mục CÓ bài)
  html/sitemap.xml                          giữ nguyên mục của trang tĩnh, sinh lại mục /tin-tuc/

Bài Smart content (thân bài thiết kế bằng HTML/CSS, không qua trình soạn thảo của trang quản trị):
  content/tin-tuc/<slug>.html = khối <!-- smart-content ... --> (title, description, cover, cover_alt,
  category, date, updated) + thân bài. Gộp chung danh sách với bài thường; trùng slug thì Smart
  content thắng. CSS/JS khối (html/assets/css|js/) chỉ nạp vào trang bài có dùng khối đó.

Mọi file trong html/tin-tuc/ là SẢN PHẨM BUILD - không sửa tay (sửa templates/, data/ hoặc content/).
Build phải idempotent: chạy 2 lần liên tiếp ra y hệt (CI kiểm tra).
"""
import html as html_mod
import json
import os
import re
import shutil

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HTML = os.path.join(ROOT, "html")
DATA = os.path.join(ROOT, "data")
TEMPLATES = os.path.join(ROOT, "templates")
CONTENT = os.path.join(ROOT, "content", "tin-tuc")
OUT = os.path.join(HTML, "tin-tuc")

SITE = "https://taxieakar.com.vn"
SITE_NAME = "Xe Taxi Eakar"
TITLE_SUFFIX = " - Xe Taxi Eakar"
DEFAULT_IMAGE = SITE + "/assets/images/pagea-hero-banner.jpg"
LIST_DESCRIPTION = (
    "Tin tức, cẩm nang du lịch và kinh nghiệm đi lại tại Ea Kar, Đắk Lắk từ Xe Taxi Eakar. "
    "Hotline 0856 713 714."
)

# PHẢI KHỚP y hệt hằng POST_CATEGORIES trong gas/Code.js. gas/ không nằm trong git nên 2 chỗ
# này KHÔNG tự đồng bộ được — sửa 1 bên thì sửa luôn bên kia (GAS.md mục II.5).
POST_CATEGORIES = [
    "Cẩm nang du lịch",
    "Kinh nghiệm đi lại",
    "Bảng giá",
    "Tin tức",
]

CATEGORY_SLUGS = {
    "Cẩm nang du lịch": "cam-nang-du-lich",
    "Kinh nghiệm đi lại": "kinh-nghiem-di-lai",
    "Bảng giá": "bang-gia",
    "Tin tức": "tin-tuc",
}

BLOG_IMAGE_PUBLIC = "/assets/images/blog/"

# (mẫu class trong thân bài, CSS, JS) - khối nào có trong bài thì mới nạp file của khối đó.
BLOCK_ASSETS = [
    (r'class="[^"]*\btv-', ["/assets/css/blocks.css"], []),
    (r'class="[^"]*\btv-process', ["/assets/css/process.css"], ["/assets/js/blocks.js"]),
    (r'class="[^"]*\btv-(gallery|video|plan|proof)', [], ["/assets/js/media.js"]),
]
SMART_FIELDS = ("title", "description", "cover", "cover_alt", "category", "date", "updated")


def esc(s):
    return html_mod.escape(str(s if s is not None else ""), quote=True)


def load_json(rel, default):
    path = os.path.join(DATA, rel)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_template(name):
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
        return fh.read()


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def cover_url(post):
    c = str(post.get("cover") or "")
    if not c:
        return ""
    return c if c.startswith("/") else BLOG_IMAGE_PUBLIC + c


def date_vn(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return "%s/%s/%s" % (m.group(3), m.group(2), m.group(1)) if m else str(iso or "")


def post_url(slug):
    return "/tin-tuc/%s/" % slug


def category_url(cat):
    return "/tin-tuc/danh-muc/%s/" % CATEGORY_SLUGS[cat]


def load_smart():
    """Đọc content/tin-tuc/*.html -> {slug: bài}. Khối thông tin là các dòng "khoá: giá trị"."""
    out = {}
    if not os.path.isdir(CONTENT):
        return out
    for name in sorted(os.listdir(CONTENT)):
        if not name.endswith(".html"):
            continue
        with open(os.path.join(CONTENT, name), encoding="utf-8") as fh:
            raw = fh.read()
        m = re.match(r"\s*<!--\s*smart-content\s*\n(.*?)-->\n?", raw, re.S)
        if not m:
            raise SystemExit("content/tin-tuc/%s thiếu khối <!-- smart-content ... --> ở đầu file" % name)
        post = {"slug": name[:-5], "smart": True, "content_html": raw[m.end():].rstrip("\n")}
        for line in m.group(1).splitlines():
            key, sep, val = line.partition(":")
            if sep and key.strip() in SMART_FIELDS:
                post[key.strip()] = val.strip()
        if not post.get("title"):
            raise SystemExit("content/tin-tuc/%s thiếu title" % name)
        if post.get("updated"):
            post["updated_at"] = post["updated"]
        out[post["slug"]] = post
    return out


def all_posts():
    smart = load_smart()
    posts = [dict(p) for p in load_json("posts.json", []) if p["slug"] not in smart]
    posts += list(smart.values())
    # Mới nhất trước; cùng ngày thì theo slug để thứ tự ổn định giữa các lần build.
    posts.sort(key=lambda p: (str(p.get("date", "")), p["slug"]), reverse=True)
    return posts


def used_categories(posts):
    """Chỉ chuyên mục THẬT SỰ có bài mới sinh trang — không đẻ trang rỗng."""
    have = {str(p.get("category") or "") for p in posts}
    return [c for c in POST_CATEGORIES if c in have]


# ------------------------------------------------------------------ <head>

def ld_json(graph):
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    # "</" trong chuỗi JSON sẽ đóng nhầm thẻ <script>.
    return data.replace("</", "<\\/")


def breadcrumb_ld(url, items):
    """items: [(nhãn, đường dẫn)] không gồm Trang chủ."""
    elements = [{"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": SITE + "/"}]
    for i, (label, href) in enumerate(items, start=2):
        elements.append({"@type": "ListItem", "position": i, "name": label, "item": SITE + href})
    return {"@type": "BreadcrumbList", "@id": SITE + url + "#breadcrumb", "itemListElement": elements}


def render_head(title, description, url, image, graph, og_type="website", index=True, extra_css=()):
    full = SITE + url
    robots = "index, follow, max-image-preview:large" if index else "noindex, follow"
    lines = [
        '  <meta charset="UTF-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "  <title>%s</title>" % esc(title),
        '  <meta name="description" content="%s">' % esc(description),
        '  <link rel="canonical" href="%s">' % esc(full),
        '  <meta name="robots" content="%s">' % robots,
        '  <meta property="og:type" content="%s">' % og_type,
        '  <meta property="og:locale" content="vi_VN">',
        '  <meta property="og:site_name" content="%s">' % SITE_NAME,
        '  <meta property="og:title" content="%s">' % esc(title),
        '  <meta property="og:description" content="%s">' % esc(description),
        '  <meta property="og:url" content="%s">' % esc(full),
        '  <meta property="og:image" content="%s">' % esc(image),
        '  <meta name="twitter:card" content="summary_large_image">',
        '  <meta name="twitter:title" content="%s">' % esc(title),
        '  <meta name="twitter:description" content="%s">' % esc(description),
        '  <meta name="twitter:image" content="%s">' % esc(image),
        '  <script type="application/ld+json">',
        ld_json(graph),
        "  </script>",
        '  <link rel="icon" href="/assets/icons/favicon.ico" sizes="any">',
        '  <link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/favicon-32x32.png">',
        '  <link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/favicon-16x16.png">',
        '  <link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">',
        '  <link rel="stylesheet" href="/style.css">',
    ]
    lines += ['  <link rel="stylesheet" href="%s">' % esc(c) for c in extra_css]
    return "\n".join(lines)


BUSINESS_REF = {"@id": SITE + "/#business"}
WEBSITE_REF = {"@id": SITE + "/#website"}


# ------------------------------------------------------------------ render nhỏ

def render_banner(heading, crumbs):
    """crumbs: [(nhãn, href hoặc None)] không gồm Trang chủ; phần tử cuối là trang hiện tại."""
    parts = ['          <a href="/">Trang chủ</a>']
    for label, href in crumbs:
        parts.append("          <span>/</span>")
        if href:
            parts.append('          <a href="%s">%s</a>' % (esc(href), esc(label)))
        else:
            parts.append("          <span>%s</span>" % esc(label))
    return (
        '    <section class="page-banner">\n'
        '      <div class="page-banner-inner">\n'
        "        <h1>%s</h1>\n"
        '        <nav class="breadcrumb" aria-label="breadcrumb">\n'
        "%s\n"
        "        </nav>\n"
        "      </div>\n"
        "    </section>" % (esc(heading), "\n".join(parts))
    )


def render_card(post):
    url = post_url(post["slug"])
    cat = post.get("category") or ""
    meta = '<span class="news-card-date">%s</span>' % esc(date_vn(post.get("date")))
    if cat:
        meta += ' <span class="news-card-cat">%s</span>' % esc(cat)
    return (
        '            <article class="news-card">\n'
        '              <a href="%s" class="news-card-thumb">\n'
        '                <img src="%s" alt="%s" loading="lazy">\n'
        "              </a>\n"
        '              <div class="news-card-body">\n'
        '                <div class="news-card-meta">%s</div>\n'
        '                <h2 class="news-card-title"><a href="%s">%s</a></h2>\n'
        '                <p class="news-card-desc">%s</p>\n'
        '                <a href="%s" class="news-card-more">Xem chi tiết</a>\n'
        "              </div>\n"
        "            </article>"
        % (esc(url), esc(cover_url(post)), esc(post.get("cover_alt") or post["title"]), meta,
           esc(url), esc(post["title"]), esc(post.get("description", "")), esc(url))
    )


def render_sidebar(posts, active_cat=None, current_slug=None):
    cats = used_categories(posts)
    out = ['          <aside class="news-sidebar">']
    if cats:
        items = []
        for cat in cats:
            cls = ' class="active"' if cat == active_cat else ""
            n = len([p for p in posts if p.get("category") == cat])
            items.append('                <li><a href="%s"%s>%s <span>(%d)</span></a></li>'
                         % (esc(category_url(cat)), cls, esc(cat), n))
        out.append(
            '            <div class="news-sidebar-card">\n'
            '              <h3 class="news-sidebar-title">Chuyên mục</h3>\n'
            '              <ul class="news-category-list">\n'
            '                <li><a href="/tin-tuc/"%s>Tất cả bài viết <span>(%d)</span></a></li>\n'
            "%s\n"
            "              </ul>\n"
            "            </div>"
            % ("" if (active_cat or current_slug) else ' class="active"', len(posts), "\n".join(items))
        )
    recent = [p for p in posts if p["slug"] != current_slug][:5]
    if recent:
        items = []
        for p in recent:
            items.append(
                '                <li>\n'
                '                  <a href="%s" class="news-recent-item">\n'
                '                    <span class="news-recent-thumb"><img src="%s" alt="%s" loading="lazy"></span>\n'
                '                    <span class="news-recent-text">%s<small>%s</small></span>\n'
                "                  </a>\n"
                "                </li>"
                % (esc(post_url(p["slug"])), esc(cover_url(p)), esc(p.get("cover_alt") or p["title"]),
                   esc(p["title"]), esc(date_vn(p.get("date"))))
            )
        out.append(
            '            <div class="news-sidebar-card">\n'
            '              <h3 class="news-sidebar-title">Bài viết mới</h3>\n'
            '              <ul class="news-recent-list">\n'
            "%s\n"
            "              </ul>\n"
            "            </div>" % "\n".join(items)
        )
    out.append(
        '            <div class="news-sidebar-card news-sidebar-cta">\n'
        "              <h3>Cần đặt xe ngay?</h3>\n"
        "              <p>Tổng đài Xe Taxi Eakar phục vụ 24/7 tại Ea Kar và toàn tỉnh Đắk Lắk.</p>\n"
        '              <a href="tel:0856713714" class="contact-submit">Gọi 0856 713 714</a>\n'
        "            </div>"
    )
    out.append("          </aside>")
    return "\n".join(out)


def render_list_main(heading, crumbs, cards_posts, posts, active_cat=None):
    if cards_posts:
        cards = '          <div class="news-list">\n%s\n          </div>' % "\n\n".join(render_card(p) for p in cards_posts)
    else:
        cards = (
            '          <div class="news-list news-list--empty">\n'
            '            <p class="news-empty">Chưa có bài viết nào. Quý khách quay lại sau nhé!</p>\n'
            "          </div>"
        )
    return (
        "%s\n\n"
        '    <section class="news-page">\n'
        '      <div class="news-inner">\n'
        '        <div class="news-grid">\n'
        "%s\n\n"
        "%s\n"
        "        </div>\n"
        "      </div>\n"
        "    </section>"
        % (render_banner(heading, crumbs), cards, render_sidebar(posts, active_cat=active_cat))
    )


# ------------------------------------------------------------------ build lớn

def build_list(layout, posts):
    url = "/tin-tuc/"
    title = "Tin Tức" + TITLE_SUFFIX
    graph = [
        {"@type": "CollectionPage", "@id": SITE + url + "#webpage", "url": SITE + url, "name": title,
         "description": LIST_DESCRIPTION, "inLanguage": "vi", "isPartOf": WEBSITE_REF,
         "about": BUSINESS_REF, "breadcrumb": {"@id": SITE + url + "#breadcrumb"}},
        breadcrumb_ld(url, [("Tin tức", url)]),
    ]
    # Chưa có bài -> trang rỗng, KHÔNG cho lập chỉ mục (nội dung mỏng hại SEO cả site).
    head = render_head(title, LIST_DESCRIPTION, url, DEFAULT_IMAGE, graph, index=bool(posts))
    main = render_list_main("TIN TỨC", [("Tin tức", None)], posts, posts)
    write(os.path.join(OUT, "index.html"), layout.replace("{{HEAD}}", head).replace("{{MAIN}}", main))


def build_categories(layout, posts):
    built = []
    for cat in used_categories(posts):
        url = category_url(cat)
        subset = [p for p in posts if p.get("category") == cat]
        title = cat + TITLE_SUFFIX
        desc = "Các bài viết chuyên mục %s của Xe Taxi Eakar - dịch vụ taxi tại Ea Kar, Đắk Lắk." % cat
        graph = [
            {"@type": "CollectionPage", "@id": SITE + url + "#webpage", "url": SITE + url, "name": title,
             "description": desc, "inLanguage": "vi", "isPartOf": WEBSITE_REF,
             "breadcrumb": {"@id": SITE + url + "#breadcrumb"}},
            breadcrumb_ld(url, [("Tin tức", "/tin-tuc/"), (cat, url)]),
        ]
        head = render_head(title, desc, url, DEFAULT_IMAGE, graph)
        main = render_list_main(cat.upper(), [("Tin tức", "/tin-tuc/"), (cat, None)], subset, posts, active_cat=cat)
        write(os.path.join(OUT, "danh-muc", CATEGORY_SLUGS[cat], "index.html"),
              layout.replace("{{HEAD}}", head).replace("{{MAIN}}", main))
        built.append(CATEGORY_SLUGS[cat])
    return built


def build_posts(layout, posts):
    for post in posts:
        detail = post if post.get("smart") else load_json(os.path.join("blog", post["slug"] + ".json"), None)
        if detail is None:
            raise SystemExit(
                "Thiếu data/blog/%s.json (có trong danh sách nhưng không có nội dung) - "
                "kiểm tra lại thao tác Lưu gần nhất." % post["slug"]
            )
        url = post_url(post["slug"])
        title = detail.get("title", post["title"])
        seo_title = detail.get("seo_title") or (title + TITLE_SUFFIX)
        desc = detail.get("description") or LIST_DESCRIPTION
        image = SITE + cover_url(detail) if cover_url(detail) else DEFAULT_IMAGE
        cat = detail.get("category") or ""
        crumbs_ld = [("Tin tức", "/tin-tuc/")]
        crumbs = [("Tin tức", "/tin-tuc/")]
        if cat in CATEGORY_SLUGS:
            crumbs_ld.append((cat, category_url(cat)))
            crumbs.append((cat, category_url(cat)))
        crumbs_ld.append((detail.get("breadcrumb") or title, url))
        crumbs.append((detail.get("breadcrumb") or title, None))

        article = {
            "@type": "BlogPosting", "@id": SITE + url + "#article", "mainEntityOfPage": SITE + url,
            "headline": title, "description": desc, "image": image, "inLanguage": "vi",
            "datePublished": detail.get("date", ""),
            "dateModified": str(detail.get("updated_at") or detail.get("date", ""))[:10],
            "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE + "/"},
            "publisher": BUSINESS_REF, "isPartOf": WEBSITE_REF,
        }
        if cat:
            article["articleSection"] = cat
        graph = [article, breadcrumb_ld(url, crumbs_ld)]
        body_html = detail.get("content_html", "")
        css, js = [], []
        if post.get("smart"):
            for pattern, c, j in BLOCK_ASSETS:
                if re.search(pattern, body_html):
                    css += [x for x in c if x not in css]
                    js += [x for x in j if x not in js]
        head = render_head(seo_title, desc, url, image, graph, og_type="article", extra_css=css)
        content_cls = "news-article-content post-detail-body" if post.get("smart") else "news-article-content"

        meta = '<span class="news-card-date">%s</span>' % esc(date_vn(detail.get("date")))
        if cat in CATEGORY_SLUGS:
            meta += ' <a class="news-card-cat" href="%s">%s</a>' % (esc(category_url(cat)), esc(cat))
        main = (
            "%s\n\n"
            '    <section class="news-page">\n'
            '      <div class="news-inner">\n'
            '        <div class="news-grid">\n'
            '          <article class="news-article">\n'
            '            <div class="news-card-meta">%s</div>\n'
            '            <img class="news-article-cover" src="%s" alt="%s">\n'
            '            <div class="%s">\n'
            # content_html là HTML do trình soạn thảo / file Smart content -> KHÔNG escape.
            "%s\n"
            "            </div>\n"
            "          </article>\n\n"
            "%s\n"
            "        </div>\n"
            "      </div>\n"
            "    </section>"
            % (render_banner(title, crumbs), meta, esc(cover_url(detail)),
               esc(detail.get("cover_alt") or title), content_cls, body_html,
               render_sidebar(posts, active_cat=cat, current_slug=post["slug"]))
        )
        page = layout.replace("{{HEAD}}", head).replace("{{MAIN}}", main)
        if js:
            tag = '<script src="/main.js" defer></script>'
            assert page.count(tag) == 1, "không tìm thấy thẻ main.js trong templates/layout.html"
            page = page.replace(tag, tag + "".join('\n  <script src="%s" defer></script>' % esc(j) for j in js))
        write(os.path.join(OUT, post["slug"], "index.html"), page)


def prune_orphans(posts, built_categories):
    """Xoá thư mục bài/chuyên mục không còn trong data/ - không dọn thì bài đã xoá qua trang
    quản trị vẫn truy cập được và Google vẫn lập chỉ mục tiếp."""
    valid = {p["slug"] for p in posts}
    removed = []
    for name in sorted(os.listdir(OUT)):
        path = os.path.join(OUT, name)
        if os.path.isdir(path) and name != "danh-muc" and name not in valid:
            shutil.rmtree(path)
            removed.append("tin-tuc/" + name)
    cat_dir = os.path.join(OUT, "danh-muc")
    if os.path.isdir(cat_dir):
        for name in sorted(os.listdir(cat_dir)):
            path = os.path.join(cat_dir, name)
            if os.path.isdir(path) and name not in built_categories:
                shutil.rmtree(path)
                removed.append("tin-tuc/danh-muc/" + name)
        if not os.listdir(cat_dir):
            os.rmdir(cat_dir)
    return removed


def build_sitemap(posts, built_categories):
    """Giữ NGUYÊN các mục trang tĩnh viết tay (kể cả lastmod), chỉ sinh lại mục /tin-tuc/."""
    path = os.path.join(HTML, "sitemap.xml")
    with open(path, encoding="utf-8") as fh:
        current = fh.read()
    blocks = re.findall(r"  <url>.*?</url>\n", current, re.S)
    static = [b for b in blocks if "<loc>%s/tin-tuc/" % SITE not in b]

    def entry(url, lastmod, priority):
        return ("  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n    <priority>%s</priority>\n  </url>\n"
                % (SITE, url, lastmod, priority))

    news = []
    if posts:
        newest = max(str(p.get("updated_at") or p.get("date", ""))[:10] for p in posts)
        news.append(entry("/tin-tuc/", newest, "0.6"))
        for cat in POST_CATEGORIES:
            if CATEGORY_SLUGS[cat] in built_categories:
                subset = [p for p in posts if p.get("category") == cat]
                news.append(entry(category_url(cat),
                                  max(str(p.get("updated_at") or p.get("date", ""))[:10] for p in subset), "0.4"))
        for p in posts:
            news.append(entry(post_url(p["slug"]), str(p.get("updated_at") or p.get("date", ""))[:10], "0.6"))

    out = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "".join(static) + "".join(news) + "</urlset>\n")
    write(path, out)
    return len(news)


def main():
    layout = read_template("layout.html")
    # Bỏ comment hướng dẫn đầu template khỏi trang build ra.
    layout = re.sub(r"<!--\n  KHUNG DÙNG CHUNG.*?-->\n", "", layout, count=1, flags=re.S)
    posts = all_posts()
    os.makedirs(OUT, exist_ok=True)
    build_list(layout, posts)
    cats = build_categories(layout, posts)
    build_posts(layout, posts)
    removed = prune_orphans(posts, cats)
    n_sitemap = build_sitemap(posts, cats)

    print("bài viết   : %d" % len(posts))
    print("chuyên mục : %s" % (", ".join(cats) or "(không có)"))
    print("sitemap    : %d mục /tin-tuc/" % n_sitemap)
    if removed:
        print("đã dọn     : %s" % ", ".join(removed))


if __name__ == "__main__":
    main()
