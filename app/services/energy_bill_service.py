
from datetime import datetime

from flask import render_template

WITHOUT = '#d9920a'
WITH = '#107c41'
GRID_LINE = '#e1dfdd'
AXIS = '#8a8886'
INK = '#242424'
MUTED = '#616161'
FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"

MONTHS = ('Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
          'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic')

PRODUCTION_SHAPE = (0.055, 0.065, 0.083, 0.093, 0.104, 0.108,
                    0.113, 0.106, 0.090, 0.073, 0.056, 0.054)
CONSUMPTION_SHAPE = (0.095, 0.088, 0.084, 0.077, 0.075, 0.078,
                     0.086, 0.086, 0.077, 0.080, 0.085, 0.089)


def _monthly(annual, shape):
    return [annual * f for f in shape]


def _eur(value, decimals=2):
    text = f'{value:,.{decimals}f}'.replace(',', ' ').replace('.', ',')
    return f'{text} €'


def _kwh(value):
    return f'{value:,.0f}'.replace(',', ' ') + ' kWh'


def compute(consumption_kwh, production_kwh, tariff, surplus_price,
            self_consumption_ratio=0.65, fixed_cost_year=0.0):
    months = []
    totals = {'consumo': 0.0, 'autoconsumo': 0.0, 'red': 0.0, 'excedente': 0.0,
              'coste_sin': 0.0, 'coste_con': 0.0, 'compensacion': 0.0,
              'compensacion_aplicada': 0.0, 'termino_fijo': 0.0,
              'energia_red_eur': 0.0}
    cons = _monthly(consumption_kwh, CONSUMPTION_SHAPE)
    prod = _monthly(production_kwh, PRODUCTION_SHAPE)
    fixed_month = fixed_cost_year / 12.0

    for i, name in enumerate(MONTHS):
        c, p = cons[i], prod[i]
        self_used = min(c, p * self_consumption_ratio)
        surplus = max(0.0, p - self_used)
        from_grid = max(0.0, c - self_used)
        cost_without = c * tariff + fixed_month
        compensation = surplus * surplus_price
        grid_cost = from_grid * tariff
        cost_with = max(fixed_month, grid_cost + fixed_month - compensation)
        applied = grid_cost + fixed_month - cost_with
        months.append({
            'name': name, 'consumo': c, 'produccion': p, 'autoconsumo': self_used,
            'red': from_grid, 'excedente': surplus,
            'coste_sin': cost_without, 'coste_con': cost_with,
            'ahorro': cost_without - cost_with,
        })
        totals['consumo'] += c
        totals['autoconsumo'] += self_used
        totals['red'] += from_grid
        totals['excedente'] += surplus
        totals['coste_sin'] += cost_without
        totals['coste_con'] += cost_with
        totals['compensacion'] += compensation
        totals['compensacion_aplicada'] += applied
        totals['termino_fijo'] += fixed_month
        totals['energia_red_eur'] += grid_cost

    totals['produccion'] = sum(prod)
    totals['ahorro'] = totals['coste_sin'] - totals['coste_con']
    totals['ahorro_pct'] = (totals['ahorro'] / totals['coste_sin'] * 100
                            if totals['coste_sin'] else 0.0)
    totals['cobertura_pct'] = (totals['autoconsumo'] / totals['consumo'] * 100
                               if totals['consumo'] else 0.0)
    totals['autoconsumo_pct'] = (totals['autoconsumo'] / totals['produccion'] * 100
                                 if totals['produccion'] else 0.0)
    return months, totals


def render_chart(months, width=560, height=330):
    pad_l, pad_r, pad_t, pad_b = 44, 12, 18, 32
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    top = max(max(m['coste_sin'] for m in months), 1.0) * 1.12
    slot = plot_w / len(months)
    bar_w = min(15.0, slot / 2.5)
    gap = 2.5

    def sy(v):
        return pad_t + plot_h - v / top * plot_h

    parts = [f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>']
    ticks = 4
    for k in range(ticks + 1):
        v = top * k / ticks
        y = sy(v)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + plot_w}" y2="{y:.1f}"'
                     f' stroke="{GRID_LINE}" stroke-width="0.7"/>')
        parts.append(f'<text x="{pad_l - 7}" y="{y + 3.2:.1f}" text-anchor="end"'
                     f' font-family="{FONT}" font-size="9" fill="{MUTED}">{v:.0f} €</text>')

    for i, m in enumerate(months):
        cx = pad_l + slot * (i + 0.5)
        x0 = cx - bar_w - gap / 2
        x1 = cx + gap / 2
        for x, value, color in ((x0, m['coste_sin'], WITHOUT), (x1, m['coste_con'], WITH)):
            h = max(1.0, plot_h - (sy(value) - pad_t))
            parts.append(f'<rect x="{x:.1f}" y="{sy(value):.1f}" width="{bar_w:.1f}"'
                         f' height="{h:.1f}" rx="2" fill="{color}"/>')
        parts.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + 14:.1f}" text-anchor="middle"'
                     f' font-family="{FONT}" font-size="9" fill="{MUTED}">{m["name"]}</text>')

    parts.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}"'
                 f' y2="{pad_t + plot_h}" stroke="{AXIS}" stroke-width="1"/>')

    peak = max(months, key=lambda m: m['ahorro'])
    idx = months.index(peak)
    px = pad_l + slot * (idx + 0.5)
    parts.append(f'<text x="{px:.1f}" y="{sy(peak["coste_sin"]) - 6:.1f}"'
                 f' text-anchor="middle" font-family="{FONT}" font-size="9"'
                 f' font-weight="700" fill="{INK}">−{peak["ahorro"]:.0f} €</text>')
    parts.append(f'<text x="{px:.1f}" y="{sy(peak["coste_sin"]) - 16:.1f}"'
                 f' text-anchor="middle" font-family="{FONT}" font-size="7.5"'
                 f' fill="{MUTED}">mejor mes</text>')

    body = '\n  '.join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
            f' viewBox="0 0 {width} {height}" role="img"'
            f' aria-label="Comparación mensual del coste de la electricidad sin y con'
            f' instalación fotovoltaica">\n  {body}\n</svg>')


class EnergyBillService:

    @staticmethod
    def build(consumption_kwh, production_kwh, tariff=0.15, surplus_price=0.06,
              self_consumption_ratio=0.65, fixed_cost_year=0.0, escalation=0.025,
              lifetime_years=25, client=None, org_name=None, project_name=None,
              installed_kwp=None):
        months, totals = compute(consumption_kwh, production_kwh, tariff,
                                 surplus_price, self_consumption_ratio, fixed_cost_year)
        cumulative = 0.0
        annual = totals['ahorro']
        for year in range(lifetime_years):
            cumulative += annual * ((1 + escalation) ** year)

        return {
            'months': months,
            'totals': totals,
            'chart': render_chart(months),
            'tariff': tariff,
            'surplus_price': surplus_price,
            'self_consumption_ratio': self_consumption_ratio * 100,
            'escalation': escalation * 100,
            'lifetime_years': lifetime_years,
            'lifetime_saving': cumulative,
            'monthly_saving': annual / 12.0,
            'installed_kwp': installed_kwp,
            'client': client,
            'org_name': org_name,
            'project_name': project_name,
            'generated_at': datetime.utcnow().strftime('%d/%m/%Y'),
            'eur': _eur,
            'kwh': _kwh,
            'colors': {'without': WITHOUT, 'with': WITH},
        }

    @staticmethod
    def render_html(**kwargs):
        return render_template('energy_bill.html', **EnergyBillService.build(**kwargs))
