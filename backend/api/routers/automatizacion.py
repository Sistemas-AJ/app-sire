from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
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

    fecha_hasta = req.date_to or datetime.now().date()

    query = db.query(Empresa).filter(Empresa.activo == True)
    if req.rucs:
        query = query.filter(Empresa.ruc.in_(req.rucs))

    if req.mode == "solo_fallidos":
        runs_query = db.query(BuzonRun.ruc_empresa).filter(
            BuzonRun.fecha_desde == fecha_desde,
            BuzonRun.fecha_hasta == fecha_hasta,
            BuzonRun.status.in_(["PENDING", "ERROR", "PARTIAL", "STOPPED"]),
        )
        eligible_rucs = {row[0] for row in runs_query.distinct().all()}
        if req.rucs:
            eligible_rucs = eligible_rucs.intersection(set(req.rucs))
        if not eligible_rucs:
            return {"ok": False, "runs": [], "errors": ["No hay empresas elegibles para encolar."]}
        query = query.filter(Empresa.ruc.in_(sorted(eligible_rucs)))
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
        ).first()
        if existing:
            if existing.status == "RUNNING":
                errors.append(f"{emp.ruc}: ya existe un run en ejecución para esa fecha.")
                continue
            existing.status = "PENDING"
            existing.retry_mode = req.mode
            existing.headless = headless
            existing.queued = True
            existing.stop_requested = False
            db.add(existing)
            runs.append(existing)
            continue

        run = BuzonRun(
            ruc_empresa=emp.ruc,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            status="PENDING",
            retry_mode=req.mode,
            headless=headless,
            queued=True,
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
    running = db.query(BuzonRun).filter(BuzonRun.status == "RUNNING")
    if ruc:
        running = running.filter(BuzonRun.ruc_empresa == ruc)
    if fecha_desde:
        running = running.filter(BuzonRun.fecha_desde == fecha_desde)
    updated = running.update({"stop_requested": True}, synchronize_session=False)

    pending = db.query(BuzonRun).filter(BuzonRun.status == "PENDING")
    if ruc:
        pending = pending.filter(BuzonRun.ruc_empresa == ruc)
    if fecha_desde:
        pending = pending.filter(BuzonRun.fecha_desde == fecha_desde)
    stopped = pending.update({"status": "STOPPED"}, synchronize_session=False)
    db.commit()
    return {
        "message": "Se ha solicitado detener la automatización.",
        "running_marked": updated,
        "pending_stopped": stopped,
    }

@router.get("/runs", response_model=schemas.BuzonRunResponse)
def list_runs(
    ruc: Optional[str] = None,
    status: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if fecha_desde and not fecha_hasta:
        fecha_hasta = datetime.now().date()

    if fecha_desde and fecha_hasta:
        rucs_con_periodo = [
            row[0]
            for row in db.query(BuzonRun.ruc_empresa)
            .filter(BuzonRun.fecha_desde == fecha_desde, BuzonRun.fecha_hasta == fecha_hasta)
            .distinct()
            .all()
        ]
        if rucs_con_periodo:
            db.query(BuzonRun).filter(
                BuzonRun.ruc_empresa.in_(rucs_con_periodo),
                BuzonRun.fecha_desde >= fecha_desde,
                BuzonRun.fecha_hasta <= fecha_hasta,
                ~(
                    (BuzonRun.fecha_desde == fecha_desde)
                    & (BuzonRun.fecha_hasta == fecha_hasta)
                ),
            ).delete(synchronize_session=False)
            db.commit()

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


@router.get("/periods", response_model=schemas.BuzonPeriodsResponse)
def list_periods(db: Session = Depends(get_db)):
    """
    Lista periodos disponibles con resumen de estados por rango.
    """
    rows = db.query(
        BuzonRun.fecha_desde,
        BuzonRun.fecha_hasta,
        BuzonRun.status,
        func.count(BuzonRun.id),
    ).group_by(
        BuzonRun.fecha_desde,
        BuzonRun.fecha_hasta,
        BuzonRun.status,
    ).all()

    summary = {}
    for fecha_desde, fecha_hasta, status, count in rows:
        key = (fecha_desde, fecha_hasta)
        if key not in summary:
            summary[key] = {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "total": 0,
                "ok": 0,
                "pending": 0,
                "running": 0,
                "stopped": 0,
                "partial": 0,
                "error": 0,
            }
        summary[key]["total"] += count
        normalized = (status or "").upper()
        if normalized == "OK":
            summary[key]["ok"] += count
        elif normalized == "PENDING":
            summary[key]["pending"] += count
        elif normalized == "RUNNING":
            summary[key]["running"] += count
        elif normalized == "STOPPED":
            summary[key]["stopped"] += count
        elif normalized == "PARTIAL":
            summary[key]["partial"] += count
        elif normalized == "ERROR":
            summary[key]["error"] += count

    periods = sorted(
        summary.values(),
        key=lambda r: (r["fecha_desde"] or date.min, r["fecha_hasta"] or date.min),
        reverse=True,
    )
    return {"ok": True, "periods": periods}

@router.get("/status")
def get_status(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Retorna el estado actual de las empresas (Simulando 'History' de la última corrida).
    """
    today = datetime.now().date()
    total = db.query(Empresa).filter(Empresa.activo == True).count()

    if fecha_desde and not fecha_hasta:
        fecha_hasta = today

    runs_query = db.query(BuzonRun)
    if fecha_desde and fecha_hasta:
        runs_query = runs_query.filter(
            BuzonRun.fecha_desde == fecha_desde,
            BuzonRun.fecha_hasta == fecha_hasta,
        )
    else:
        runs_query = runs_query.filter(BuzonRun.fecha_desde == today)

    has_runs = db.query(runs_query.exists()).scalar()
    if not has_runs:
        return {
            "resumen": {
                "total_empresas": total,
                "pendientes": total,
                "procesando": 0,
                "completados": 0,
                "sin_novedades": 0,
                "errores": 0,
            }
        }

    pendientes = runs_query.filter(BuzonRun.status.in_(["PENDING", "STOPPED"])).count()
    procesando = runs_query.filter(BuzonRun.status == "RUNNING").count()
    completados = runs_query.filter(BuzonRun.status == "OK").count()
    sin_novedades = runs_query.filter(BuzonRun.status == "OK").count()
    errores = runs_query.filter(BuzonRun.status.in_(["ERROR", "PARTIAL"])).count()
    
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
