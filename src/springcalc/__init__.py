"""muelles — biblioteca de cálculo de muelles (compresión, tracción y torsión).

API pública principal:
    - MuelleCompresion, MuelleTraccion, MuelleTorsion: cálculo por tipo de muelle.
    - Material, get_available_materials: datos de materiales.
    - GoodmanData, GoodmanAnalyzer, Goodman: análisis de fatiga (diagrama de Goodman).
"""

from muelles.lineal.compresion import MuelleCompresion
from muelles.lineal.traccion import MuelleTraccion
from muelles.lineal.torsion import MuelleTorsion
from muelles.lineal.goodman import Goodman, GoodmanAnalyzer, GoodmanData
from muelles.pymodels.material import Material, get_available_materials

__version__ = "0.1.0"

__all__ = [
    "MuelleCompresion",
    "MuelleTraccion",
    "MuelleTorsion",
    "Material",
    "get_available_materials",
    "GoodmanData",
    "GoodmanAnalyzer",
    "Goodman",
    "__version__",
]
