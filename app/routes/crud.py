from flask import Blueprint, request, jsonify
from app import db
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.wire import Wire

crud_bp = Blueprint('crud', __name__)

# ========== PANELS CRUD ==========

@crud_bp.route('/api/panels', methods=['GET'])
def get_all_panels():
    panels = Panel.query.all()

    return jsonify([panel.to_dict() for panel in panels])

@crud_bp.route('/api/panels/<int:panel_id>', methods=['GET'])
def get_panel(panel_id):
    panel = Panel.query.get_or_404(panel_id)
    return jsonify(panel.to_dict())

@crud_bp.route('/api/panels', methods=['POST'])
def create_panel():
    data = request.get_json()
    
    # Validación básica
    required_fields = ['nombre', 'power', 'voc', 'vmp', 'imp']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400
    
    panel = Panel(
        nombre=data['nombre'],
        y=data.get('y', 0),
        tcp=data.get('tcp', 0),
        tcv=data.get('tcv', 0),
        voc=data['voc'],
        vmp=data['vmp'],
        imp=data['imp'],
        isc=data.get('isc', 0),
        power=data['power'],
        t_noct=data.get('t_noct', 45),
        height=data.get('height', 0),
        width=data.get('width', 0)
    )
    
    db.session.add(panel)
    db.session.commit()
    
    return jsonify(panel.to_dict()), 201

@crud_bp.route('/api/panels/<int:panel_id>', methods=['PUT'])
def update_panel(panel_id):
    panel = Panel.query.get_or_404(panel_id)
    data = request.get_json()
    
    # Actualizar campos
    update_fields = ['nombre', 'y', 'tcp', 'tcv', 'voc', 'vmp', 'imp',
                    'isc', 'power', 't_noct', 'height', 'width']
    
    for field in update_fields:
        if field in data:
            setattr(panel, field, data[field])
    
    db.session.commit()
    return jsonify(panel.to_dict())

@crud_bp.route('/api/panels/<int:panel_id>', methods=['DELETE'])
def delete_panel(panel_id):
    panel = Panel.query.get_or_404(panel_id)
    db.session.delete(panel)
    db.session.commit()
    return jsonify({'message': 'Panel eliminado correctamente'})

# ========== INVERTERS CRUD ==========

@crud_bp.route('/api/inverters', methods=['GET'])
def get_all_inverters():
    inverters = Inverter.query.all()
    return jsonify([inverter.to_dict() for inverter in inverters])

@crud_bp.route('/api/inverters/<int:inverter_id>', methods=['GET'])
def get_inverter(inverter_id):
    inverter = Inverter.query.get_or_404(inverter_id)
    return jsonify(inverter.to_dict())

@crud_bp.route('/api/inverters', methods=['POST'])
def create_inverter():
    data = request.get_json()
    
    required_fields = ['nombre', 'power', 'vmax', 'I_max_input', 'I_max_output']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400
    
    inverter = Inverter(
        nombre=data['nombre'],
        y=data.get('y', 0),
        power_max=data.get('power_max', data['power']),
        power=data['power'],
        vmax=data['vmax'],
        I_max_input=data['I_max_input'],
        I_max_output=data['I_max_output']
    )
    
    db.session.add(inverter)
    db.session.commit()
    
    return jsonify(inverter.to_dict()), 201

@crud_bp.route('/api/inverters/<int:inverter_id>', methods=['PUT'])
def update_inverter(inverter_id):
    inverter = Inverter.query.get_or_404(inverter_id)
    data = request.get_json()
    
    update_fields = ['nombre', 'y', 'power_max', 'power', 'vmax', 
                    'I_max_input', 'I_max_output']
    
    for field in update_fields:
        if field in data:
            setattr(inverter, field, data[field])
    
    db.session.commit()
    return jsonify(inverter.to_dict())

@crud_bp.route('/api/inverters/<int:inverter_id>', methods=['DELETE'])
def delete_inverter(inverter_id):
    inverter = Inverter.query.get_or_404(inverter_id)
    db.session.delete(inverter)
    db.session.commit()
    return jsonify({'message': 'Inversor eliminado correctamente'})

# ========== WIRES CRUD ==========

# GET - Listar todos los wires
@crud_bp.route('/api/wires', methods=['GET'])
def get_all_wires():
    try:
        wires = Wire.query.all()
        return jsonify([wire.to_dict() for wire in wires])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET - Obtener un wire por ID
@crud_bp.route('/api/wires/<int:wire_id>', methods=['GET'])
def get_wire(wire_id):
    wire = Wire.query.get_or_404(wire_id)
    return jsonify(wire.to_dict())

# POST - Crear nuevo wire
@crud_bp.route('/api/wires', methods=['POST'])
def create_wire():
    try:
        data = request.get_json()
        
        # Validaciones básicas
        required_fields = ['seccion', 'corriente', 'tipo', 'material', 'no_conductores']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Crear nuevo wire
        wire = Wire(
            seccion=float(data['seccion']),
            corriente=float(data['corriente']),
            tipo=data['tipo'],
            material=data['material'],
            no_conductores=int(data['no_conductores'])
        )
        
        db.session.add(wire)
        db.session.commit()
        
        return jsonify(wire.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# PUT - Actualizar wire existente
@crud_bp.route('/api/wires/<int:wire_id>', methods=['PUT'])
def update_wire(wire_id):
    wire = Wire.query.get_or_404(wire_id)
    data = request.get_json()

    update_fields = ['seccion', 'corriente', 'tipo', 'material', 'no_conductores']
    for field in update_fields:
        if field in data:
            setattr(wire, field, data[field])

    db.session.commit()
    return jsonify(wire.to_dict())

# DELETE - Eliminar wire
@crud_bp.route('/api/wires/<int:wire_id>', methods=['DELETE'])
def delete_wire(wire_id):
    wire = Wire.query.get_or_404(wire_id)
    db.session.delete(wire)
    db.session.commit()
    return jsonify({'message': 'Wire eliminado correctamente'})

# GET - Buscar wires por criterios
@crud_bp.route('/api/wires/search', methods=['GET'])
def search_wires():
    try:
        # Parámetros de búsqueda
        material = request.args.get('material')
        tipo = request.args.get('tipo')
        min_corriente = request.args.get('min_corriente')
        max_seccion = request.args.get('max_seccion')
        no_conductores = request.args.get('no_conductores')
        
        query = Wire.query
        
        if material:
            query = query.filter(Wire.material == material)
        if tipo:
            query = query.filter(Wire.tipo == tipo)
        if min_corriente:
            query = query.filter(Wire.corriente >= float(min_corriente))
        if max_seccion:
            query = query.filter(Wire.seccion <= float(max_seccion))
        if no_conductores:
            query = query.filter(Wire.no_conductores == int(no_conductores))
        
        wires = query.all()
        return jsonify([wire.to_dict() for wire in wires])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@crud_bp.route('/api/wires/calculate-section', methods=['POST'])
def calculate_section():
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['tipo', 'material', 'no_conductores', 'i_section']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Buscar wires que cumplan los criterios
        wires = Wire.query.filter(
            Wire.tipo == data['tipo'],
            Wire.material == data['material'],
            Wire.no_conductores == int(data['no_conductores']),
            Wire.corriente >= float(data['i_section']) * 1.25,
            Wire.seccion >= 6
        ).order_by(Wire.corriente.asc()).all()
        
        if not wires:
            return jsonify({
                'error': 'No se encontraron wires que cumplan los criterios',
                'seccion': None
            }), 404
        
        # Retornar el primer wire que cumple (menor sección que cumpla el requerimiento)
        wire = wires[0]
        return jsonify({
            'seccion': wire.seccion,
            'corriente': wire.corriente,
            'wire': wire.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# ========== PROTECTIONS CRUD ==========
