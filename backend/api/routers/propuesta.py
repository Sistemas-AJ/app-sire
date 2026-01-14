from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db, db_session, Empresa, EmpresaSire, RCEPropuestaFile, RCEPropuestaItem
from api import schemas
from rce.propuesta.run import procesar_empresa


router = APIRouter(prefix="/propuesta", tags=["propuesta"])


@router.post("/run", response_model=schemas.PropuestaRunResponse)
def run_propuesta(req: schemas.PropuestaRunRequest):
    results = []
    errors = []

    with db_session() as db:
        q = (
            db.query(Empresa, EmpresaSire)
            .join(EmpresaSire, EmpresaSire.ruc_empresa == Empresa.ruc)
            .filter(Empresa.activo == True)
            .filter(EmpresaSire.activo == True)
        )
        if req.ruc:
            q = q.filter(Empresa.ruc == req.ruc)
        if req.rucs:
            q = q.filter(Empresa.ruc.in_(req.rucs))

        pairs = q.all()
        if (req.ruc or req.rucs) and not pairs:
            raise HTTPException(status_code=404, detail="Empresa no encontrada o sin credenciales SIRE activas")

        for emp, cred in pairs:
            try:
                res = procesar_empresa(db, emp, cred, req.periodo, req.fec_ini, req.fec_fin)
                results.append(schemas.PropuestaRunItem(periodo=req.periodo, **res))
            except Exception as e:
                errors.append(f"{emp.ruc}: {e}")

    return schemas.PropuestaRunResponse(ok=len(errors) == 0, results=results, errors=errors)


@router.get("/status", response_model=schemas.PropuestaFileResponse)
def get_propuesta_status(ruc: str, periodo: str, db: Session = Depends(get_db)):
    row = (
        db.query(RCEPropuestaFile)
        .filter(RCEPropuestaFile.ruc_empresa == ruc, RCEPropuestaFile.periodo == periodo)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No se encontró propuesta para ese periodo")
    return row


@router.get("/items", response_model=List[schemas.PropuestaItemResponse])
def list_items(
    ruc: str,
    periodo: str,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = (
        db.query(RCEPropuestaItem)
        .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
        .order_by(RCEPropuestaItem.id.asc())
        .offset(offset)
        .limit(limit)
    )
    return q.all()


@router.get("/availability", response_model=schemas.PropuestaAvailabilityResponse)
def propuesta_availability(periodo: str, db: Session = Depends(get_db)):
    rucs = [
        r[0]
        for r in db.query(RCEPropuestaFile.ruc_empresa)
        .filter(RCEPropuestaFile.periodo == periodo)
        .distinct()
        .all()
    ]
    msg = f"{len(rucs)} empresas tienen propuesta válida en este periodo."
    return schemas.PropuestaAvailabilityResponse(periodo=periodo, available_rucs=rucs, message=msg)


@router.get("/periods", response_model=List[str])
def propuesta_periods(db: Session = Depends(get_db)):
    rows = (
        db.query(RCEPropuestaFile.periodo)
        .distinct()
        .order_by(RCEPropuestaFile.periodo.desc())
        .all()
    )
    return [r[0] for r in rows]
