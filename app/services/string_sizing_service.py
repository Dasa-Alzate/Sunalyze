
import math

VOC_COLD_MARGIN = 1.05
VMPP_PROXY_MARGIN = 0.97
ISC_DESIGN_FACTOR = 1.25
DC_AC_RATIO_MAX = 1.3
DC_AC_RATIO_MIN = 0.8
MAX_STRINGS_PER_MPPT = 2
FUSE_THRESHOLD_STRINGS_PER_MPPT = 3

REF_IEC_62548 = 'IEC 62548'
REF_ITC_BT_40 = 'ITC-BT-40'
REF_IEC_61215 = 'IEC 61215'


class StringSizingService:

    @staticmethod
    def evaluate(panel, inverter, site, ctx=None):
        t_min = site.get('coldest_temp')
        t_amb_max = site.get('hottest_temp')
        noct = site.get('noct') or 45.0
        required = site.get('required_panels')

        def want(row, entity, field, unlocks):
            raw = getattr(row, field, None)
            if raw is None and ctx is not None:
                ctx.value(row, entity, field, unlocks)
            return raw

        tcv = want(panel, 'panel', 'tcv',
                   'Ventana de tensión del string en frío y en calor')
        voc = panel.voc
        vmp = panel.vmp
        imp = panel.imp
        isc = want(panel, 'panel', 'isc',
                   'Corriente de diseño del string y límite por MPPT')
        mppt_v_min = want(inverter, 'inverter', 'mppt_v_min',
                          'Número mínimo de módulos en serie (Vmpp caliente)')
        mppt_count = want(inverter, 'inverter', 'mppt_count',
                          'Reparto de las cadenas entre seguidores MPP')
        isc_max_mppt = want(inverter, 'inverter', 'isc_max_per_mppt',
                            'Verificación de cortocircuito por MPPT')
        vmax = inverter.vmax

        assumptions = []

        voc_cold = None
        n_max = None
        if tcv is not None and voc:
            voc_cold = voc * (1 + tcv / 100 * (t_min - 25))
            n_max = math.floor(vmax / (voc_cold * VOC_COLD_MARGIN))

        t_cell_hot = None
        vmpp_hot = None
        n_min = None
        if t_amb_max is not None:
            t_cell_hot = t_amb_max + (noct - 20) / 800 * 1000
        if tcv is not None and vmp and t_cell_hot is not None:
            vmpp_hot = vmp * (1 + tcv / 100 * (t_cell_hot - 25)) * VMPP_PROXY_MARGIN
            target = ctx.assumptions if ctx is not None else assumptions
            target.append({
                'entity': 'panel', 'field': 'tcv',
                'label': 'Coeficiente β de Vmp',
                'used': tcv,
                'reason': 'Se usa el coeficiente de Voc como aproximación del de Vmp '
                          f'con un margen del {round((1 - VMPP_PROXY_MARGIN) * 100)} %: '
                          'el coeficiente real de Vmp es más negativo y la ficha no lo publica.',
            })
            if mppt_v_min:
                n_min = max(1, math.ceil(mppt_v_min / vmpp_hot))

        isc_design = isc * ISC_DESIGN_FACTOR if isc is not None else None

        configurations = []
        recommended = None
        if n_max and required:
            floor_series = n_min or 1
            for n_series in range(min(n_max, required), floor_series - 1, -1):
                n_parallel = math.ceil(required / n_series)
                per_mppt = math.ceil(n_parallel / mppt_count) if mppt_count else None
                total = n_series * n_parallel
                cfg_checks = StringSizingService._config_checks(
                    n_series, n_parallel, per_mppt,
                    voc_cold, vmpp_hot, isc_design, imp,
                    vmax, mppt_v_min, isc_max_mppt, inverter.I_max_input,
                )
                verdict = ('fallo' if any(c['verdict'] == 'fallo' for c in cfg_checks)
                           else 'aviso' if any(c['verdict'] == 'aviso' for c in cfg_checks)
                           else 'ok')
                configurations.append({
                    'n_series': n_series,
                    'n_parallel': n_parallel,
                    'strings_per_mppt': per_mppt,
                    'total_panels': total,
                    'excess_panels': total - required,
                    'voc_cold_string': round(voc_cold * n_series, 1) if voc_cold else None,
                    'vmpp_hot_string': round(vmpp_hot * n_series, 1) if vmpp_hot else None,
                    'verdict': verdict,
                })
            configurations.sort(key=lambda c: (
                {'ok': 0, 'aviso': 1, 'fallo': 2}[c['verdict']],
                c['excess_panels'],
                -c['n_series'],
            ))
            configurations = configurations[:6]
            if configurations and configurations[0]['verdict'] != 'fallo':
                recommended = configurations[0]

        checks = StringSizingService._global_checks(
            panel, inverter, recommended, required,
            voc_cold, vmpp_hot, t_cell_hot, isc_design,
            mppt_v_min, isc_max_mppt,
        )

        core_fields = [tcv, mppt_v_min]
        if all(v is not None for v in core_fields) and isc is not None and mppt_count:
            detail_level = 'completo'
        elif tcv is not None:
            detail_level = 'parcial'
        else:
            detail_level = 'no_disponible'

        return {
            'series_range': {
                'min': n_min,
                'max': n_max,
                'computed_with': {
                    't_min': round(t_min, 1) if t_min is not None else None,
                    't_cell_hot': round(t_cell_hot, 1) if t_cell_hot is not None else None,
                    'voc_cold_module': round(voc_cold, 2) if voc_cold else None,
                    'vmpp_hot_module': round(vmpp_hot, 2) if vmpp_hot else None,
                },
            },
            'recommended': recommended,
            'configurations': configurations,
            'checks': checks,
            'assumptions': assumptions,
            'detail_level': detail_level,
        }

    @staticmethod
    def _config_checks(n_series, n_parallel, per_mppt, voc_cold, vmpp_hot,
                       isc_design, imp, vmax, mppt_v_min, isc_max_mppt, i_max_input):
        checks = []
        if voc_cold:
            v = voc_cold * n_series * VOC_COLD_MARGIN
            checks.append({'id': 'voc_cold', 'value': v, 'limit': vmax,
                           'verdict': 'ok' if v < vmax else 'fallo'})
        if vmpp_hot and mppt_v_min:
            v = vmpp_hot * n_series
            checks.append({'id': 'vmpp_hot', 'value': v, 'limit': mppt_v_min,
                           'verdict': 'ok' if v > mppt_v_min else 'fallo'})
        if isc_design and isc_max_mppt and per_mppt:
            i = isc_design * per_mppt
            checks.append({'id': 'isc_mppt', 'value': i, 'limit': isc_max_mppt,
                           'verdict': 'ok' if i <= isc_max_mppt else 'fallo'})
        if imp and i_max_input and per_mppt:
            i = imp * per_mppt
            checks.append({'id': 'impp_input', 'value': i, 'limit': i_max_input,
                           'verdict': 'ok' if i <= i_max_input else 'aviso'})
        if per_mppt and per_mppt > MAX_STRINGS_PER_MPPT:
            checks.append({'id': 'strings_mppt', 'value': per_mppt,
                           'limit': MAX_STRINGS_PER_MPPT, 'verdict': 'aviso'})
        return checks

    @staticmethod
    def _global_checks(panel, inverter, recommended, required,
                       voc_cold, vmpp_hot, t_cell_hot, isc_design,
                       mppt_v_min, isc_max_mppt):
        checks = []

        if voc_cold and recommended:
            v = round(voc_cold * recommended['n_series'] * VOC_COLD_MARGIN, 1)
            checks.append({
                'id': 'voc_cold',
                'label': 'Tensión de circuito abierto en el día más frío',
                'value': v, 'limit': inverter.vmax, 'unit': 'V',
                'verdict': 'ok' if v < inverter.vmax else 'fallo',
                'source': REF_IEC_62548,
                'note': f'{recommended["n_series"]} módulos en serie con margen del 5 %.',
            })

        if vmpp_hot and mppt_v_min and recommended:
            v = round(vmpp_hot * recommended['n_series'], 1)
            checks.append({
                'id': 'vmpp_hot',
                'label': 'Tensión MPP con célula caliente',
                'value': v, 'limit': mppt_v_min, 'unit': 'V',
                'verdict': 'ok' if v > mppt_v_min else 'fallo',
                'source': REF_IEC_61215,
                'note': f'Célula a {round(t_cell_hot)} °C por NOCT; β de Vmp estimado '
                        'desde el de Voc con margen del 3 %.',
            })

        if isc_design is not None and isc_max_mppt and recommended and recommended.get('strings_per_mppt'):
            i = round(isc_design * recommended['strings_per_mppt'], 1)
            checks.append({
                'id': 'isc_mppt',
                'label': 'Corriente de cortocircuito de diseño por MPPT',
                'value': i, 'limit': isc_max_mppt, 'unit': 'A',
                'verdict': 'ok' if i <= isc_max_mppt else 'fallo',
                'source': REF_IEC_62548,
                'note': 'Isc × 1,25 por el refuerzo de irradiancia.',
            })

        if recommended and inverter.I_max_input and panel.imp and recommended.get('strings_per_mppt'):
            i = round(panel.imp * recommended['strings_per_mppt'], 1)
            checks.append({
                'id': 'impp_input',
                'label': 'Corriente de operación por entrada',
                'value': i, 'limit': inverter.I_max_input, 'unit': 'A',
                'verdict': 'ok' if i <= inverter.I_max_input else 'aviso',
                'source': REF_IEC_62548,
                'note': 'Límite de operación del seguidor, no de soportabilidad.',
            })

        if required and panel.power and inverter.power:
            ratio = round(required * panel.power / 1000 / inverter.power, 2)
            verdict = 'ok' if DC_AC_RATIO_MIN <= ratio <= DC_AC_RATIO_MAX else 'aviso'
            checks.append({
                'id': 'dc_ac_ratio',
                'label': 'Ratio de potencia DC/AC',
                'value': ratio, 'limit': DC_AC_RATIO_MAX, 'unit': '',
                'verdict': verdict,
                'source': REF_ITC_BT_40,
                'note': 'La práctica moderna sobredimensiona entre 1,1 y 1,3; la potencia '
                        'del inversor fija además la categoría administrativa.',
            })

        if recommended and recommended.get('strings_per_mppt'):
            needs_fuse = recommended['strings_per_mppt'] >= FUSE_THRESHOLD_STRINGS_PER_MPPT
            fuse = panel.max_series_fuse_a
            checks.append({
                'id': 'string_fuse',
                'label': 'Fusibles de rama',
                'value': recommended['strings_per_mppt'],
                'limit': FUSE_THRESHOLD_STRINGS_PER_MPPT, 'unit': 'ramas/MPPT',
                'verdict': ('aviso' if needs_fuse and not fuse else 'ok'),
                'source': REF_IEC_62548,
                'note': ('Con 3 o más ramas por MPPT la corriente inversa puede superar lo '
                         'admisible del módulo; '
                         + (f'calibre máximo de ficha: {fuse} A.' if fuse
                            else 'falta el calibre máximo de fusible de la ficha.'))
                if needs_fuse else
                'Con 2 ramas o menos por MPPT una rama soporta la inversa de la otra.',
            })

        return checks
