import math


# Table A ampacities at 40 C for copper, XLPE, two loaded conductors, method B1.
AMPACITY_B1_XLPE_CU_2C = (
    (4, 38), (6, 49), (10, 68), (16, 91), (25, 115), (35, 143),
    (50, 174), (70, 223), (95, 271), (120, 314), (150, 359),
    (185, 409), (240, 489)
)

AMBIENT_TEMPERATURE_ASSUMPTION_C = 40
MIN_DC_SECTION_MM2 = 4
MIN_AC_SECTION_MM2 = 6
COPPER_RESISTIVITY_OHM_MM2_M = 0.0225
TOTAL_VOLTAGE_DROP_LIMIT_PCT = 1.5
VOLTAGE_DROP_PER_RUN_PCT = TOTAL_VOLTAGE_DROP_LIMIT_PCT / 2
AC_NOMINAL_VOLTAGE_V = 230
DESIGN_CURRENT_FACTOR = 1.25


def select_section(current_a, minimum_section_mm2):
    if current_a is None or not math.isfinite(float(current_a)) or float(current_a) <= 0:
        return None
    for section_mm2, ampacity_a in AMPACITY_B1_XLPE_CU_2C:
        if section_mm2 >= minimum_section_mm2 and ampacity_a >= float(current_a):
            return {
                'section_mm2': section_mm2,
                'ampacity_a': ampacity_a,
                'table_ampacity_a': ampacity_a,
            }
    return None


def maximum_length_m(current_a, voltage_v, section_mm2):
    if current_a is None or voltage_v is None or section_mm2 is None:
        return None
    current_a = float(current_a)
    voltage_v = float(voltage_v)
    if current_a <= 0 or voltage_v <= 0:
        return None
    allowed_drop_v = voltage_v * VOLTAGE_DROP_PER_RUN_PCT / 100
    return allowed_drop_v * float(section_mm2) / (
        2 * current_a * COPPER_RESISTIVITY_OHM_MM2_M
    )


def size_run(current_a, minimum_section_mm2, voltage_v=None):
    nominal_current_a = float(current_a) if current_a is not None else None
    design_current_a = nominal_current_a * DESIGN_CURRENT_FACTOR if nominal_current_a is not None else None
    selected = select_section(design_current_a, minimum_section_mm2)
    return {
        'nominal_current_a': round(nominal_current_a, 2) if nominal_current_a is not None else None,
        'current_a': round(design_current_a, 2) if design_current_a is not None else None,
        'current_factor': DESIGN_CURRENT_FACTOR,
        'sizing_status': 'ok' if selected else ('missing_current' if current_a is None else 'exceeds_table'),
        'minimum_section_mm2': minimum_section_mm2,
        'section_mm2': selected['section_mm2'] if selected else None,
        'ampacity_a': selected['ampacity_a'] if selected else None,
        'voltage_v': round(float(voltage_v), 2) if voltage_v is not None else None,
        'maximum_length_m': round(
            maximum_length_m(design_current_a, voltage_v, selected['section_mm2']), 2,
        ) if selected and voltage_v is not None else None,
        'voltage_drop_allowance_pct': VOLTAGE_DROP_PER_RUN_PCT,
    }


def size_installation(panel, inverter, cell_amount, max_cell_amount=None):
    dc_current_a = getattr(panel, 'isc', None) if panel else None
    ac_current_a = getattr(inverter, 'I_max_output', None) if inverter else None

    dc_voltage_v = None
    if panel and panel.vmp and cell_amount and float(cell_amount) > 0:
        modules_in_series = math.ceil(float(cell_amount))
        if max_cell_amount and float(max_cell_amount) > 0:
            modules_in_series = min(modules_in_series, math.floor(float(max_cell_amount)))
        if modules_in_series > 0:
            dc_voltage_v = float(panel.vmp) * modules_in_series

    dc = size_run(dc_current_a, MIN_DC_SECTION_MM2, dc_voltage_v)
    dc['modules_in_series'] = modules_in_series if dc_voltage_v is not None else None
    ac = size_run(ac_current_a, MIN_AC_SECTION_MM2, AC_NOMINAL_VOLTAGE_V)
    return {
        'standard': 'ITC-BT-19 / C.52-1 bis',
        'installation_method': 'B1',
        'insulation': 'XLPE 90 °C',
        'conductor_material': 'Cu',
        'loaded_conductors': 2,
        'ambient_temperature_assumption_c': AMBIENT_TEMPERATURE_ASSUMPTION_C,
        'ac_voltage_assumption': '230 V monofásica',
        'current_basis': 'Isc × 1,25 en CC; Imax_out × 1,25 en CA, sin multiplicar paralelos',
        'voltage_drop_total_limit_pct': TOTAL_VOLTAGE_DROP_LIMIT_PCT,
        'voltage_drop_per_run_pct': VOLTAGE_DROP_PER_RUN_PCT,
        'copper_resistivity_ohm_mm2_m': COPPER_RESISTIVITY_OHM_MM2_M,
        'dc': dc,
        'ac': ac,
        'ground_section_mm2': ac['section_mm2'],
        'ground_rule': 'Misma sección que el conductor de fase CA',
    }