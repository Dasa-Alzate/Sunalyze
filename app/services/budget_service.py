from app.extensions import db
from app.models.budget_item import BudgetItem, CAPITULOS
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery


class BudgetService:

    @staticmethod
    def totals(items, iva_pct):
        base = round(sum(i.importe for i in items), 2)
        iva = round(base * (iva_pct or 0) / 100, 2)
        return {'base': base, 'iva_pct': iva_pct, 'iva': iva, 'total': round(base + iva, 2)}

    @classmethod
    def get_budget(cls, project):
        items = BudgetItem.query.filter_by(project_id=project.id).order_by(
            BudgetItem.capitulo, BudgetItem.orden, BudgetItem.id
        ).all()
        return {
            'iva_pct': project.budget_iva_pct,
            'capitulos': CAPITULOS,
            'items': [i.to_dict() for i in items],
            'totales': cls.totals(items, project.budget_iva_pct),
        }

    @classmethod
    def replace(cls, project, iva_pct, items_data):
        BudgetItem.query.filter_by(project_id=project.id).delete()
        for idx, data in enumerate(items_data):
            db.session.add(BudgetItem(
                project_id=project.id,
                capitulo=data['capitulo'],
                descripcion=data['descripcion'].strip(),
                unidad=(data.get('unidad') or 'ud').strip(),
                cantidad=data.get('cantidad', 1),
                precio_unitario=data.get('precio_unitario', 0),
                orden=data.get('orden', idx),
            ))
        project.budget_iva_pct = iva_pct
        db.session.flush()
        return cls.get_budget(project)

    @staticmethod
    def _final_price(base, org_pct, equip_pct):
        price = (base or 0) * (1 + (org_pct or 0) / 100) * (1 + (equip_pct or 0) / 100)
        return round(price, 2)

    @classmethod
    def seed_from_design(cls, project):
        from app.services.org_service import OrgService

        profile = OrgService.get_budget_profile(project.org_id)
        org_pct = profile.get('equipment_inflation_pct') or 0

        items = []
        resultados = project.resultados or {}
        n_paneles = 0
        try:
            n_paneles = int(resultados.get('cell_amount') or 0)
        except (TypeError, ValueError):
            pass
        n_modulos = max(1, n_paneles)

        panel = Panel.query.get(project.panel_id) if project.panel_id else None
        if panel:
            items.append({'capitulo': 1, 'descripcion': f'Módulo fotovoltaico {panel.nombre} ({panel.power:.0f} Wp)',
                          'unidad': 'ud', 'cantidad': n_modulos,
                          'precio_unitario': cls._final_price(panel.precio_unitario, org_pct, panel.inflacion_pct)})

        inverter = Inverter.query.get(project.inverter_id) if project.inverter_id else None
        if inverter:
            items.append({'capitulo': 1, 'descripcion': f'Inversor {inverter.nombre} ({inverter.power:.1f} kW)',
                          'unidad': 'ud', 'cantidad': 1,
                          'precio_unitario': cls._final_price(inverter.precio_unitario, org_pct, inverter.inflacion_pct)})

        battery = Battery.query.get(project.battery_id) if project.battery_id else None
        if battery:
            items.append({'capitulo': 1, 'descripcion': f'Batería {battery.nombre} ({battery.capacity_kwh:.1f} kWh)',
                          'unidad': 'ud', 'cantidad': max(1, project.battery_quantity or 1),
                          'precio_unitario': cls._final_price(battery.precio_unitario, org_pct, battery.inflacion_pct)})

        items.append({'capitulo': 2, 'descripcion': 'Cableado CC/CA, protecciones eléctricas y pequeño material',
                      'unidad': 'PA', 'cantidad': 1, 'precio_unitario': 0})
        items.append({'capitulo': 2, 'descripcion': 'Canalizaciones y puesta a tierra',
                      'unidad': 'PA', 'cantidad': 1, 'precio_unitario': 0})

        estructura = 'coplanar' if project.coplanar else 'con inclinación'
        items.append({'capitulo': 3, 'descripcion': f'Estructura {estructura} para {n_modulos} módulos',
                      'unidad': 'PA', 'cantidad': 1, 'precio_unitario': 0})

        mano_obra = round((profile.get('labor_fixed') or 0) + (profile.get('labor_per_panel') or 0) * n_modulos, 2)
        items.append({'capitulo': 3, 'descripcion': f'Mano de obra: montaje y puesta en marcha ({n_modulos} módulos)',
                      'unidad': 'PA', 'cantidad': 1, 'precio_unitario': mano_obra})

        items.append({'capitulo': 4, 'descripcion': 'Legalización, boletín eléctrico y tramitación de autoconsumo',
                      'unidad': 'PA', 'cantidad': 1, 'precio_unitario': 0})

        for line in profile.get('custom_lines') or []:
            try:
                capitulo = int(line.get('capitulo') or 4)
            except (TypeError, ValueError):
                capitulo = 4
            descripcion = str(line.get('descripcion') or '').strip()
            if not descripcion or capitulo not in CAPITULOS:
                continue
            try:
                cantidad = float(line.get('cantidad') or 1)
                precio = float(line.get('precio_unitario') or 0)
            except (TypeError, ValueError):
                cantidad, precio = 1, 0
            items.append({'capitulo': capitulo, 'descripcion': descripcion,
                          'unidad': str(line.get('unidad') or 'ud'),
                          'cantidad': cantidad, 'precio_unitario': precio})

        return cls.replace(project, project.budget_iva_pct, items)

    @classmethod
    def memoria_vars(cls, project):
        data = cls.get_budget(project)
        if not data['items']:
            return {}

        def money(v):
            return f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

        chapters = []
        for num, titulo in CAPITULOS.items():
            rows = [i for i in data['items'] if i['capitulo'] == num]
            if not rows:
                continue
            chapters.append({
                'num': num,
                'titulo': titulo,
                'partidas': [{**r, 'cantidad_fmt': f"{r['cantidad']:g}",
                           'precio_fmt': money(r['precio_unitario']),
                           'importe_fmt': money(r['importe'])} for r in rows],
                'subtotal_fmt': money(round(sum(r['importe'] for r in rows), 2)),
            })
        t = data['totales']
        return {
            'budget_chapters': chapters,
            'budget_base': money(t['base']),
            'budget_iva_pct': f"{t['iva_pct']:g}",
            'budget_iva': money(t['iva']),
            'budget_total': money(t['total']),
        }
