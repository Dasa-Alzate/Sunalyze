from app.models.database import BaseModel
from app import db


class InstallationDefaults(BaseModel):
    __tablename__ = 'installation_defaults'

    # Cableado DC
    dc_material = db.Column(db.String(100), nullable=False)
    dc_modelo = db.Column(db.String(100), nullable=False)

    # Cableado AC
    ac_material = db.Column(db.String(100), nullable=False)
    ac_modelo = db.Column(db.String(100), nullable=False)

    # Cableado de tierra
    tierra_material = db.Column(db.String(100), nullable=False)
    tierra_modelo = db.Column(db.String(100), nullable=False)

    # Protecciones DC
    dc_sobretensiones_modelo = db.Column(db.String(100), nullable=False)
    dc_fusibles_modelo = db.Column(db.String(100), nullable=False)
    dc_portafusibles = db.Column(db.String(100), nullable=False)
    dc_magnetotermico_modelo = db.Column(db.String(100), nullable=False)

    # Protecciones AC
    ac_diferencial_modelo = db.Column(db.String(100), nullable=False)
    ac_magnetotermico_modelo = db.Column(db.String(100), nullable=False)

    # Equipos adicionales
    inyeccion_cero_modelo = db.Column(db.String(100), nullable=False)
    dispositivo_medida_modelo = db.Column(db.String(100), nullable=False)

    @classmethod
    def get(cls):
        return cls.query.first()
