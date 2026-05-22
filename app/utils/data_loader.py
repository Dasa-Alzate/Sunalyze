"""Carga de datos iniciales: catalogo oficial del marketplace por marca."""

import json
import logging
import os
from app.extensions import db
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.installation_defaults import InstallationDefaults
from app.models.catalog import Catalog, CatalogSubscription
from app.models.organization import Organization

logger = logging.getLogger(__name__)

BRAND_DISPLAY = {'JASolar': 'JA Solar'}

SEED_BATTERIES = [
    {
        'nombre': 'BYD Battery-Box Premium HVS 5.1',
        'capacity_kwh': 5.12,
        'usable_kwh': 5.12,
        'dod': 100.0,
        'power_kw': 5.1,
        'voltage': 204.0,
        'technology': 'LiFePO4',
        'round_trip_efficiency': 96.0,
        'max_cycles': 6000,
        'height': 649,
        'width': 585,
        'depth': 298,
    },
    {
        'nombre': 'Pylontech US5000',
        'capacity_kwh': 4.8,
        'usable_kwh': 4.56,
        'dod': 95.0,
        'power_kw': 3.55,
        'voltage': 48.0,
        'technology': 'LiFePO4',
        'round_trip_efficiency': 95.0,
        'max_cycles': 6000,
        'height': 132,
        'width': 442,
        'depth': 410,
    },
]


def _brand_from_name(nombre):
    token = nombre.split()[0]
    if '-' in token:
        token = token.split('-')[0]
    return BRAND_DISPLAY.get(token, token)


def _official_catalog(brand):
    catalog = Catalog.query.filter_by(nombre=brand, org_id=None).first()
    if not catalog:
        catalog = Catalog(
            nombre=brand,
            descripcion=f'Catálogo oficial de {brand}',
            org_id=None,
            is_official=True,
        )
        db.session.add(catalog)
        db.session.flush()
    return catalog


def load_initial_data():
    """Carga los datos iniciales desde el JSON a la base de datos"""

    json_path = os.path.join(os.path.dirname(__file__), '../../data/database.json')

    try:
        if Panel.query.first() or Inverter.query.first():
            logger.info("Datos iniciales ya presentes, se omite la carga.")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for panel_data in data.get('placas', []):
            catalog = _official_catalog(_brand_from_name(panel_data['nombre']))
            panel = Panel(
                catalog_id=catalog.id,
                nombre=panel_data['nombre'],
                y=panel_data['y'],
                tcp=panel_data['tcp'],
                tcv=panel_data['tcv'],
                voc=panel_data['voc'],
                vmp=panel_data['vmp'],
                imp=panel_data['imp'],
                isc=panel_data['isc'],
                power=panel_data['power'],
                t_noct=panel_data['t_noct'],
                height=panel_data['height'],
                width=panel_data['width'],
                datasheet=panel_data.get('datasheet')
            )
            db.session.add(panel)

        for inverter_data in data.get('inversores', []):
            catalog = _official_catalog(_brand_from_name(inverter_data['nombre']))
            inverter = Inverter(
                catalog_id=catalog.id,
                nombre=inverter_data['nombre'],
                y=inverter_data['y'],
                power_max=inverter_data.get('power_max', inverter_data.get('power', 0)),
                power=inverter_data['power'],
                vmax=inverter_data['vmax'],
                I_max_input=inverter_data['I_max_input'],
                I_max_output=inverter_data['I_max_output'],
                datasheet=inverter_data.get('datasheet')
            )
            db.session.add(inverter)

        for battery_data in SEED_BATTERIES:
            catalog = _official_catalog(_brand_from_name(battery_data['nombre']))
            battery = Battery(catalog_id=catalog.id, **battery_data)
            db.session.add(battery)

        InstallationDefaults.query.delete()
        defaults = InstallationDefaults(
            dc_material='cobre/unipolar',
            dc_modelo='H1Z2Z2-K',
            ac_material='cobre/unipolar',
            ac_modelo='H07Z1-K',
            tierra_material='cobre/unipolar',
            tierra_modelo='RZ1-K',
            dc_sobretensiones_modelo='Beny 600v BUD 40/2',
            dc_fusibles_modelo='10X38 DC 16A',
            dc_portafusibles='10X38 1000v DC',
            dc_magnetotermico_modelo='Beny DC 600v 16A',
            ac_diferencial_modelo='Schneider Tipo A 40A 30mA',
            ac_magnetotermico_modelo='Schneider 2P 40A',
            inyeccion_cero_modelo='Incorporado en inversor',
            dispositivo_medida_modelo='Incorporado en inversor',
        )
        db.session.add(defaults)

        db.session.commit()
        logger.info("Datos iniciales cargados exitosamente!")

    except Exception:
        logger.exception("Error cargando datos iniciales")
        db.session.rollback()
        raise


def ensure_marketplace():
    """Backfill idempotente del marketplace.

    Asigna catalogo oficial por marca a los equipos huerfanos (catalog_id
    NULL) y suscribe todos los workspaces existentes a los catalogos
    oficiales. Seguro de ejecutar tras cada migracion.
    """
    orphans = 0
    for model in (Panel, Inverter, Battery):
        for row in model.query.filter(model.catalog_id.is_(None)).all():
            row.catalog_id = _official_catalog(_brand_from_name(row.nombre)).id
            orphans += 1

    officials = Catalog.query.filter(Catalog.org_id.is_(None), Catalog.is_official.is_(True)).all()
    subscribed = 0
    for org in Organization.active().all():
        for catalog in officials:
            exists = CatalogSubscription.query.filter_by(org_id=org.id, catalog_id=catalog.id).first()
            if not exists:
                db.session.add(CatalogSubscription(org_id=org.id, catalog_id=catalog.id))
                subscribed += 1

    db.session.commit()
    logger.info('Marketplace asegurado: %d equipos asignados, %d suscripciones creadas, %d catalogos oficiales',
                orphans, subscribed, len(officials))
