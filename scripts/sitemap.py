"""Regenera sitemap.xml con TODAS las paginas publicas de la web.

Por que existe
--------------
Hasta el 2026-09-28 el sitemap se escribia a mano y listaba 19 de 39 paginas:
faltaban la pagina de confianza, las comparativas, la de calidad, todas las
versiones en castellano y los informes nuevos. Google encuentra lo que el
sitemap le da; lo demas llega tarde o no llega.

Ahora sale del arbol de ficheros, con la pareja de idioma cuando existe, y el
flujo del informe semanal lo regenera cada vez que publica.

Uso:  python scripts/sitemap.py
"""

from __future__ import annotations

import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DOMINIO = "https://magsolutionsai.com"
# Verificacion de Search Console y paginas que no se sirven.
EXCLUIR = re.compile(r"^(google[0-9a-f]+\.html|404\.html)$")
# Una pagina que pide no indexarse (p. ej. la bienvenida post-instalacion) no
# va al sitemap: lo decide su propia meta, no una lista que se desincroniza.
NOINDEX = re.compile(r'<meta\s+name="robots"\s+content="[^"]*noindex', re.I)


def _url(ruta: str) -> str:
    if ruta == "index.html":
        return f"{DOMINIO}/"
    if ruta.endswith("/index.html"):
        return f"{DOMINIO}/{ruta[:-len('index.html')]}"
    return f"{DOMINIO}/{ruta}"


def paginas() -> list:
    fuera = []
    for patron in ("*.html", "es/*.html", "blog/*.html"):
        for p in RAIZ.glob(patron):
            ruta = p.relative_to(RAIZ).as_posix()
            if EXCLUIR.match(p.name) or NOINDEX.search(p.read_text(encoding="utf-8")):
                continue
            fuera.append(ruta)
    return sorted(fuera)


def _pareja(ruta: str, todas: set):
    """(en, es) si la pagina existe en los dos idiomas; None si no."""
    if ruta.startswith("es/"):
        en = ruta[3:]
        return (en, ruta) if en in todas else None
    es = f"es/{ruta}"
    return (ruta, es) if es in todas else None


def generar() -> str:
    todas = paginas()
    conjunto = set(todas)
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
         '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for ruta in todas:
        L.append("  <url>")
        L.append(f"    <loc>{_url(ruta)}</loc>")
        par = _pareja(ruta, conjunto)
        if par:
            en, es = par
            L.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{_url(en)}"/>')
            L.append(f'    <xhtml:link rel="alternate" hreflang="es" href="{_url(es)}"/>')
            L.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{_url(en)}"/>')
        L.append("  </url>")
    L.append("</urlset>")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    texto = generar()
    (RAIZ / "sitemap.xml").write_text(texto, encoding="utf-8", newline="\n")
    print(f"sitemap.xml: {texto.count('<url>')} paginas")
