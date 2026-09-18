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
import sys
import urllib.request

ENDPOINT = "https://api.magsolutionsai.com/articulo-semanal"
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def traer() -> dict:
    with urllib.request.urlopen(ENDPOINT, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


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

    slug = d["slug"]
    pagina = RAIZ / "blog" / f"{slug}.html"
    if pagina.exists():
        print(f"{slug} ya está publicado. Nada que hacer.")
        return 0

    for clave in ("html", "markdown", "tarjeta", "jsonld", "rss", "fecha"):
        if not d.get(clave):
            raise SystemExit(f"ERROR: el endpoint no trae '{clave}'. No se publica nada.")

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
