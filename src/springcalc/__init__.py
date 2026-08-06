"""springcalc — spring calculation library (compression, extension, and torsion).

Main public API:
    - CompressionSpring, ExtensionSpring, TorsionSpring: calculations per spring type.
    - Material, get_available_materials: material data.
    - GoodmanData, GoodmanAnalyzer, Goodman: fatigue analysis (Goodman diagram).
"""

from springcalc.lineal.compresion import CompressionSpring
from springcalc.lineal.generic_compression import CompressionSpringGeneral
from springcalc.lineal.extension import ExtensionSpring
from springcalc.lineal.torsion import TorsionSpring
from springcalc.lineal.animation import CompressionAnimator
from springcalc.lineal.goodman import Goodman, GoodmanAnalyzer, GoodmanData
from springcalc.pymodels.material import Material, get_available_materials, get_materials_dataframe
from springcalc.pymodels.positions import (
    LinearPosition,
    AngularPosition,
    LinearLoadPosition,
    AngularLoadPosition,
    LinearPositionsTable,
    AngularPositionsTable,
)
from springcalc.pymodels.wire_characteristics import get_wire_tolerance, get_RMa_range
from springcalc.plots.goodman_diagram import generate_goodman_diagram
from springcalc.report import SpringPDFReport
from springcalc.pymodels.units import ureg
from springcalc.lineal.plotting import interactive_backend
from importlib.metadata import version as _version

__version__ = _version("springcalc")

__all__ = [
    "CompressionSpring",
    "CompressionSpringGeneral",
    "ExtensionSpring",
    "TorsionSpring",
    "CompressionAnimator",
    "Material",
    "get_available_materials",
    "get_materials_dataframe",
    "LinearPosition",
    "AngularPosition",
    "LinearLoadPosition",
    "AngularLoadPosition",
    "LinearPositionsTable",
    "AngularPositionsTable",
    "get_wire_tolerance",
    "get_RMa_range",
    "GoodmanData",
    "GoodmanAnalyzer",
    "Goodman",
    "generate_goodman_diagram",
    "SpringPDFReport",
    "ureg",
    "interactive_backend",
    "__version__",
]
