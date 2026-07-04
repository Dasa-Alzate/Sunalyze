"""Esquema de validacion del formulario de la memoria tecnica (PDF).

Tipa los campos del formulario que llegan como `request.form`. La presencia de
los campos obligatorios la sigue verificando MemoriaService.REQUIRED_FIELDS; este
esquema aporta validacion de tipo y rango (422 ante basura, negativos o fuera de
rango). Los campos vacios se normalizan a None antes de validar para no romper los
opcionales. El servicio re-lee el formulario crudo, asi que validar aqui no altera
las variables de plantilla ni los SVG generados.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MemoriaFormSchema(BaseModel):
    model_config = {'extra': 'ignore'}

    panel_id: Optional[int] = Field(default=None, gt=0)
    inverter_id: Optional[int] = Field(default=None, gt=0)
    battery_id: Optional[int] = Field(default=None, gt=0)
    battery_quantity: Optional[int] = Field(default=None, ge=1, le=1000)

    hired_power_kw: Optional[float] = Field(default=None, gt=0, le=100000)
    input_v: Optional[float] = Field(default=None, gt=0, le=100000)
    panels_peak_power_kw: Optional[float] = Field(default=None, gt=0, le=100000)
    panels_number: Optional[int] = Field(default=None, ge=1, le=100000)
    mppt_inputs: Optional[int] = Field(default=None, ge=1, le=100)

    panels_surface: Optional[float] = Field(default=None, ge=0, le=1000000)
    panels_inclination: Optional[float] = Field(default=None, ge=0, le=90)
    panels_azimut: Optional[float] = Field(default=None, ge=-180, le=180)
    panel_temp_min_limit: Optional[float] = Field(default=None, ge=-100, le=200)
    panel_temp_max_limit: Optional[float] = Field(default=None, ge=-100, le=200)

    wire_dc_length: Optional[float] = Field(default=None, ge=0, le=100000)
    wire_ac_length: Optional[float] = Field(default=None, ge=0, le=100000)
    wire_ground_length: Optional[float] = Field(default=None, ge=0, le=100000)

    protections_dc_thermal_v_max: Optional[float] = Field(default=None, gt=0, le=2000)
    protections_dc_breaker_i: Optional[float] = Field(default=None, gt=0, le=500)
    protections_ac_thermal_i: Optional[float] = Field(default=None, gt=0, le=2000)
    protections_ac_diff_i: Optional[float] = Field(default=None, gt=0, le=2000)

    panels_output_i_max_expected: Optional[float] = Field(default=None, gt=0, le=10000)
    panels_output_i_max_oversized: Optional[float] = Field(default=None, gt=0, le=10000)
    inverter_output_i_max_expected: Optional[float] = Field(default=None, gt=0, le=10000)

    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    altitude: Optional[float] = Field(default=None, ge=-500, le=10000)

    annual_production: Optional[float] = Field(default=None, ge=0, le=1000000000)
    annual_irradiance: Optional[float] = Field(default=None, ge=0, le=1000000000)

    location: Optional[str] = Field(default=None, max_length=200)
    client_name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=300)
    zipcode: Optional[str] = Field(default=None, max_length=20)
    catastral_reference: Optional[str] = Field(default=None, max_length=60)
    energy_company_name: Optional[str] = Field(default=None, max_length=120)
    energy_company_cups: Optional[str] = Field(default=None, max_length=40)
    input_v_type: Optional[str] = Field(default=None, max_length=40)
    inyection_type: Optional[str] = Field(default=None, max_length=80)
    panels_place: Optional[str] = Field(default=None, max_length=120)
    panels_disposition: Optional[str] = Field(default=None, max_length=120)
    inverter_place: Optional[str] = Field(default=None, max_length=120)
    inverter_phases: Optional[str] = Field(default=None, max_length=40)
    protections_ac_transitory_surge_model: Optional[str] = Field(default=None, max_length=120)
    wire_dc_section: Optional[str] = Field(default=None, max_length=60)
    wire_ac_section: Optional[str] = Field(default=None, max_length=60)
    wire_ground_section: Optional[str] = Field(default=None, max_length=60)
    date: Optional[str] = Field(default=None, max_length=40)

    @field_validator('*', mode='before')
    @classmethod
    def _empty_to_none(cls, value):
        """Normaliza cadenas vacias o solo-espacios a None (opcional ausente)."""
        if isinstance(value, str) and value.strip() == '':
            return None
        return value
