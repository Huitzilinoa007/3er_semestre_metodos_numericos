# Laboratorio Numérico Interactivo (v2, tema oscuro)

Suite de métodos numéricos en Streamlit. Cada método muestra, en este orden:
**datos → procedimiento en LaTeX (se escribe en vivo) → tabla que se va llenando → resultados y gráfica**.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Pruebas de la lógica (no necesitan Streamlit): `python -m unittest discover -s tests -v` (37 pruebas)

## Qué hay hoy

- **Errores y Punto Flotante:** Punto flotante IEEE 754 (simple y doble).
- **Raíces de Ecuaciones:** Bisección, Regla Falsa, Newton-Raphson, Secante, Punto Fijo, Aitken, Deflación y Müller.
- **Interpolación:** Neville y Hermite.
- **Derivadas Numéricas:** Derivación por 2 puntos y por 5 puntos (centrada y de extremo).
- **Integración Numérica:** Trapecio, Simpson 3/8, Cuadratura adaptativa, Integración doble por trapecio y por Simpson 3/8.
- **En desarrollo (Persona B, solo aparecen en el menú):** Lagrange, Diferencias divididas, Splines cúbicos,
  Derivación por 3 puntos, Extrapolación de Richardson, Simpson 1/3, Romberg, Cuadratura gaussiana e
  Integración doble por Simpson 1/3.
- Los campos empiezan **vacíos**; al abrir no se calcula nada ni aparece ningún error.

### Métodos "directos" (Persona A)

Los métodos que no son de raíces no iteran hasta una tolerancia: su tabla tiene **una fila por paso del cálculo**
(un nodo, un valor de h, un subintervalo, un bit…). Viven aparte para no mezclarse con los de raíces:

| Pieza | Archivo |
|---|---|
| Lógica | `core/metodos/punto_flotante.py`, `neville.py`, `hermite.py`, `derivacion.py`, `integracion.py`, `integracion_multiple.py` |
| Ejecutores (texto → Resultado, con sus tarjetas en `ctx["kpis"]`) | `core/ejecutores_directos.py` |
| Procedimiento paso a paso | `core/procedimiento_directos.py` |
| Plan de la tabla animada | final de `core/tabla_pasos.py` (las reglas reciben `(i, res)`) |
| Gráficas | `ui/plots/directos.py` |
| Campos y textos | `METODOS_PERSONA_A` en `registry.py` |

`registry.py` ahora admite campos de tipo `lista` (nodos separados por comas), `lista_o_funcion` (valores o una
función de x), `funcion_xy` (f(x, y)), `numero` y `entero`, campos `opcional`, selectores (`Opcion`) y qué controles
comunes mostrar (`controles=("tol", "nmax")` o ninguno). Para los métodos de la Persona B conviene copiar el
`MetodoSpec` del método más parecido (por ejemplo Simpson 3/8 para Simpson 1/3, o Neville para Lagrange).

### Correcciones de la revisión del 24/11/2026

- Bisección y Regla Falsa ya no dicen "Convergió" en un polo (1/x, tan x): marcan "No convergió" y explican la asíntota.
- Punto Fijo ya no bloquea cuando |g'(x₀)| ≥ 1 (ej. g = e^(−x), x₀ = −0.5 sí converge): avisa y calcula.
- Newton, Punto Fijo y Müller, cuando no convergen, muestran la tabla de lo que hicieron con "No convergió".
- Müller ya no falla con "puntos colineales" cuando un punto inicial es raíz exacta (x³ − 1 con 0, 1, 2).
- Aitken explica en español cuando la sucesión diverge (antes salía "Numerical result out of range").
- Deflación sugiere Müller cuando quedan raíces complejas; ya no aparece "−0.000000".

## Cómo se comporta cada método

- **Procedimiento:** se desarrollan las iteraciones que elijas (por defecto 1, 2 y 3) y, **siempre al final, la última**,
  que es la que lleva al resultado.
- **Tabla:** se llena celda por celda en las primeras filas (ámbar = celda que se calcula, azul = celdas que se usan);
  las demás filas aparecen más rápido. Al terminar se resalta la iteración donde se alcanza la tolerancia.
  En los métodos "de escalerita" (Newton, Secante, Punto Fijo, Aitken, Müller, Deflación) se ve cómo la última
  columna de una fila alimenta la primera de la siguiente.
- **Resultados:** tarjetas KPI y gráfica con slider para recorrer cada iteración.
- "Saltar animación" y "Repetir animación" controlan procedimiento y tabla a la vez; "Sin animación" lo muestra todo de golpe.

## Estructura

```
app.py                  entrada: tema y navegación
registry.py             catálogo de métodos, sus campos y la lista "en desarrollo"
.streamlit/config.toml  paleta y tipografías de Streamlit
core/                   lógica pura (sin Streamlit)
  parser.py             lee lo que escribe el usuario (SymPy, seguro, errores en español)
  metodos/              un archivo por método (+ _plantilla.py para copiar)
  ejecutores.py         texto -> parser -> método -> Resultado
  procedimiento.py      desarrollo paso a paso en LaTeX + selección de iteraciones
  tabla_pasos.py        plan de llenado de la tabla (qué celda se usa para calcular cuál)
  escritura.py          corta las ecuaciones en pedazos válidos para animarlas
ui/
  styles.css            todo el diseño (colores, títulos, tabla, tarjetas)
  components/           tarjeta de datos, hoja, tabla animada, resultados, secciones
  plots/                gráficas Plotly por método
  views/                inicio, vista genérica de método, "en desarrollo"
tests/                  pruebas
```

## Cómo agregar un método nuevo (paso a paso)

Ejemplo: pasar **Trapecio** de "en desarrollo" a método real.

1. **Lógica:** copia `core/metodos/_plantilla.py` como `core/metodos/trapecio.py`. La función devuelve `(resultado, DataFrame)`
   y la tabla lleva **una fila por iteración**, con una columna `iter` (1, 2, 3...) y los errores como número (`np.nan`, no `"-"`).
2. **Ejecutor:** en `core/ejecutores.py` escribe `_ej_trapecio(textos, numeros, tol, n_max)` que devuelva un `Resultado(...)`
   y regístralo en el diccionario `EJECUTORES`.
3. **Registro:** en `registry.py` quita el nombre de `PROXIMAMENTE` y agrega un `MetodoSpec(...)` en `METODOS`
   (copia uno existente). El `id` debe ser el mismo en todos los pasos.
4. **Procedimiento:** en `core/procedimiento.py` agrega su entrada en `_PLANTEAMIENTO`, `_VERIFICACION` e `_ITERACION`.
5. **Tabla animada:** en `core/tabla_pasos.py` describe cada columna (qué celdas usa) y regístralo en `PLANES`.
   *Si te lo saltas, la tabla se llena fila por fila sin resaltar celdas y todo funciona igual.*
6. **Gráfica:** escribe `figura_<metodo>(res, k, rango)` en `ui/plots/`, regístrala en `_FIGURAS` y agrega su caso en `rango_auto`.
7. Corre `python -m unittest discover -s tests -v` y agrega tu caso a la lista `CASOS` de `tests/test_core.py`.

### Para Neville (y otras tablas triangulares)

Neville es de **interpolación**, por eso hoy solo está en el menú como "en desarrollo". Su tabla es triangular
(una "escalerita" hacia la derecha): usa el mismo plan de `tabla_pasos.py` marcando en cada celda `P_{i,j}` las dos celdas
de la columna anterior de las que sale. Las celdas que no existen en el triángulo se dejan como `NaN`.

## Trabajar en equipo sin pisarse

- Cada método vive en **su propio archivo** dentro de `core/metodos/` y su gráfica en `ui/plots/`.
- Los archivos compartidos (`registry.py`, `ejecutores.py`, `procedimiento.py`, `tabla_pasos.py`, `ui/plots/__init__.py`)
  son diccionarios donde cada método agrega **una línea**, así que los conflictos de Git son fáciles de resolver.
- Recomendación: una rama por método y *pull request* corto para cada uno.

## Cambios a tus archivos originales de `metodosnum` (la matemática no se tocó)

| Archivo | Cambio de interfaz |
|---|---|
| `falsa_posicion.py` | Sin `input()`/`print()` a nivel de módulo; devuelve `(c, tabla)` y tiene tope de iteraciones |
| `secante.py` | Tope de iteraciones y aviso si `f(x0) == f(x1)` |
| `punto_fijo.py` | `max_iter` como parámetro; ya no marca "no convergió" si converge justo en la última iteración |
| `deflacion.py` | Import relativo; devuelve `(raíces, tabla)` con una fila por etapa |
| `newton_rapshon.py` | Renombrado a `newton_raphson.py` (queda un alias con el nombre anterior) |
| `biseccion.py` | Se usa la versión de tu Proyecto (con columna `iter` y NaN) |
| `aceleracion_aitken.py`, `muller.py` | Solo comentarios |
