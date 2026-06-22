"""Motor financiero fotovoltaico: dominio puro, sin Flask.

Expone `compute` (cálculo del estudio económico a partir de unos supuestos, la
producción anual y el ratio de autoconsumo) y las primitivas numéricas (`irr`,
`npv`) por si otras capas las necesitan. No importa nada de Flask ni de la BD.
"""

from .engine import compute
from .metrics import irr, npv

__all__ = ['compute', 'irr', 'npv']
