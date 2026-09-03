#!/usr/bin/env python3
"""Generador del blog de MagSolutionsAI.

Lee `content/posts/*.md` y produce `blog/index.html` + `blog/<slug>.html`,
ademas de meter las entradas nuevas en `sitemap.xml`.

POR QUE UN GENERADOR Y NO HTML A MANO
-------------------------------------
El blog lo mantiene una tarea programada (el "empleado de marketing"). Si
cada articulo fuera HTML suelto escrito a mano, cada ejecucion tendria que
reproducir de memoria la cabecera, el SEO, el nav y el CTA -- y acabaria
divergiendo, como ya paso con el indice (ver el fix "build_index.py borraba
el SEO al regenerar"). Aqui la plantilla vive en UN sitio: este fichero.

CERO DEPENDENCIAS
-----------------
El conversor de Markdown de abajo cubre el subconjunto que usamos y nada
mas. Es deliberado: el resto del proyecto tampoco añade dependencias para
lo que se puede resolver con la libreria estandar, y una tarea automatica
que se rompe porque falta un paquete en el entorno no sirve de nada.

Uso:
    python tools/build_blog.py
"""

import os
import re
import html
import json
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
BLOG_DIR = ROOT / "blog"
SITEMAP = ROOT / "sitemap.xml"

BASE = "https://magsolutionsai.com"
INSTALL_URL = "https://github.com/apps/magaudit-agent"


# ── Markdown minimo ────────────────────────────────────────────────────────

_LIST_BULLET = r"^[-*]\s+"
_LIST_NUMBER = r"^\d+\.\s+"

def _inline(text: str) -> str:
    """Negrita, cursiva, codigo y enlaces. El texto ya viene escapado."""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def md_to_html(md: str) -> str:
    """Subconjunto de Markdown: h2/h3, parrafos, listas, citas, bloques de
    codigo y tablas simples. Suficiente para articulos tecnicos."""
    out, lines = [], md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Bloque de codigo
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            cls = f' class="lang-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>" + "\n".join(buf) + "</code></pre>")
            continue

        # Tabla
        if "|" in line and i + 1 < len(lines) and re.match(r"^[\s|:-]+$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i]:
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{_inline(html.escape(c))}</th>" for c in header)
            trs = "".join(
                "<tr>" + "".join(f"<td>{_inline(html.escape(c))}</td>" for c in r) + "</tr>"
                for r in rows
            )
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue

        # Encabezados
        m = re.match(r"^(#{2,4})\s+(.*)", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(html.escape(m.group(2)))}</h{lvl}>")
            i += 1
            continue

        # Cita
        # OJO: se unen las lineas ANTES de aplicar _inline. Si se aplicara
        # linea a linea, una negrita o un enlace partido por un salto de
        # linea en el .md nunca casaria con el regex y llegaria al HTML
        # como `**texto**` literal. Paso de verdad al publicar el primer
        # articulo.
        if line.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:])
                i += 1
            out.append('<blockquote class="callout"><p>'
                       + _inline(html.escape(" ".join(buf))) + "</p></blockquote>")
            continue

        # Listas. Un elemento puede continuar en la linea siguiente con
        # sangria (estilo Markdown normal); sin absorber esas continuaciones,
        # la segunda linea se escapaba de la lista y salia como parrafo
        # suelto debajo.
        bullet = _LIST_BULLET if re.match(_LIST_BULLET, line) else (
                 _LIST_NUMBER if re.match(_LIST_NUMBER, line) else None)
        if bullet:
            tag = "ul" if bullet is _LIST_BULLET else "ol"
            items = []
            while i < len(lines) and re.match(bullet, lines[i]):
                parts = [re.sub(bullet, "", lines[i])]
                i += 1
                while (i < len(lines) and lines[i].strip()
                       and lines[i].startswith(("  ", "\t"))
                       and not re.match(r"^\s*([-*]\s|\d+\.\s)", lines[i])):
                    parts.append(lines[i].strip())
                    i += 1
                items.append("<li>" + _inline(html.escape(" ".join(parts))) + "</li>")
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue

        # Parrafo (mismo criterio que la cita: unir primero, formatear despues)
        if line.strip():
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,4}\s|[-*]\s|\d+\.\s|>\s|```)", lines[i]):
                buf.append(lines[i])
                i += 1
            out.append("<p>" + _inline(html.escape(" ".join(buf))) + "</p>")
            continue

        i += 1

    return "\n".join(out)


# ── Lectura de posts ───────────────────────────────────────────────────────

def parse_post(path: Path) -> dict:
    """Frontmatter simple `clave: valor` entre dos lineas de `---`."""
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise ValueError(f"{path.name}: falta el frontmatter")
    _, fm, body = raw.split("---", 2)

    meta = {}
    for line in fm.strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()

    for req in ("title", "description", "date"):
        if req not in meta:
            raise ValueError(f"{path.name}: falta '{req}' en el frontmatter")

    meta["slug"] = meta.get("slug") or path.stem[11:]  # quita el YYYY-MM-DD-
    meta["body"] = body.strip()
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    words = len(re.sub(r"[^\w\s]", "", meta["body"]).split())
    meta["reading_min"] = max(1, round(words / 220))
    return meta


# ── Plantillas ─────────────────────────────────────────────────────────────

def _head(title, desc, canonical, extra_ld="", is_article=False):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="{'article' if is_article else 'website'}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/logo-512.png">
<meta property="og:site_name" content="MagSolutionsAI">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{BASE}/logo-512.png">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/png" href="/favicon-64.png">
<link rel="apple-touch-icon" href="/logo-200.png">
{extra_ld}
<link rel="stylesheet" href="/style.css?v=6">
</head>
<body>

<header class="nav">
  <div class="wrap nav-in">
    <a class="brand" href="/"><img src="/logo-200.png" alt=""><b>MagSolutionsAI</b></a>
    <nav class="nav-links">
      <a href="/">Home</a>
      <a href="/blog/">Blog</a>
      <a href="/pricing.html">Pricing</a>
      <a href="/hallucination-index.html">Index</a>
      <a class="nav-cta" href="{INSTALL_URL}">Install free</a>
    </nav>
  </div>
</header>
"""


FOOTER = f"""
<footer>
  <div class="wrap foot">
    <span>&copy; 2026 MagSolutionsAI</span>
    <a href="/privacy.html">Privacy</a>
    <a href="/terms.html">Terms</a>
    <a href="mailto:magsolutionsai@gmail.com">Contact</a>
    <span class="sp"></span>
    <a href="https://github.com/MagSolutionsAI">GitHub</a>
  </div>
</footer>

</body>
</html>
"""


def _cta(variant="post"):
    """Todo articulo termina en una via de conversion. Contenido sin salida
    hacia el producto es trafico que no paga las horas que cuesta."""
    return f"""
<section class="post-cta">
  <h2>Check this on your own pull requests</h2>
  <p>MagSolutionsAI is a GitHub App that verifies every dependency in every pull request
     against the live PyPI and npm registries, and blocks the ones that do not exist.
     Free for public repositories, forever &mdash; no card, no CI config.</p>
  <div class="cta">
    <a class="btn btn-1" href="{INSTALL_URL}">Install on GitHub &rarr;</a>
    <a class="btn btn-2" href="/pricing.html">See pricing</a>
  </div>
</section>
"""


def render_post(p: dict) -> str:
    d = datetime.strptime(p["date"], "%Y-%m-%d").date()
    canonical = f"{BASE}/blog/{p['slug']}.html"
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": p["title"],
        "description": p["description"],
        "datePublished": p["date"],
        "dateModified": p.get("updated", p["date"]),
        "url": canonical,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "image": f"{BASE}/logo-512.png",
        "inLanguage": "en",
        "keywords": p["tags"],
        "author": {"@type": "Organization", "name": "MagSolutionsAI", "url": f"{BASE}/"},
        "publisher": {
            "@type": "Organization", "name": "MagSolutionsAI",
            "url": f"{BASE}/",
            "logo": {"@type": "ImageObject", "url": f"{BASE}/logo-512.png"},
        },
    }, ensure_ascii=False, indent=2)

    breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{BASE}/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": canonical},
        ],
    }, ensure_ascii=False, indent=2)

    extra = (f'<script type="application/ld+json">\n{ld}\n</script>\n'
             f'<script type="application/ld+json">\n{breadcrumb}\n</script>')

    tags = "".join(f'<span class="ptag">{html.escape(t)}</span>' for t in p["tags"])

    return (
        _head(f"{p['title']} | MagSolutionsAI", p["description"], canonical, extra, is_article=True)
        + f"""
<main class="wrap post">
  <nav class="crumbs"><a href="/">Home</a> / <a href="/blog/">Blog</a></nav>
  <article>
    <header class="post-hd">
      <div class="post-meta">
        <time datetime="{p['date']}">{d.strftime('%d %B %Y')}</time>
        <span class="sep">&middot;</span>
        <span>{p['reading_min']} min read</span>
      </div>
      <h1>{html.escape(p['title'])}</h1>
      <p class="post-lede">{html.escape(p['description'])}</p>
      <div class="ptags">{tags}</div>
    </header>
    <div class="post-body">
{md_to_html(p['body'])}
    </div>
  </article>
  {_cta()}
</main>
""" + FOOTER
    )


def render_index(posts: list) -> str:
    canonical = f"{BASE}/blog/"
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "MagSolutionsAI Blog",
        "description": "Analysis of AI-generated code supply chain risk: slopsquatting, "
                       "hallucinated dependencies and the security of code written by machines.",
        "url": canonical,
        "inLanguage": "en",
        "publisher": {"@type": "Organization", "name": "MagSolutionsAI", "url": f"{BASE}/"},
        "blogPost": [
            {"@type": "BlogPosting", "headline": p["title"], "url": f"{BASE}/blog/{p['slug']}.html",
             "datePublished": p["date"], "description": p["description"]}
            for p in posts
        ],
    }, ensure_ascii=False, indent=2)

    cards = []
    for p in posts:
        d = datetime.strptime(p["date"], "%Y-%m-%d").date()
        tags = "".join(f'<span class="ptag">{html.escape(t)}</span>' for t in p["tags"])
        # Sin la clase `rv` a proposito: ese efecto depende de JavaScript y
        # aqui el contenido no puede depender de JS para ser visible.
        cards.append(f"""
      <a class="pcard" href="/blog/{p['slug']}.html">
        <div class="post-meta">
          <time datetime="{p['date']}">{d.strftime('%d %b %Y')}</time>
          <span class="sep">&middot;</span><span>{p['reading_min']} min</span>
        </div>
        <h2>{html.escape(p['title'])}</h2>
        <p>{html.escape(p['description'])}</p>
        <div class="ptags">{tags}</div>
      </a>""")

    empty = "" if posts else """
      <div class="honest"><span class="lbl">Nothing published yet</span>
      <p>Articles land here as they are written. Nothing is seeded or padded.</p></div>"""

    return (
        _head("Blog — AI supply chain security | MagSolutionsAI",
              "Analysis of AI-generated code supply chain risk: slopsquatting, hallucinated "
              "dependencies, and how to verify what your assistant just suggested.",
              canonical, f'<script type="application/ld+json">\n{ld}\n</script>')
        + f"""
<main class="wrap">
  <section class="idx-hero">
    <span class="lbl">Blog</span>
    <h1>What breaks when machines write the imports</h1>
    <p>Analysis of the supply chain risk in AI-generated code &mdash; hallucinated packages,
       claimed slopsquats, and how to verify a dependency before it reaches your build server.
       Evidence and reproducible checks, not vendor opinion.</p>
  </section>

  <section class="posts">{''.join(cards)}{empty}
  </section>
</main>
""" + FOOTER
    )


# ── Sitemap ────────────────────────────────────────────────────────────────

def update_sitemap(posts: list):
    """Reescribe SOLO el bloque del blog, delimitado por comentarios. El
    resto del sitemap (portada, precios, indice, legales) lo mantiene una
    persona y no se toca -- esto evita que la tarea automatica pise cambios
    manuales, que es exactamente el fallo que ya cometio build_index.py."""
    xml = SITEMAP.read_text(encoding="utf-8")
    START, END = "  <!-- blog:start -->", "  <!-- blog:end -->"

    entries = [f"""
  <url>
    <loc>{BASE}/blog/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>"""]
    for p in posts:
        entries.append(f"""
  <url>
    <loc>{BASE}/blog/{p['slug']}.html</loc>
    <lastmod>{p.get('updated', p['date'])}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>""")
    block = START + "".join(entries) + "\n" + END

    if START in xml and END in xml:
        xml = re.sub(re.escape(START) + r".*?" + re.escape(END), block, xml, flags=re.S)
    else:
        xml = xml.replace("</urlset>", block + "\n\n</urlset>")
    SITEMAP.write_text(xml, encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────────────

def selftest():
    """Comprobaciones del conversor de Markdown. Cubren los tres fallos que
    aparecieron al publicar los primeros articulos -- los tres producian
    HTML valido pero MAL, que es justo lo que una tarea automatica no puede
    detectar sola. `python tools/build_blog.py --selftest` antes de publicar.
    """
    fails = []

    def check(name, got, want_in):
        if want_in not in got:
            fails.append(f"{name}\n    esperaba encontrar: {want_in}\n    en: {got[:160]}")

    # 1. Negrita partida por un salto de linea (fallo real #1)
    check("negrita multilinea",
          md_to_html("Texto con **negrita\nque sigue** aqui."),
          "<b>negrita que sigue</b>")

    # 2. Elemento de lista con continuacion sangrada (fallo real #2)
    html_out = md_to_html("- Primero, que continua\n  en la linea siguiente.\n- Segundo.")
    check("lista con continuacion", html_out, "<li>Primero, que continua en la linea siguiente.</li>")
    if html_out.count("<ul>") != 1 or "<p>" in html_out:
        fails.append(f"lista con continuacion: la continuacion se salio de la lista\n    {html_out}")

    # 3. Cita multilinea (mismo origen que #1)
    check("cita multilinea",
          md_to_html("> Una cita **con negrita\n> partida** dentro."),
          "<b>con negrita partida</b>")

    # Elementos basicos
    check("encabezado", md_to_html("## Titulo"), "<h2>Titulo</h2>")
    check("codigo en bloque", md_to_html("```\ncurl -s x\n```"), "<pre><code>curl -s x</code></pre>")
    check("codigo en linea", md_to_html("usa `pip install`."), "<code>pip install</code>")
    check("enlace", md_to_html("ver [aqui](https://x.com)."), '<a href="https://x.com">aqui</a>')
    check("tabla", md_to_html("| A | B |\n|---|---|\n| 1 | 2 |"), "<th>A</th>")
    check("lista numerada", md_to_html("1. Uno\n2. Dos"), "<ol><li>Uno</li><li>Dos</li></ol>")

    # Escapado: el contenido no puede inyectar HTML
    check("escapado", md_to_html("un <script>alert(1)</script> aqui"), "&lt;script&gt;")

    if fails:
        print("SELFTEST FALLA:\n" + "\n".join("  - " + f for f in fails))
        return 1
    print("  selftest OK (11 comprobaciones)")
    return 0


def main():
    BLOG_DIR.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    posts = [parse_post(f) for f in sorted(POSTS_DIR.glob("*.md"))]
    posts.sort(key=lambda p: p["date"], reverse=True)

    for p in posts:
        (BLOG_DIR / f"{p['slug']}.html").write_text(render_post(p), encoding="utf-8")
        print(f"  escrito blog/{p['slug']}.html")

    (BLOG_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")
    print(f"  escrito blog/index.html ({len(posts)} articulo(s))")

    update_sitemap(posts)
    print("  sitemap.xml actualizado (solo el bloque del blog)")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    # El selftest corre siempre antes de generar: si el conversor esta roto,
    # es preferible no publicar a publicar articulos mal formateados.
    if selftest() != 0:
        sys.exit(1)
    main()
