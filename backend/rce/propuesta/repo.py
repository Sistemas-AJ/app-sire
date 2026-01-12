from sqlalchemy.orm import Session
from core.database import Empresa, EmpresaSire

def get_empresas_sire_activas(db: Session):
    # join Empresa + EmpresaSire
    return (
        db.query(Empresa, EmpresaSire)
        .join(EmpresaSire, EmpresaSire.ruc_empresa == Empresa.ruc)
        .filter(Empresa.activo == True)
        .filter(EmpresaSire.activo == True)
        .all()
    )
