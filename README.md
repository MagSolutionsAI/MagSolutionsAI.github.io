# magsolutionsai.com

[![MagAudit](https://api.magsolutionsai.com/badge/MagSolutionsAI/MagSolutionsAI.github.io.svg)](https://github.com/apps/magaudit-agent)

El sitio de **MagSolutionsAI**. HTML estático, sin build, servido por GitHub
Pages desde `main`.

- Producción: **https://magsolutionsai.com**
- Producto: [MagAudit Agent](https://github.com/apps/magaudit-agent), una
  GitHub App que audita cada pull request.

## Estructura

| | |
|---|---|
| `index.html` | portada |
| `pricing.html` · `privacy.html` · `terms.html` · `legal-notice.html` | producto y legales |
| `magaudit-vs-*.html` | comparativas con otras herramientas |
| `hallucination-index.html` | índice público de dependencias inexistentes vistas en repositorios reales |
| `blog/` · `content/` · `es/` | artículos y versión en castellano |
| `evidence/` | el corpus con el que se calcula nuestra tasa de falsos positivos |
| `CNAME` · `.nojekyll` | configuración de GitHub Pages |

## Publicar

Un push a `main` publica. No hay pipeline ni paso de compilación: lo que hay en
el repositorio es lo que se sirve.

## Nos auditamos con nuestro propio producto

La App está instalada en este repositorio, así que cada pull request pasa por el
mismo detector que ofrecemos a los clientes. La insignia de arriba sale de
nuestra propia API y refleja auditorías reales de este repositorio — si dice
`not audited`, es que todavía no ha habido ninguna.

El `.magaudit.yml` excluye `evidence/`, que está lleno a propósito de líneas que
parecen credenciales. Esa exclusión no las esconde: el comentario de cada pull
request dice cuántos hallazgos está ocultando y por qué.

## Verificar lo que afirmamos

- Nuestra tasa de error, derivada de las pruebas y no escrita a mano:
  **https://api.magsolutionsai.com/quality**
- Las cifras de campo en vivo: **https://api.magsolutionsai.com/measurement**
- El corpus que respalda ambas: [`evidence/`](evidence/)
