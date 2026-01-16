from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, date, timedelta

from core.database import get_db, Empresa, BuzonRun
from api import schemas

router = APIRouter(
    prefix="/automatizacion",
    tags=["automatizacion"]
)

@router.post("/run", response_model=schemas.BuzonRunResponse)
async def run_automation(req: schemas.AutomationRunRequest, db: Session = Depends(get_db)):
    """
    Encola runs de buzón (uno por empresa) para ser procesados por el worker.
    """
    errors = []
    runs = []
    headless = not req.show_browser

    if req.date_from:
        fecha_desde = req.date_from
    else:
        days_back = req.days_back if req.days_back is not None else 7
        fecha_desde = (datetime.now() - timedelta(days=days_back)).date()

    fecha_hasta = req.date_to

    query = db.query(Empresa).filter(Empresa.activo == True)
    if req.rucs:
        query = query.filter(Empresa.ruc.in_(req.rucs))

    if req.mode == "solo_fallidos":
        query = query.filter(Empresa.last_run_status == "ERROR")
    elif req.mode == "pendientes":
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(
            or_(
                Empresa.last_run_status.notin_(['COMPLETADO', 'SIN_NOVEDADES']),
                Empresa.last_run_at == None,
                Empresa.last_run_at < today_start
            )
        )

    empresas = query.all()
    if not empresas:
        return {"ok": False, "runs": [], "errors": ["No hay empresas elegibles para encolar."]}

    for emp in empresas:
        existing = db.query(BuzonRun).filter(
            BuzonRun.ruc_empresa == emp.ruc,
            BuzonRun.fecha_desde == fecha_desde,
            BuzonRun.status.in_(["PENDING", "RUNNING"])
        ).first()
        if existing:
            errors.append(f"{emp.ruc}: ya existe un run pendiente/en ejecución para esa fecha.")
            continue
        run = BuzonRun(
            ruc_empresa=emp.ruc,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            status="PENDING",
            retry_mode=req.mode,
            headless=headless,
        )
        db.add(run)
        db.flush()
        runs.append(run)

    db.commit()
    return {"ok": len(runs) > 0, "runs": runs, "errors": errors}

@router.post("/stop")
def stop_automation(
    ruc: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Solicita detener la automatización de forma segura.
    Se detendrá después de terminar la empresa actual.
    """
    query = db.query(BuzonRun).filter(BuzonRun.status == "RUNNING")
    if ruc:
        query = query.filter(BuzonRun.ruc_empresa == ruc)
    if fecha_desde:
        query = query.filter(BuzonRun.fecha_desde == fecha_desde)
    updated = query.update({"stop_requested": True}, synchronize_session=False)
    db.commit()
    return {"message": "Se ha solicitado detener la automatización.", "updated": updated}

@router.get("/runs", response_model=schemas.BuzonRunResponse)
def list_runs(
    ruc: Optional[str] = None,
    status: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
):
    query = db.query(BuzonRun)
    if ruc:
        query = query.filter(BuzonRun.ruc_empresa == ruc)
    if status:
        query = query.filter(BuzonRun.status == status)
    if fecha_desde:
        query = query.filter(BuzonRun.fecha_desde >= fecha_desde)
    if fecha_hasta:
        query = query.filter(BuzonRun.fecha_desde <= fecha_hasta)
    runs = query.order_by(BuzonRun.id.desc()).limit(200).all()
    return {"ok": True, "runs": runs, "errors": []}

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    """
    Retorna el estado actual de las empresas (Simulando 'History' de la última corrida).
    """
    total = db.query(Empresa).filter(Empresa.activo == True).count()
    pendientes = db.query(Empresa).filter(Empresa.last_run_status == 'PENDIENTE', Empresa.activo == True).count()
    procesando = db.query(Empresa).filter(Empresa.last_run_status == 'PROCESANDO', Empresa.activo == True).count()
    completados = db.query(Empresa).filter(Empresa.last_run_status == 'COMPLETADO', Empresa.activo == True).count()
    sin_novedades = db.query(Empresa).filter(Empresa.last_run_status == 'SIN_NOVEDADES', Empresa.activo == True).count()
    errores = db.query(Empresa).filter(Empresa.last_run_status == 'ERROR', Empresa.activo == True).count()
    
    return {
        "resumen": {
            "total_empresas": total,
            "pendientes": pendientes,
            "procesando": procesando,
            "completados": completados,
            "sin_novedades": sin_novedades,
            "errores": errores
        }
    }

@router.get("/errors")
def get_errors(db: Session = Depends(get_db)):
    """
    Detalle de empresas con error.
    """
    errores = db.query(Empresa).filter(Empresa.last_run_status == 'ERROR', Empresa.activo == True).all()
    return [
        {
            "ruc": e.ruc,
            "razon_social": e.razon_social,
            "error": e.last_run_error,
            "fecha": e.last_run_at
        }
        for e in errores
    ]
