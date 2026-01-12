from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from core.database import get_db, Empresa, Notificacion
from api import schemas

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

@router.get("/stats")
def get_global_stats(db: Session = Depends(get_db)):
    """
    Métricas generales para los widgets del Dashboard.
    """
    total_empresas = db.query(Empresa).filter(Empresa.activo == True).count()
    
    # Éxito Global (Empresas en COMPLETADO vs Total Procesadas hoy)
    # Consideramos 'Procesadas' a las que tienen last_run_at hoy
    hoy = datetime.now().date()
    # Filtro aproximado de fecha
    run_today = db.query(Empresa).filter(
        Empresa.activo == True,
        Empresa.last_run_at >= hoy
    )
    total_runs_today = run_today.count()
    completados_today = run_today.filter(Empresa.last_run_status == 'COMPLETADO').count()
    sin_novedades_today = run_today.filter(Empresa.last_run_status == 'SIN_NOVEDADES').count()
    fail_today = run_today.filter(Empresa.last_run_status == 'ERROR').count()
    
    success_rate = 0
    if total_runs_today > 0:
        # Consideramos éxito (COMPLETADO + SIN_NOVEDADES) / Total
        success_rate = ((completados_today + sin_novedades_today) / total_runs_today) * 100

    # Total Notificaciones descargadas
    total_pdfs = db.query(Notificacion).count()
    
    # Notificaciones pendientes de procesar (si tuvieramos un flag 'procesado' real en backend de negocio)
    # Aqui usamos el campo 'procesado' de la tabla, que por defecto es False.
    pending_process = db.query(Notificacion).filter(Notificacion.procesado == False).count()

    return {
        "total_empresas": total_empresas,
        "runs_today": {
            "total": total_runs_today,
            "success": completados_today + sin_novedades_today,
            "error": fail_today,
            "success_rate_percent": round(success_rate, 2)
        },
        "notifications": {
            "total_downloaded": total_pdfs,
            "pending_action": pending_process
        }
    }

from sqlalchemy import or_

@router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    search: Optional[str] = None, # Antes 'ruc'
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,   
    limit: int = 100
):
    """
    Lista de notificaciones descargadas con filtros para tabla del frontend.
    """
    query = db.query(Notificacion, Empresa.razon_social).join(Empresa, Notificacion.ruc_empresa == Empresa.ruc)
    
    if search:
        # Búsqueda parcial por RUC o Razón Social (Case Insensitive)
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Notificacion.ruc_empresa.ilike(search_term),
                Empresa.razon_social.ilike(search_term)
            )
        )
        
    if start_date:
        try:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Notificacion.fecha_emision >= dt_start)
        except:
            pass
            
    if end_date:
        try:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            # Ajustar al final del dia
            dt_end = dt_end.replace(hour=23, minute=59, second=59)
            query = query.filter(Notificacion.fecha_emision <= dt_end)
        except:
            pass
            
    # Ordenar por más reciente
    results = query.order_by(Notificacion.fecha_emision.desc()).limit(limit).all()
    
    # Formatear
    data = []
    for notif, razon_social in results:
        data.append({
            "id": notif.id,
            "ruc": notif.ruc_empresa,
            "razon_social": razon_social,
            "codigo": notif.codigo_notificacion,
            "asunto": notif.asunto,
            "fecha_emision": notif.fecha_emision,
            "fecha_recibido": notif.fecha_recibido_sunat, # Campo nuevo
            "fecha_descarga": notif.fecha_leido,
            "ruta_pdf": notif.ruta_pdf_local,
            "estado": notif.estado_sunat
        })
        
    return data
