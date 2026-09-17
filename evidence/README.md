# Nuestro corpus de falsos positivos

Esto es lo que hay detrás de <https://api.magsolutionsai.com/quality>.

Cada corrección que hemos hecho al detector está fijada por una prueba de
regresión, y **cada prueba se construye con la línea exacta observada en un
repositorio público real**, citado en el comentario de al lado. No son casos
inventados para que salga bien: son las veces que nos equivocamos sobre código
de otra gente.

El número que publica `/quality` se deriva de contar estas pruebas. No se
escribe a mano. Si alguien borra una, el recuento baja solo.

## Por qué está publicado

Porque hasta el 2026-09-17 no lo estaba, y el endpoint decía «compruébalo tú
mismo» apuntando a un fichero de un repositorio privado. Una verificación que
nadie puede hacer no es una verificación.

Y porque es lo más difícil de copiar que tenemos. Una empresa con miles de
clientes no puede empezar a publicar su tasa de error: sus clientes
preguntarían y sus inversores también. Es una posición que solo sostiene quien
todavía no tiene nada que perder, y deja de poder sostenerla el día que lo
tiene.

## Sobre las credenciales que verás aquí dentro

El fichero está lleno de cadenas con forma de clave de API. **Ninguna es real.**
Son de tres clases:

1. **Inventadas** para la prueba, con longitudes y alfabetos que no
   corresponden a ningún formato válido del proveedor.
2. **Publicadas por el propio proveedor** en su documentación, como
   `AKIAIOSFODNN7EXAMPLE`, que AWS documenta precisamente para ejemplos.
3. **Redactadas** cuando venían de un repositorio de terceros: se conserva la
   forma de la línea, no el valor.

Nunca comprobamos si una credencial funciona — ni las nuestras. El módulo que
audita habla con `api.github.com` y con los registros de paquetes, y con nada
más.

## Qué puedes comprobar tú

- **La procedencia.** Cada comentario `# owner/repo#123` apunta a un pull
  request público. Abre el enlace y busca la línea.
- **El comportamiento.** Instala la App en un repositorio de prueba tuyo y pega
  esas líneas en un pull request. Lo que dice la prueba es lo que tiene que
  pasar.
- **La aritmética.** Cuenta las funciones `def test_` del fichero y compáralo
  con `correcciones_fijadas_por_prueba` en `/quality`.

## Lo que este fichero no es

No es el detector. Las reglas viven en el repositorio del producto, que es
privado. Esto es el registro de nuestros errores y de las correcciones que los
cerraron — que es la parte que hay que poder auditar.
