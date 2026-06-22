"""Estudio económico de una instalación fotovoltaica: dominio puro, sin Flask.

`compute` recibe los supuestos (objeto con los atributos de FinancialAssumptions),
la producción anual estimada (kWh/año, del analysis_service) y opcionalmente el
ratio de autoconsumo (si falta, se toma el del supuesto o un default). Devuelve un
desglose completo: cashflow año a año, ahorro del año 1, payback simple/descontado,
ROI, TIR, VAN, LCOE y CO₂ evitado.

Puntos de enchufe para fases futuras:
- `incentives`: lista de incentivos que reducen el CAPEX neto (Fase 2,
  subvenciones) o aportan cashflow en un año concreto. En Fase 1 llega vacía.
- `production_kwh_year` y `self_consumption_ratio`: una fuente horaria futura
  (Datadis/ESIOS) solo tiene que afinar estos valores o el bloque de ahorro anual.
"""

from .metrics import npv, irr, payback_period

DEFAULT_SELF_CONSUMPTION_RATIO = 0.65
DEFAULT_EMISSION_FACTOR_KG_KWH = 0.25


def _gross_capex(a):
    if a.capex_total is not None:
        return float(a.capex_total)
    return float((a.capex_equipment or 0.0)
                 + (a.capex_labor or 0.0)
                 + (a.capex_legalization or 0.0))


def _capex_reductions(incentives):
    total = 0.0
    cashflow_by_year = {}
    for inc in incentives or []:
        kind = inc.get('kind', 'capex_reduction')
        amount = float(inc.get('amount', 0.0) or 0.0)
        if kind == 'capex_reduction':
            total += amount
        elif kind == 'cashflow':
            year = int(inc.get('year', 1) or 1)
            cashflow_by_year[year] = cashflow_by_year.get(year, 0.0) + amount
    return total, cashflow_by_year


def _incentives_breakdown(incentives):
    items = []
    total = 0.0
    for inc in incentives or []:
        amount = float(inc.get('amount', 0.0) or 0.0)
        items.append({
            'kind': inc.get('kind', 'capex_reduction'),
            'amount': round(amount, 2),
            'year': int(inc.get('year', 1) or 1),
            'label': inc.get('label'),
        })
        total += amount
    return {'items': items, 'total_eur': round(total, 2)}


def _annuity(principal, annual_rate, years):
    if principal <= 0 or years <= 0:
        return 0.0
    if annual_rate == 0:
        return principal / years
    r = annual_rate
    return principal * r * (1 + r) ** years / ((1 + r) ** years - 1)


def _resolve_self_consumption(a, self_consumption_ratio):
    if self_consumption_ratio is not None:
        ratio = self_consumption_ratio
    elif getattr(a, 'self_consumption_ratio', None) is not None:
        ratio = a.self_consumption_ratio
    else:
        ratio = DEFAULT_SELF_CONSUMPTION_RATIO
    return min(1.0, max(0.0, float(ratio)))


def compute(assumptions, production_kwh_year, self_consumption_ratio=None, incentives=None):
    a = assumptions
    production = float(production_kwh_year or 0.0)
    ratio = _resolve_self_consumption(a, self_consumption_ratio)

    gross_capex = _gross_capex(a)
    capex_with_vat = gross_capex * (1.0 + float(a.iva_pct))
    incentive_reduction, incentive_cashflow = _capex_reductions(incentives)
    net_capex = max(0.0, capex_with_vat - incentive_reduction)

    financing_amount = 0.0
    loan_annuity = 0.0
    loan_term = 0
    if getattr(a, 'financing', None) is not None:
        financing_amount = min(float(a.financing.amount or 0.0), net_capex)
        loan_term = int(a.financing.term_years or 0)
        loan_annuity = _annuity(financing_amount, float(a.financing.interest_rate or 0.0), loan_term)

    initial_investment = net_capex - financing_amount

    emission_factor = float(getattr(a, 'emission_factor_kg_kwh', None) or DEFAULT_EMISSION_FACTOR_KG_KWH)
    annual_consumption = float(getattr(a, 'annual_consumption_kwh', None) or 0.0)

    degradation = float(a.panel_degradation_pct)
    escalation = float(a.tariff_escalation_pct)
    discount = float(a.discount_rate)
    lifetime = int(a.lifetime_years)

    years = []
    cashflows_after_year0 = []
    co2_lifetime = 0.0
    discounted_costs = 0.0
    discounted_energy = 0.0

    for t in range(1, lifetime + 1):
        prod_t = production * ((1.0 - degradation) ** (t - 1))
        tariff_t = float(a.tariff_eur_kwh) * ((1.0 + escalation) ** (t - 1))
        surplus_price_t = float(a.surplus_price_eur_kwh) * ((1.0 + escalation) ** (t - 1))

        self_kwh = prod_t * ratio
        surplus_kwh = prod_t * (1.0 - ratio)

        saving_self = self_kwh * tariff_t
        grid_import_kwh = max(0.0, annual_consumption - self_kwh)
        surplus_cap = grid_import_kwh * tariff_t
        saving_surplus = min(surplus_kwh * surplus_price_t, surplus_cap)

        om_t = float(a.om_cost_eur_year) * ((1.0 + escalation) ** (t - 1))
        loan_t = loan_annuity if t <= loan_term else 0.0

        cashflow_t = saving_self + saving_surplus - om_t - loan_t + incentive_cashflow.get(t, 0.0)

        discount_factor = (1.0 + discount) ** t
        co2_t = prod_t * emission_factor
        co2_lifetime += co2_t
        discounted_costs += (om_t + loan_t) / discount_factor
        discounted_energy += prod_t / discount_factor

        cashflows_after_year0.append(cashflow_t)
        years.append({
            'year': t,
            'production_kwh': round(prod_t, 2),
            'tariff_eur_kwh': round(tariff_t, 5),
            'self_consumed_kwh': round(self_kwh, 2),
            'surplus_kwh': round(surplus_kwh, 2),
            'saving_self_eur': round(saving_self, 2),
            'saving_surplus_eur': round(saving_surplus, 2),
            'om_eur': round(om_t, 2),
            'loan_payment_eur': round(loan_t, 2),
            'cashflow_eur': round(cashflow_t, 2),
            'discounted_cashflow_eur': round(cashflow_t / discount_factor, 2),
            'co2_avoided_kg': round(co2_t, 2),
        })

    full_series = [-initial_investment] + cashflows_after_year0
    npv_value = npv(discount, full_series)
    irr_value = irr(full_series)
    payback_simple = payback_period(initial_investment, cashflows_after_year0)

    discounted_cashflows = [cf / ((1.0 + discount) ** t)
                            for t, cf in enumerate(cashflows_after_year0, start=1)]
    payback_discounted = payback_period(initial_investment, discounted_cashflows)

    total_cashflow = sum(cashflows_after_year0)
    roi = ((total_cashflow - initial_investment) / initial_investment) if initial_investment > 0 else None

    lcoe = ((initial_investment + discounted_costs) / discounted_energy) if discounted_energy > 0 else None

    year1 = years[0] if years else {}

    return {
        'inputs': {
            'production_kwh_year': round(production, 2),
            'self_consumption_ratio': round(ratio, 4),
            'lifetime_years': lifetime,
            'discount_rate': discount,
            'emission_factor_kg_kwh': emission_factor,
        },
        'capex': {
            'gross_eur': round(gross_capex, 2),
            'iva_pct': float(a.iva_pct),
            'with_vat_eur': round(capex_with_vat, 2),
            'incentive_reduction_eur': round(incentive_reduction, 2),
            'net_eur': round(net_capex, 2),
            'financed_eur': round(financing_amount, 2),
            'initial_investment_eur': round(initial_investment, 2),
        },
        'annual_saving_year1_eur': round(
            (year1.get('saving_self_eur', 0.0) + year1.get('saving_surplus_eur', 0.0)), 2),
        'incentives': _incentives_breakdown(incentives),
        'metrics': {
            'payback_simple_years': round(payback_simple, 2) if payback_simple is not None else None,
            'payback_discounted_years': round(payback_discounted, 2) if payback_discounted is not None else None,
            'roi': round(roi, 4) if roi is not None else None,
            'irr': round(irr_value, 5) if irr_value is not None else None,
            'npv_eur': round(npv_value, 2),
            'lcoe_eur_kwh': round(lcoe, 5) if lcoe is not None else None,
            'co2_avoided_year1_kg': round(year1.get('co2_avoided_kg', 0.0), 2),
            'co2_avoided_lifetime_kg': round(co2_lifetime, 2),
        },
        'cashflow': years,
    }
