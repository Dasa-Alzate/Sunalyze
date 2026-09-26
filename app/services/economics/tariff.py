"""Tarifa eléctrica por periodos sobre el calendario canónico.

Ventanas 2.0TD peninsulares: laborables 0-8 valle, 8-10 y 14-18 y 22-24 llano,
10-14 y 18-22 punta; sábados y domingos valle completo (festivos fuera de v1).
Los precios por defecto son editables por organización (OrgTariffProfile).
"""

from app.services.consumption.expanders import DAYS_PER_MONTH, day_type_of

PERIODS = ('punta', 'llano', 'valle')

DEFAULT_TARIFF = {
    'nombre': '2.0TD',
    'precio_punta': 0.193,
    'precio_llano': 0.135,
    'precio_valle': 0.083,
    'precio_excedente': 0.06,
    'precio_potencia_p1_dia': 0.077,
    'precio_potencia_p2_dia': 0.0077,
    'impuesto_electricidad': 0.0511,
    'iva_pct': 21.0,
    'alquiler_contador_mes': 0.81,
}


def period_of(day_of_year, hour):
    if day_type_of(day_of_year) != 'laborable':
        return 'valle'
    if hour < 8:
        return 'valle'
    if 10 <= hour < 14 or 18 <= hour < 22:
        return 'punta'
    return 'llano'


def price_of(tariff, period):
    return tariff[f'precio_{period}']


def monthly_bill(tariff, energy_cost, potencia_kw, days, surplus_credit, hucha):
    """Factura de un mes con compensación simplificada y hucha arrastrada.

    Devuelve (factura_neta, hucha_restante, factura_bruta). El crédito de
    excedentes solo descuenta hasta dejar la factura bruta en cero: el saldo
    sobrante se arrastra pero nunca se convierte en dinero cobrable.
    """
    potencia = potencia_kw * (tariff['precio_potencia_p1_dia'] + tariff['precio_potencia_p2_dia']) * days
    subtotal = energy_cost + potencia + tariff['alquiler_contador_mes']
    base = subtotal * (1.0 + tariff['impuesto_electricidad'])
    bruta = base * (1.0 + tariff['iva_pct'] / 100.0)
    hucha += surplus_credit
    descuento = min(bruta, hucha)
    return bruta - descuento, hucha - descuento, bruta


def annual_bill(tariff, monthly_energy_cost, monthly_surplus_credit, potencia_kw):
    """Suma las doce facturas arrastrando la hucha mes a mes."""
    total = 0.0
    hucha = 0.0
    months = []
    for m in range(12):
        neta, hucha, bruta = monthly_bill(
            tariff, monthly_energy_cost[m], potencia_kw, DAYS_PER_MONTH[m],
            monthly_surplus_credit[m], hucha)
        total += neta
        months.append({'factura_neta': round(neta, 2), 'factura_bruta': round(bruta, 2),
                       'hucha': round(hucha, 2)})
    return {'total': round(total, 2), 'meses': months, 'hucha_perdida': round(hucha, 2)}
