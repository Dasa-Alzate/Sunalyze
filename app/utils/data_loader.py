"""Utilidad para cargar datos iniciales desde JSON a la base de datos."""

import json
import os
from app import db
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.installation_defaults import InstallationDefaults

def load_initial_data():
    """Carga los datos iniciales desde el JSON a la base de datos"""
    
    json_path = os.path.join(os.path.dirname(__file__), '../../data/database.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Limpiar tablas existentes
        Panel.query.delete()
        Inverter.query.delete()
        
        # Cargar paneles
        for panel_data in data.get('placas', []):
            panel = Panel(
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
                width=panel_data['width']
            )
            db.session.add(panel)
        
        # Cargar inversores
        for inverter_data in data.get('inversores', []):
            inverter = Inverter(
                nombre=inverter_data['nombre'],
                y=inverter_data['y'],
                power_max=inverter_data.get('power_max', inverter_data.get('power', 0)),
                power=inverter_data['power'],
                vmax=inverter_data['vmax'],
                I_max_input=inverter_data['I_max_input'],
                I_max_output=inverter_data['I_max_output']
            )
            db.session.add(inverter)
        
        # Cargar configuración por defecto de instalación
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
        print("Datos iniciales cargados exitosamente!")
        
    except Exception as e:
        print(f"Error cargando datos iniciales: {e}")
        db.session.rollback()