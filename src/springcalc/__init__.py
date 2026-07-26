"""springcalc — spring calculation library (compression, extension, and torsion).

Main public API:
    - CompressionSpring, ExtensionSpring, TorsionSpring: calculations per spring type.
    - Material, get_available_materials: material data.
    - GoodmanData, GoodmanAnalyzer, Goodman: fatigue analysis (Goodman diagram).
"""

from springcalc.lineal.compresion import CompressionSpring
from springcalc.lineal.traccion import ExtensionSpring
from springcalc.lineal.torsion import TorsionSpring
from springcalc.lineal.goodman import Goodman, GoodmanAnalyzer, GoodmanData
from springcalc.pymodels.material import Material, get_available_materials
from springcalc.report import SpringPDFReport

__version__ = "0.1.0"

__all__ = [
    "CompressionSpring",
    "ExtensionSpring",
    "TorsionSpring",
    "Material",
    "get_available_materials",
    "GoodmanData",
    "GoodmanAnalyzer",
    "Goodman",
    "SpringPDFReport",
    "__version__",
]
