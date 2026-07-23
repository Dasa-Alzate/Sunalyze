from app.models.database import BaseModel
from app import db


class InstallationDefaults(BaseModel):
    __tablename__ = 'installation_defaults'

    dc_material = db.Column(db.String(100), nullable=False)
    dc_modelo = db.Column(db.String(100), nullable=False)

    ac_material = db.Column(db.String(100), nullable=False)
    ac_modelo = db.Column(db.String(100), nullable=False)

    tierra_material = db.Column(db.String(100), nullable=False)
    tierra_modelo = db.Column(db.String(100), nullable=False)

    dc_sobretensiones_modelo = db.Column(db.String(100), nullable=False)
    dc_fusibles_modelo = db.Column(db.String(100), nullable=False)
    dc_portafusibles = db.Column(db.String(100), nullable=False)
    dc_magnetotermico_modelo = db.Column(db.String(100), nullable=False)

    ac_diferencial_modelo = db.Column(db.String(100), nullable=False)
    ac_magnetotermico_modelo = db.Column(db.String(100), nullable=False)

    inyeccion_cero_modelo = db.Column(db.String(100), nullable=False)
    dispositivo_medida_modelo = db.Column(db.String(100), nullable=False)

    @classmethod
    def get(cls):
        return cls.query.first()
