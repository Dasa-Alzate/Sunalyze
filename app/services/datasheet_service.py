
from datetime import datetime

from flask import render_template

from app.services import iv_curve

_KIND_LABEL = {
    'panels': 'Módulo fotovoltaico',
    'inverters': 'Inversor',
    'batteries': 'Batería de almacenamiento',
    'wires': 'Conductor',
}


def _n(value, decimals=2, unit=''):
    if value is None:
        return None
    if float(value) == int(float(value)) and decimals == 0:
        text = f'{int(float(value))}'
    else:
        text = f'{float(value):.{decimals}f}'.rstrip('0').rstrip('.')
    return f'{text} {unit}'.strip()


def _rows(pairs):
    return [(label, value) for label, value in pairs if value is not None]


def _brand_and_model(row):
    catalog = getattr(row, 'catalog', None)
    brand = catalog.nombre if catalog else None
    nombre = getattr(row, 'nombre', None) or ''
    if brand and nombre.lower().startswith(brand.lower()):
        return brand, nombre[len(brand):].strip() or nombre
    return brand, nombre


def _panel_context(row):
    area = None
    if row.height and row.width:
        area = (row.height / 1000.0) * (row.width / 1000.0)
    efficiency = row.y
    if efficiency is None and row.power and area:
        efficiency = row.power / (area * 1000.0) * 100.0

    headline = _rows([
        ('Potencia nominal', _n(row.power, 0, 'Wp')),
        ('Eficiencia', _n(efficiency, 2, '%')),
        ('Tensión circuito abierto', _n(row.voc, 2, 'V')),
        ('Corriente cortocircuito', _n(row.isc, 2, 'A')),
    ])
    electrical = _rows([
        ('Potencia máxima (Pmax)', _n(row.power, 0, 'Wp')),
        ('Tensión en el punto de máxima potencia (Vmp)', _n(row.vmp, 2, 'V')),
        ('Corriente en el punto de máxima potencia (Imp)', _n(row.imp, 2, 'A')),
        ('Tensión en circuito abierto (Voc)', _n(row.voc, 2, 'V')),
        ('Corriente de cortocircuito (Isc)', _n(row.isc, 2, 'A')),
        ('Eficiencia del módulo', _n(efficiency, 2, '%')),
        ('Factor de forma (FF)', _n(
            (row.vmp * row.imp) / (row.voc * row.isc) * 100
            if all(v for v in (row.vmp, row.imp, row.voc, row.isc)) else None, 1, '%')),
    ])
    thermal = _rows([
        ('Coeficiente de temperatura de Pmax (γ)', _n(row.tcp, 3, '%/°C')),
        ('Coeficiente de temperatura de Voc (β)', _n(row.tcv, 3, '%/°C')),
        ('Temperatura nominal de operación (NOCT)', _n(row.t_noct, 1, '°C')),
    ])
    mechanical = _rows([
        ('Alto', _n(row.height, 0, 'mm')),
        ('Ancho', _n(row.width, 0, 'mm')),
        ('Superficie', _n(area, 2, 'm²')),
    ])
    chart = ''
    if all(v for v in (row.voc, row.vmp, row.imp, row.isc)):
        chart = iv_curve.render(row.voc, row.vmp, row.imp, row.isc)
    return {'headline': headline, 'blocks': [
        ('Características eléctricas en STC', electrical),
        ('Comportamiento térmico', thermal),
        ('Datos mecánicos', mechanical),
    ], 'chart': chart, 'chart_caption':
        'Curva I-V y P-V en STC (1000 W/m², 25 °C, AM 1,5), con familia '
        'de curvas a irradiancia decreciente.',
        'stc_note': 'STC: 1000 W/m², temperatura de célula 25 °C, masa de aire AM 1,5.'}


def _inverter_context(row):
    headline = _rows([
        ('Potencia nominal CA', _n(row.power, 2, 'kW')),
        ('Tensión máxima CC', _n(row.vmax, 0, 'V')),
        ('Eficiencia máxima', _n(row.y, 1, '%')),
        ('Corriente máx. salida', _n(row.I_max_output, 2, 'A')),
    ])
    dc = _rows([
        ('Tensión máxima de entrada CC', _n(row.vmax, 0, 'V')),
        ('Corriente máxima de entrada CC', _n(row.I_max_input, 2, 'A')),
    ])
    ac = _rows([
        ('Potencia nominal CA', _n(row.power, 2, 'kW')),
        ('Potencia máxima aparente', _n(row.power_max, 2, 'kVA')),
        ('Corriente máxima de salida CA', _n(row.I_max_output, 2, 'A')),
    ])
    general = _rows([
        ('Eficiencia máxima', _n(row.y, 1, '%')),
        ('Relación CC/CA máxima recomendada', _n(
            1.3 if row.power else None, 2, '')),
    ])
    return {'headline': headline, 'blocks': [
        ('Entrada CC (fotovoltaica)', dc),
        ('Salida CA (red)', ac),
        ('Datos generales', general),
    ], 'chart': '', 'chart_caption': '',
        'stc_note': 'Valores según ficha del fabricante; verificar la ventana MPP '
                    'antes del dimensionado de strings.'}


def _battery_context(row):
    usable = row.usable_kwh
    if usable is None and row.capacity_kwh and row.dod:
        usable = row.capacity_kwh * row.dod / 100.0
    headline = _rows([
        ('Capacidad nominal', _n(row.capacity_kwh, 2, 'kWh')),
        ('Potencia de descarga', _n(row.power_kw, 2, 'kW')),
        ('Tensión nominal', _n(row.voltage, 0, 'V')),
        ('Energía útil', _n(usable, 2, 'kWh')),
    ])
    energy = _rows([
        ('Capacidad nominal', _n(row.capacity_kwh, 2, 'kWh')),
        ('Energía útil', _n(usable, 2, 'kWh')),
        ('Profundidad de descarga (DoD)', _n(row.dod, 0, '%')),
        ('Rendimiento de ciclo completo', _n(row.round_trip_efficiency, 1, '%')),
    ])
    power = _rows([
        ('Potencia máxima de descarga continua', _n(row.power_kw, 2, 'kW')),
        ('Tensión nominal', _n(row.voltage, 0, 'V')),
        ('Tecnología', row.technology),
        ('Ciclos de vida', _n(row.max_cycles, 0, 'ciclos')),
    ])
    mechanical = _rows([
        ('Alto', _n(row.height, 0, 'mm')),
        ('Ancho', _n(row.width, 0, 'mm')),
        ('Profundidad', _n(row.depth, 0, 'mm')),
    ])
    return {'headline': headline, 'blocks': [
        ('Energía', energy),
        ('Potencia y tecnología', power),
        ('Datos mecánicos', mechanical),
    ], 'chart': '', 'chart_caption': '',
        'stc_note': 'La tensión nominal puede no estar publicada por la fuente; '
                    'verificar en la ficha del fabricante.'}


_BUILDERS = {
    'panels': _panel_context,
    'inverters': _inverter_context,
    'batteries': _battery_context,
}


class DatasheetService:

    @staticmethod
    def context(resource, row, org_name=None):
        builder = _BUILDERS.get(resource)
        if builder is None:
            raise ValueError(f'No hay plantilla de ficha para «{resource}».')
        brand, model = _brand_and_model(row)
        data = builder(row)
        data.update({
            'kind_label': _KIND_LABEL.get(resource, 'Equipo'),
            'brand': brand or '—',
            'model': model or getattr(row, 'nombre', '—'),
            'full_name': getattr(row, 'nombre', ''),
            'org_name': org_name,
            'generated_at': datetime.utcnow().strftime('%d/%m/%Y'),
            'source': row.source,
            'source_url': row.source_url,
            'scraped_at': row.scraped_at.strftime('%d/%m/%Y') if row.scraped_at else None,
            'verified_by': row.verified_by,
            'verified_at': row.verified_at.strftime('%d/%m/%Y') if row.verified_at else None,
            'needs_review': row.needs_review,
            'review_notes': row.review_notes,
            'datasheet_url': getattr(row, 'datasheet', None),
        })
        return data

    @staticmethod
    def render_html(resource, row, org_name=None):
        return render_template('datasheet.html',
                               **DatasheetService.context(resource, row, org_name))
