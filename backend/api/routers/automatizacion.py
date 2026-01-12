from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from core.database import get_db, Empresa
from api import schemas
import main_auto 

router = APIRouter(
    prefix="/automatizacion",
    tags=["automatizacion"]
)

@router.post("/run")
async def run_automation(
    req: schemas.AutomationRunRequest, 
    background_tasks: BackgroundTasks
):
    """
    Inicia el proceso de descarga masiva en segundo plano.
    """
    retry_mode = (req.mode == "solo_fallidos")
    headless = not req.show_browser # Si show_browser=True, entonces headless=False
    
    # Lanzar tarea en background (FastAPI, al ser función síncrona la lanzara en threadpool)
    background_tasks.add_task(main_auto.run_automation_process, retry_mode=retry_mode, days_back=req.days_back, headless=headless)
    
    return {"message": "Proceso de automatización iniciado", "params": req}

@router.post("/stop")
def stop_automation():
    """
    Solicita detener la automatización de forma segura.
    Se detendrá después de terminar la empresa actual.
    """
    main_auto.request_stop()
    return {"message": "Se ha solicitado detener la automatización. El robot se detendrá al finalizar la empresa actual."}

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
