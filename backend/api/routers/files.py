from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import zipfile
import io
from datetime import datetime

from core.database import get_db, Notificacion, Empresa
from rce.propuesta.config import REGISTROS_DIR

router = APIRouter(
    prefix="/files",
    tags=["files"]
)

@router.get("/download/{id}")
def download_single_pdf(id: int, db: Session = Depends(get_db)):
    """
    Descarga un PDF individual por su ID de notificación.
    """
    notif = db.query(Notificacion).filter(Notificacion.id == id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    
    file_path = notif.ruta_pdf_local
    if not file_path or not os.path.exists(file_path):
         raise HTTPException(status_code=404, detail="Archivo físico no encontrado en el servidor")
         
    # Nombre amigable para el usuario
    filename = os.path.basename(file_path)
    return FileResponse(file_path, filename=filename, media_type='application/pdf')

@router.get("/batch-zip")
def download_zip(
    db: Session = Depends(get_db),
    ruc: Optional[str] = None,
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
):
    """
    Genera y descarga un ZIP con los PDFs que coincidan con los filtros.
    """
    query = db.query(Notificacion)
    
    if ruc:
        query = query.filter(Notificacion.ruc_empresa == ruc)
    if start_date:
        try:
            dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Notificacion.fecha_emision >= dt)
        except: pass
    if end_date:
        try:
            dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59)
            query = query.filter(Notificacion.fecha_emision <= dt)
        except: pass
        
    # Limitar para evitar explosión de memoria? 
    # Por ahora hardlimit de seguridad, o confiamos en el user.
    # Pongamos un limite razonable de 500 para este demo.
    results = query.order_by(Notificacion.fecha_emision.desc()).limit(200).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No se encontraron archivos con esos filtros")
        
    # Generar ZIP en memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for notif in results:
            if notif.ruta_pdf_local and os.path.exists(notif.ruta_pdf_local):
                # Estructura dentro del ZIP: RUC/Fecha_Asunto.pdf
                date_str = notif.fecha_emision.strftime("%Y%m%d")
                clean_asunto = "".join([c if c.isalnum() else "_" for c in notif.asunto[:30]])
                arcname = f"{notif.ruc_empresa}/{date_str}_{clean_asunto}_{notif.id}.pdf"
                zip_file.write(notif.ruta_pdf_local, arcname=arcname)
    
    zip_buffer.seek(0)
    
    filename = f"reportes_sunat_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
    
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/download")
def download_file(path: str = Query(..., description="Ruta absoluta dentro de REGISTROS_DIR")):
    """
    Descarga un archivo arbitrario siempre que esté dentro de REGISTROS_DIR.
    """
    if not path:
        raise HTTPException(status_code=400, detail="path es requerido")

    base = os.path.abspath(REGISTROS_DIR)
    target = os.path.abspath(path)

    if not target.startswith(base + os.sep) and target != base:
        raise HTTPException(status_code=403, detail="Ruta no permitida")
    if not os.path.exists(target):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    if os.path.isdir(target):
        raise HTTPException(status_code=400, detail="La ruta no es un archivo")

    filename = os.path.basename(target)
    return FileResponse(target, filename=filename)
