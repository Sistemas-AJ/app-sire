from typing import List, Optional
from sqlalchemy.orm import Session

# Importa tu SessionLocal / get_db / Base desde donde lo tienes hoy:
from core.database import db_session

# Importa el modelo Empresa desde donde esté definido.
# Si lo tienes en core/database.py, esto funciona:
from core.database import Empresa


def get_empresas_activas(db: Session) -> List[Empresa]:
    """
    Devuelve empresas activas con credenciales SOL (usuario_sol/clave_sol no nulos).
    """
    return (
        db.query(Empresa)
        .filter(Empresa.activo == True)
        .filter(Empresa.usuario_sol.isnot(None))
        .filter(Empresa.clave_sol.isnot(None))
        .order_by(Empresa.ruc.asc())
        .all()
    )


def get_empresa(db: Session, ruc: str) -> Optional[Empresa]:
    return db.query(Empresa).filter(Empresa.ruc == ruc).first()
