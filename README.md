# springcalc

A Python library for **spring calculations**: compression, extension, and
torsion springs. Includes material data, wire characteristic calculations,
and fatigue analysis via the Goodman diagram.

> The code was extracted from a Django web application and reorganized as a
> standalone library. The web layer (views, templates, `static/`) is not part
> of the library.

## Structure

```
src/springcalc/         Library package
├── lineal/             Calculation engine (compression, extension, torsion, Goodman)
├── pymodels/           Data models (pydantic): material, units, wire, positions
├── material/           Material and tolerance tables (CSV, package data)
├── regresiones/        Fitted models loaded at runtime
│   └── factor_f/       Shigley's factor f (plain JSON coefficients + loader)
├── plots/              Goodman diagram generation
└── report/             PDF report generation (SpringPDFReport)

tests/                  Tests (pytest)
scripts/regresiones/    Training scripts that regenerate the JSON coefficients (not runtime)
docs/                   Reference material (spreadsheet, figures)
```

## Installation

The project uses [uv](https://docs.astral.sh/uv/):

```bash
uv sync                 # create the environment and install dependencies
```

Or with pip in editable mode:

```bash
pip install -e ".[dev]"
```

## Usage

```python
from springcalc import Material, CompressionSpring

material = Material(material_name="SH")
spring = CompressionSpring(material=material, wire_diameter=2.0)
spring.nr_coils = 8
print(spring.calculate_solid_length())
print(spring.calculate_pitch())
```

Generating a PDF report (spring data, load/travel/diameter curves, and the
Goodman fatigue diagram):

```python
from springcalc.report import SpringPDFReport

report = SpringPDFReport(spring, title="Spring XYZ-123")
report.build("spring_report.pdf")
```

## Tests

```bash
uv run pytest
```

## Retraining the regression models

The included JSON coefficient files are already fitted. To regenerate them:

```bash
uv run python scripts/regresiones/factor_f/factor_f.py
```
