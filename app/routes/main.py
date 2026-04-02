from flask import Blueprint, render_template, request
from app.controllers.analysis_controller import AnalysisController
from app.controllers.memoria_controller import MemoriaController
from app.models.panel import Panel
from app.models.inverter import Inverter

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    panels = Panel.query.with_entities(Panel.id, Panel.nombre).all()
    inverters = Inverter.query.with_entities(Inverter.id, Inverter.nombre).all()
    return render_template('index.html',
        panels=[{"id": p.id, "nombre": p.nombre} for p in panels],
        inverters=[{"id": i.id, "nombre": i.nombre} for i in inverters])

@bp.route('/api/panel-analysis', methods=['POST'])
def panel_analysis():
    return AnalysisController.calculate_panel_requirements(request.get_json())

@bp.route('/imprimir/memoria-pdf', methods=['GET', 'POST'])
def generar_memoria_pdf():
    return MemoriaController.generar_pdf(request.form if request.method == 'POST' else {})
