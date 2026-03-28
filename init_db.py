from app import create_app, db
from app.utils.data_loader import load_initial_data

app = create_app()

with app.app_context():
    # Crear todas las tablas
    db.create_all()
    print("Tablas creadas exitosamente!")
    
    # Cargar datos iniciales
    load_initial_data()