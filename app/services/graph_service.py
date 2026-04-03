"""Servicio de generación de gráficos SVG para la memoria técnica."""

import pygal
from pygal.style import Style

MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
          'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

_COMMON_STYLE = dict(
    background='transparent',
    plot_background='transparent',
    foreground='#333',
    foreground_strong='#333',
    foreground_subtle='#666',
    guide_stroke_color='rgba(0,0,0,0.15)',
    major_guide_stroke_color='rgba(0,0,0,0.5)',
    font_family='Arial, Helvetica, sans-serif',
    label_font_size=10,
    major_label_font_size=10,
    title_font_size=13,
    legend_font_size=10,
)

CHART_STYLE = Style(**_COMMON_STYLE, colors=('#3498db',))
BALANCE_STYLE = Style(**_COMMON_STYLE, colors=('#f39c12', '#3498db'))

# Distribución mensual del consumo (peso relativo por mes, suma = 1)
# Más consumo en verano (aire acondicionado) e invierno (calefacción)
MONTHLY_CONSUMPTION_WEIGHTS = [
    0.095, 0.085, 0.080, 0.075, 0.070, 0.080,
    0.095, 0.095, 0.080, 0.075, 0.080, 0.090,
]

BASE_CONFIG = dict(
    style=CHART_STYLE,
    width=720,
    height=340,
    show_legend=False,
    print_values=True,
    print_values_position='top',
    value_formatter=lambda x: f'{x:.0f}',
    x_labels=MONTHS,
    margin=20,
    show_y_guides=True,
    rounded_bars=2,
)


class GraphService:
    """Genera gráficos SVG de producción e irradiancia para la memoria técnica."""

    @staticmethod
    def generate_monthly_production(monthly_data: list[float]) -> str:
        """Gráfico de barras con producción mensual en Wh."""
        monthly_wh = [round(v * 1000) for v in monthly_data]
        chart = pygal.Bar(**BASE_CONFIG)
        chart.title = 'Producción mensual estimada (Wh)'
        chart.add('Producción', monthly_wh)
        return chart.render(is_unicode=True)

    @staticmethod
    def generate_monthly_irradiance(monthly_data: list[float]) -> str:
        """Gráfico de barras con irradiancia mensual en kWh/m²."""
        chart = pygal.Bar(**BASE_CONFIG)
        chart.title = 'Irradiación mensual en el plano (kWh/m²)'
        chart.add('Irradiación', monthly_data)
        return chart.render(is_unicode=True)

    @staticmethod
    def generate_energy_balance(monthly_production: list[float], annual_consumption: float) -> str:
        """Gráfico de barras agrupadas: producción vs consumo estimado mensual."""
        monthly_consumption = [round(annual_consumption * w) for w in MONTHLY_CONSUMPTION_WEIGHTS]

        chart = pygal.Bar(
            style=BALANCE_STYLE,
            width=720,
            height=360,
            show_legend=True,
            legend_at_bottom=True,
            print_values=True,
            print_values_position='top',
            value_formatter=lambda x: f'{x:.0f}',
            x_labels=MONTHS,
            margin=20,
            show_y_guides=True,
            rounded_bars=2,
        )
        chart.title = 'Balance energético mensual (kWh)'
        chart.add('Consumo estimado', monthly_consumption)
        chart.add('Producción FV', [round(v) for v in monthly_production])
        return chart.render(is_unicode=True)
