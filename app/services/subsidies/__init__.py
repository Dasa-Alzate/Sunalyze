"""Subvenciones e incentivos al autoconsumo FV (España), por capas y sin Flask.

Expone `SubsidyService.applicable(...)` que devuelve una lista de `Incentive` lista para
alimentar el motor financiero (`app.services.finance.compute`), y `resolve` del catálogo.
"""

from .service import SubsidyService
from .catalog import resolve

__all__ = ['SubsidyService', 'resolve']
