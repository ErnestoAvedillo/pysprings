# muelles

Biblioteca de Python para el **cálculo de muelles** (resortes): compresión, tracción
y torsión. Incluye datos de materiales, cálculo de características del hilo y análisis
de fatiga mediante el diagrama de Goodman.

> El código se extrajo de una aplicación web Django y se reorganizó como biblioteca
> independiente. La capa web (vistas, plantillas, `static/`) no forma parte de la
> biblioteca.

## Estructura

```
src/muelles/            Paquete de la biblioteca
├── lineal/             Motor de cálculo (compresión, tracción, torsión, Goodman)
├── pymodels/           Modelos de datos (pydantic): material, unidades, hilo, posiciones
├── material/           Tablas de materiales y tolerancias (CSV, datos de paquete)
├── regresiones/        Modelos ajustados cargados en runtime
│   └── factor_f/       Factor f de Shigley (modelo .pkl + cargador)
└── plots/              Generación del diagrama de Goodman

tests/                  Tests (pytest)
scripts/regresiones/    Scripts de entrenamiento que generan los .pkl (no runtime)
docs/                   Material de referencia (hoja de cálculo, figuras)
```

## Instalación

El proyecto usa [uv](https://docs.astral.sh/uv/):

```bash
uv sync                 # crea el entorno e instala dependencias
```

O con pip en modo editable:

```bash
pip install -e ".[dev]"
```

## Uso

```python
from muelles import Material, MuelleCompresion

material = Material(nombre_material="SH")
muelle = MuelleCompresion(material=material, diametro_hilo=2.0)
muelle.numero_espiras = 8
print(muelle.calcular_longitud_bloqueo())
print(muelle.calcular_paso())
```

## Tests

```bash
uv run pytest
```

## Reentrenar los modelos de regresión

Los `.pkl` incluidos ya están entrenados. Para regenerarlos:

```bash
uv run python scripts/regresiones/factor_f/factor_f.py
```
