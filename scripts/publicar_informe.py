"""Recoge el informe de campo semanal y lo publica en este blog.

Por qué el sentido va de fuera hacia dentro
--------------------------------------------
El servidor que genera el informe **no puede escribir en este repositorio**: la
organización tiene deshabilitadas las deploy keys. En vez de pedir ese permiso
se invierte el sentido — el servidor expone el artículo ya renderizado y este
script, ejecutado por GitHub Actions (que en su propio repositorio ya puede
escribir), lo recoge.

Por qué importa que el artículo viva aquí
-----------------------------------------
Sin página en nuestro dominio, el `canonical_url` del artículo en dev.to apunta
a dev.to, y todo el posicionamiento que genere es de ellos. En cuanto esta
página existe, el servidor corrige el enlace y el original pasa a ser nuestro.

Este script no decide nada
--------------------------
Todo el criterio —qué se escribe, qué cifras lleva, cómo se renderiza— vive en
el servidor, donde hay pruebas. Aquí solo se escriben ficheros e se insertan
fragmentos en anclas conocidas. Si una ancla no aparece, falla en voz alta en
vez de publicar a medias.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.request

ENDPOINT = "https://api.magsolutionsai.com/articulo-semanal"
MEDICION = "https://api.magsolutionsai.com/measurement"
RAIZ = pathlib.Path(__file__).resolve().parent.parent

# Cuanto puede haber crecido la medicion entre que el servidor escribe el
# articulo (lunes 09:30) y este script lo recoge (10:30). El barrido corre a
# las 06:00, asi que en ese hueco no deberia crecer nada; el margen es holgura.
MARGEN = 0.10


def traer() -> dict:
    with urllib.request.urlopen(ENDPOINT, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def cifras_en_vivo() -> dict:
    with urllib.request.urlopen(MEDICION, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def motivo_para_no_publicar(articulo: dict, vivo: dict) -> str | None:
    """La unica decision que toma este script: si las cifras del articulo
    no son las de la medicion real, no se publica.

    El 2026-09-18 se publico aqui un articulo con las cifras de las PRUEBAS
    del servidor (1000 PRs, `a/b#1`): el fichero de prueba viajo en un
    despliegue y este script lo publico sin mirar. Un articulo sin cifras
    declaradas tampoco se publica: lo que no se puede contrastar no sale."""
    cifras = articulo.get("cifras") or {}
    escrito = cifras.get("prs_analysed")
    real = vivo.get("prs_analysed")
    if not isinstance(escrito, int) or not isinstance(real, int) or real <= 0:
        return f"no se pueden contrastar las cifras (articulo {escrito!r}, medicion {real!r})"
    if not (real * (1 - MARGEN) <= escrito <= real):
        return (f"el articulo dice {escrito} pull requests y la medicion en vivo dice "
                f"{real}: no es una medicion real")
    return None


def insertar(fichero: pathlib.Path, ancla: str, fragmento: str,
             antes: bool = True) -> None:
    t = fichero.read_text(encoding="utf-8")
    if ancla not in t:
        raise SystemExit(f"ERROR: no se encuentra el ancla en {fichero.name}: {ancla[:48]!r}")
    i = t.index(ancla)
    if antes:
        t = t[:i] + fragmento + t[i:]
    else:
        i += len(ancla)
        t = t[:i] + "\n" + fragmento.rstrip("\n") + t[i:]
    fichero.write_text(t, encoding="utf-8")


def main() -> int:
    try:
        d = traer()
    except Exception as e:
        print(f"No se pudo consultar el endpoint ({type(e).__name__}). Nada que hacer.")
        return 0

    if not d.get("hay"):
        print("Todavía no hay informe generado.")
        return 0

    # `slug` y `fecha` llegan de la API y acaban en rutas. Hasta el 2026-09-30
    # se usaban tal cual: `slug="../index"` escribia la portada del dominio
    # (auditoria adversarial, H12). Solo kebab-case y fecha ISO.
    slug, fecha = str(d.get("slug") or ""), str(d.get("fecha") or "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise SystemExit(f"ERROR: slug no valido {slug[:60]!r}. No se publica nada.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        raise SystemExit(f"ERROR: fecha no valida {fecha[:60]!r}. No se publica nada.")
    pagina = RAIZ / "blog" / f"{slug}.html"
    if pagina.exists():
        print(f"{slug} ya está publicado. Nada que hacer.")
        return 0

    for clave in ("html", "markdown", "tarjeta", "jsonld", "rss", "fecha"):
        if not d.get(clave):
            raise SystemExit(f"ERROR: el endpoint no trae '{clave}'. No se publica nada.")

    try:
        vivo = cifras_en_vivo()
    except Exception as e:
        raise SystemExit(f"ERROR: no se pudo leer la medicion en vivo ({type(e).__name__}). "
                         "Sin contrastar las cifras no se publica nada.")
    motivo = motivo_para_no_publicar(d, vivo)
    if motivo:
        raise SystemExit(f"ERROR: {motivo}. No se publica nada.")

    pagina.write_text(d["html"], encoding="utf-8")
    posts = RAIZ / "content" / "posts"
    posts.mkdir(parents=True, exist_ok=True)
    (posts / f"{d['fecha']}-{slug}.md").write_text(d["markdown"], encoding="utf-8")

    indice = RAIZ / "blog" / "index.html"
    insertar(indice, '      <a class="pcard" href=', d["tarjeta"])
    insertar(indice, '"blogPost": [', d["jsonld"], antes=False)

    feed = RAIZ / "feed.xml"
    insertar(feed, "    <item>", d["rss"])

    print(f"Publicado: blog/{slug}.html")
    print(f"  + content/posts/{d['fecha']}-{slug}.md")
    print("  + tarjeta en el índice, entrada en el JSON-LD y en el feed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
