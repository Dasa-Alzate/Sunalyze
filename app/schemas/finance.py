
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator


class FinancingTerms(BaseModel):
    amount: float = Field(ge=0)
    interest_rate: float = Field(default=0.0, ge=0, le=1)
    term_years: int = Field(default=0, ge=0, le=40)


class Incentive(BaseModel):
    kind: str = Field(default='capex_reduction')
    amount: float = Field(ge=0)
    year: int = Field(default=1, ge=1)
    label: Optional[str] = Field(default=None, max_length=120)


class FinancialAssumptions(BaseModel):
    capex_total: Optional[float] = Field(default=None, ge=0)
    capex_equipment: Optional[float] = Field(default=None, ge=0)
    capex_labor: Optional[float] = Field(default=None, ge=0)
    capex_legalization: Optional[float] = Field(default=None, ge=0)
    iva_pct: float = Field(default=0.21, ge=0, le=1)

    tariff_eur_kwh: float = Field(default=0.15, ge=0)
    annual_consumption_kwh: Optional[float] = Field(default=None, ge=0)
    self_consumption_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    surplus_price_eur_kwh: float = Field(default=0.06, ge=0)

    lifetime_years: int = Field(default=25, ge=1, le=50)
    discount_rate: float = Field(default=0.04, ge=0, le=1)
    tariff_escalation_pct: float = Field(default=0.025, ge=-1, le=1)
    panel_degradation_pct: float = Field(default=0.005, ge=0, le=1)
    om_cost_eur_year: float = Field(default=0.0, ge=0)
    emission_factor_kg_kwh: float = Field(default=0.25, ge=0)

    financing: Optional[FinancingTerms] = None
    incentives: List[Incentive] = Field(default_factory=list)

    @model_validator(mode='after')
    def _require_some_capex(self):
        has_breakdown = any(v is not None for v in
                            (self.capex_equipment, self.capex_labor, self.capex_legalization))
        if self.capex_total is None and not has_breakdown:
            raise ValueError('Indica capex_total o un desglose (equipo/mano_obra/legalizacion).')
        return self


class ComputeRequest(BaseModel):
    assumptions: FinancialAssumptions
    production_kwh_year: Optional[float] = Field(default=None, ge=0)
    self_consumption_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    apply_subsidies: bool = False
    ccaa: Optional[str] = Field(default=None, max_length=80)
    municipio: Optional[str] = Field(default=None, max_length=120)


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    assumptions: FinancialAssumptions
    is_default: bool = False
    production_kwh_year: Optional[float] = Field(default=None, ge=0)
    self_consumption_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    apply_subsidies: bool = False
    ccaa: Optional[str] = Field(default=None, max_length=80)
    municipio: Optional[str] = Field(default=None, max_length=120)


class ScenarioUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    assumptions: Optional[FinancialAssumptions] = None
    is_default: Optional[bool] = None
    production_kwh_year: Optional[float] = Field(default=None, ge=0)
    self_consumption_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    apply_subsidies: bool = False
    ccaa: Optional[str] = Field(default=None, max_length=80)
    municipio: Optional[str] = Field(default=None, max_length=120)
