# Reglas de este sitio — vinculantes para cualquier agente que publique aquí

Este repositorio lo edita también una **rutina autónoma semanal** que publica
artículos sin que nadie los revise antes. Estas reglas existen para que esa
rutina no reintroduzca afirmaciones que ya se retiraron por falsas.

Léelas antes de escribir una sola línea publicable.

---

## 1. Lo que el producto hace, exactamente

La App **publica un comentario** en el pull request. Nada más.

- **No crea check runs.** No crea estados de commit. **No puede bloquear un
  merge**, y no debe insinuarse que lo haga.
- Verificado en el código el 2026-09-09: la única llamada a GitHub tras auditar
  es `POST issues/{n}/comments`.

Prohibido escribir, en cualquier idioma: «bloquea el merge», «blocks the merge»,
«gated», «lo detiene antes de fusionar», «impide que llegue al lockfile».

Permitido: «lo marca como crítico en el PR», «lo reporta con fichero y línea».

## 2. Cifras: solo las medidas, y con su denominador

| Afirmación | Estado |
|---|---|
| Paquetes alucinados confirmados | **0** |
| Dependencias resueltas | ver `https://api.magsolutionsai.com/measurement` |
| Clientes de pago | **0** |
| Instalaciones ajenas | **0** |

- **Nunca** citar una cifra que no salga de ese endpoint o de
  `data/field_scan.jsonl` del repo del producto.
- **Nunca** redondear a la baja con «roughly» ni a la alta con «más de» si el
  número exacto está disponible.
- Un cero siempre va con su denominador. «0 alucinaciones» no significa nada;
  «0 en 1.419 dependencias resueltas» es un resultado.

## 3. Prohibido el discurso del miedo sin dato

El posicionamiento es exactamente el contrario al del sector: **medimos el
ataque que vendemos y publicamos que casi no aparece**. Un artículo que dé a
entender que el slopsquatting es frecuente contradice nuestra propia medición y
destruye lo único que nos diferencia.

Prohibido: «plaga», «epidemia», «está pasando ahora mismo a escala», «tu equipo
ya está expuesto».

Obligatorio al hablar del riesgo: decir que en nuestra medición no apareció.

## 4. Nunca inventar un nombre de paquete

Si un artículo menciona un paquete, ese paquete **existe y se ha comprobado** en
el registro esa misma sesión, o se cita un advisory con su identificador. Un
nombre inventado en una web que detecta nombres inventados es el fin de la
credibilidad del producto.

## 5. Competencia: nombrarla y reconocer dónde gana

GitHub Advanced Security hace mucho más que nosotros y hay que decirlo. Nuestra
ventaja es el modelo de precio (plano por organización frente a 19 $ + 30 $ por
committer y mes en repos privados) y la verificación de existencia, no la
cobertura.

Prohibido sugerir que somos un sustituto de una plataforma completa.

## 6. Paridad de idiomas

Toda sección nueva de `index.html` va también a `es/index.html`. Una web
bilingüe donde la versión española no tiene los argumentos principales es peor
que una web monolingüe.

## 7. Antes de publicar

1. ¿Cada cifra tiene fuente comprobable?
2. ¿Alguna frase promete algo que el código no hace? (regla 1)
3. ¿Los enlaces internos resuelven?
4. ¿Existe la versión en español?

Si alguna respuesta es no, no se publica.
