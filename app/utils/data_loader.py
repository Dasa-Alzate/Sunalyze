"""Utilidad para cargar datos iniciales desde JSON a la base de datos."""

import json
import os
from app import db
from app.models.panel import Panel
from app.models.inverter import Inverter

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
        
        db.session.commit()
        print("Datos iniciales cargados exitosamente!")
        
    except Exception as e:
        print(f"Error cargando datos iniciales: {e}")
        db.session.rollback()