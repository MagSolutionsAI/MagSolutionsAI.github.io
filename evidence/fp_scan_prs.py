"""fp_scan_prs — mide el ruido del detector sobre la poblacion CORRECTA.

Por que existe
--------------
El 2026-09-17, auditando como Red Team, se midio el detector sobre 6.000
ficheros de librerias ya publicadas. Sirvio para el escaneo de instalacion —
que mira ficheros enteros— y bajo sus falsos positivos de 4 a 0.

Pero para las reglas VULN esa poblacion es la equivocada, y equivocarse de
poblacion es el error que este proyecto ya ha cometido tres veces (§16, §19,
§21 del corpus). `eval` o `pickle.loads` en un fichero entero no dicen ni quien
ni cuando; sobre una linea que alguien acaba de escribir, si.

Asi que la pregunta que este script responde es la unica que le importa a un
cliente: **de cada 100 pull requests reales, en cuantos abrimos la boca, y
cuantas de esas veces teniamos razon.**

Que NO hace
-----------
No toca nada. Lee pull requests publicos con un token de solo lectura y no
escribe comentarios, no abre issues y no contacta con nadie. La salida se
revisa a mano: el recuento no es la medicion, la revision si.

Uso:
    python tools/fp_scan_prs.py [n_prs] [--json]
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.github_app.detector import audit_diff          # noqa: E402
from tools.gh_api import gh_json, gh_text               # noqa: E402

# Lenguajes donde el detector tiene reglas. Buscar PRs de repos Fortran seria
# medir nuestra propia irrelevancia, no nuestro ruido.
CONSULTAS = [
    "is:pr is:open language:python",
    "is:pr is:open language:javascript",
    "is:pr is:open language:typescript",
]


def _prs(n: int) -> list:
    """Pull requests abiertos, recientes, de repositorios publicos."""
    fuera, por_consulta = [], max(1, n // len(CONSULTAS))
    for q in CONSULTAS:
        pagina = 1
        while len([x for x in fuera if x[2] == q]) < por_consulta and pagina <= 4:
            from urllib.parse import quote
            d = gh_json(f"search/issues?q={quote(q)}&sort=created&order=desc"
                        f"&per_page=50&page={pagina}")
            if not d or not d.get("items"):
                break
            for it in d["items"]:
                url = (it.get("pull_request") or {}).get("url")
                if url:
                    fuera.append((url, it.get("html_url", ""), q))
            pagina += 1
    return fuera[:n]


def barrido(n: int = 120) -> dict:
    prs = _prs(n)
    por_regla = collections.Counter()
    hallazgos = []
    con_hallazgo = analizados = 0

    for url, html, _q in prs:
        diff = gh_text(url, accept="application/vnd.github.v3.diff")
        if not diff:
            continue
        analizados += 1
        try:
            res = audit_diff(diff)
        except Exception as exc:
            hallazgos.append({"pr": html, "ERROR": f"{type(exc).__name__}: {exc}"[:200]})
            continue
        if res["findings"]:
            con_hallazgo += 1
        for f in res["findings"]:
            por_regla[f["rule_id"]] += 1
            hallazgos.append({"pr": html, "regla": f["rule_id"],
                              "severidad": f["severity"],
                              "donde": f"{f['file']}:{f['line']}",
                              "linea": (f.get("snippet") or "")[:150]})

    return {
        "prs_analizados": analizados,
        "prs_con_hallazgo": con_hallazgo,
        "tasa_pct": round(100 * con_hallazgo / analizados, 1) if analizados else 0,
        "por_regla": dict(por_regla.most_common()),
        "hallazgos": hallazgos,
    }


def main(n: int, como_json: bool) -> int:
    r = barrido(n)
    if como_json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(f"PRs analizados   : {r['prs_analizados']}")
    print(f"Con hallazgo     : {r['prs_con_hallazgo']}  ({r['tasa_pct']} %)")
    print(f"Hallazgos totales: {len(r['hallazgos'])}")
    print()
    for regla, k in r["por_regla"].items():
        print(f"  {regla:22} {k}")
    print()
    print("CADA HALLAZGO — a revisar a mano, que es donde esta la medicion:")
    for h in r["hallazgos"]:
        if "ERROR" in h:
            print(f"  !! {h['pr']}  {h['ERROR']}")
            continue
        print(f"  [{h['severidad']:8}] {h['regla']:20} {h['donde']}")
        print(f"      {h['linea']}")
        print(f"      {h['pr']}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    raise SystemExit(main(int(args[0]) if args else 120, "--json" in sys.argv))
