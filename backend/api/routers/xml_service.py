from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional

from core.database import get_db, db_session, Empresa, RCEPropuestaItem, CPEEvidencia, CPEDetalle, RCERun
from api import schemas
from api.routers.auth import get_current_user
from rce.xml_service.job import run_xml_job_for_empresa_periodo, request_stop
from rce.xml_detail.report import build_reporte_detalle
from rce.xml_service.repository import fetch_items_pendientes_xml


router = APIRouter(
    prefix="/xml",
    tags=["xml"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/run", response_model=schemas.XMLRunResponse)
def run_xml(req: schemas.XMLRunRequest):
    processed = []
    errors = []

    rucs = []
    if req.ruc:
        rucs.append(req.ruc)
    if req.rucs:
        rucs.extend(req.rucs)
    if rucs:
        rucs = sorted(set(rucs))
    else:
        with db_session() as db:
            rucs = [
                r[0]
                for r in db.query(RCEPropuestaItem.ruc_empresa)
                .filter(RCEPropuestaItem.periodo == req.periodo)
                .distinct()
                .all()
            ]

    with db_session() as db:
        for ruc in rucs:
            existing = (
                db.query(RCERun)
                .filter(
                    RCERun.modulo == "XML",
                    RCERun.ruc_empresa == ruc,
                    RCERun.periodo == req.periodo,
                    RCERun.status.in_(["PENDING", "RUNNING", "ERROR", "PARTIAL", "STOPPED"]),
                )
                .first()
            )
            if existing:
                stats = existing.stats_json or {}
                if req.limit is not None:
                    stats["limit"] = req.limit
                stats["headless"] = req.headless
                existing.stats_json = stats
                if existing.status in ["ERROR", "PARTIAL", "STOPPED"]:
                    existing.status = "PENDING"
                db.add(existing)
                processed.append(ruc)
                continue

            run = RCERun(
                ruc_empresa=ruc,
                periodo=req.periodo,
                modulo="XML",
                status="PENDING",
                stats_json={"limit": req.limit, "headless": req.headless},
            )
            db.add(run)
            processed.append(ruc)
        db.commit()

    return schemas.XMLRunResponse(ok=len(errors) == 0, processed_rucs=processed, errors=errors)


@router.post("/stop", response_model=schemas.XMLStopResponse)
def stop_xml(req: schemas.XMLStopRequest):
    request_stop(req.ruc, req.periodo)
    msg = "Stop solicitado"
    if req.ruc or req.periodo:
        msg = f"Stop solicitado para ruc={req.ruc or '*'} periodo={req.periodo or '*'}"
    return schemas.XMLStopResponse(ok=True, message=msg)


@router.get("/pending", response_model=List[schemas.PropuestaItemResponse])
def pending_items(
    ruc: str,
    periodo: str,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return fetch_items_pendientes_xml(db, ruc, periodo, limit=limit)


@router.get("/evidencias", response_model=List[schemas.EvidenciaResponse])
def list_evidencias(
    ruc: str,
    periodo: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(CPEEvidencia)
        .join(RCEPropuestaItem, CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id)
        .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
        .filter(CPEEvidencia.tipo == "XML")
    )
    if status:
        q = q.filter(CPEEvidencia.status == status)
    return q.order_by(CPEEvidencia.propuesta_item_id.asc()).all()


@router.get("/detalle", response_model=schemas.DetalleResponse)
def get_detalle(
    item_id: int,
    extractor_version: str = "v1",
    db: Session = Depends(get_db),
):
    row = (
        db.query(CPEDetalle)
        .filter(CPEDetalle.propuesta_item_id == item_id, CPEDetalle.extractor_version == extractor_version)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    return row


@router.get("/progress", response_model=schemas.XMLProgressResponse)
def get_progress(ruc: str, periodo: str, db: Session = Depends(get_db)):
    total_items = (
        db.query(func.count(RCEPropuestaItem.id))
        .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
        .scalar()
    )

    rows = (
        db.query(CPEEvidencia.status, func.count(CPEEvidencia.id))
        .join(RCEPropuestaItem, CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id)
        .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
        .filter(CPEEvidencia.tipo == "XML")
        .group_by(CPEEvidencia.status)
        .all()
    )

    counts = {status: count for status, count in rows}
    ok = counts.get("OK", 0)
    error = counts.get("ERROR", 0)
    not_found = counts.get("NOT_FOUND", 0)
    auth = counts.get("AUTH", 0)
    pending = counts.get("PENDING", 0)
    total_evidencias = sum(counts.values())

    remaining = max(total_items - ok - not_found, 0)

    return schemas.XMLProgressResponse(
        ruc=ruc,
        periodo=periodo,
        total_items=total_items or 0,
        total_evidencias=total_evidencias,
        ok=ok,
        error=error,
        not_found=not_found,
        auth=auth,
        pending=pending,
        remaining=remaining,
    )


@router.get("/progress/global", response_model=schemas.XMLProgressGlobalResponse)
def get_progress_global(periodo: str, db: Session = Depends(get_db)):
    total_items = (
        db.query(func.count(RCEPropuestaItem.id))
        .filter(RCEPropuestaItem.periodo == periodo)
        .scalar()
    )
    total_empresas = (
        db.query(func.count(func.distinct(RCEPropuestaItem.ruc_empresa)))
        .filter(RCEPropuestaItem.periodo == periodo)
        .scalar()
    )

    rows = (
        db.query(CPEEvidencia.status, func.count(CPEEvidencia.id))
        .join(RCEPropuestaItem, CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id)
        .filter(RCEPropuestaItem.periodo == periodo)
        .filter(CPEEvidencia.tipo == "XML")
        .group_by(CPEEvidencia.status)
        .all()
    )

    counts = {status: count for status, count in rows}
    ok = counts.get("OK", 0)
    error = counts.get("ERROR", 0)
    not_found = counts.get("NOT_FOUND", 0)
    auth = counts.get("AUTH", 0)
    pending = counts.get("PENDING", 0)
    total_evidencias = sum(counts.values())
    remaining = max((total_items or 0) - ok - not_found, 0)

    return schemas.XMLProgressGlobalResponse(
        periodo=periodo,
        total_empresas=total_empresas or 0,
        total_items=total_items or 0,
        total_evidencias=total_evidencias,
        ok=ok,
        error=error,
        not_found=not_found,
        auth=auth,
        pending=pending,
        remaining=remaining,
    )


@router.get("/report", response_model=schemas.XMLReportResponse)
def get_report(ruc: str, periodo: str, db: Session = Depends(get_db)):
    q = (
        db.query(RCEPropuestaItem, CPEEvidencia, CPEDetalle)
        .outerjoin(
            CPEEvidencia,
            and_(
                CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id,
                CPEEvidencia.tipo == "XML",
            ),
        )
        .outerjoin(
            CPEDetalle,
            and_(
                CPEDetalle.propuesta_item_id == RCEPropuestaItem.id,
                CPEDetalle.extractor_version == "v1",
            ),
        )
        .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
        .order_by(RCEPropuestaItem.id.asc())
    )

    total_items = 0
    ok = error = not_found = auth = pending = 0
    items = []

    for item, ev, det in q.all():
        total_items += 1
        status = ev.status if ev else "PENDING"
        if status == "OK":
            ok += 1
        elif status == "ERROR":
            error += 1
        elif status == "NOT_FOUND":
            not_found += 1
        elif status == "AUTH":
            auth += 1
        else:
            pending += 1

        items.append(
            schemas.XMLReportItemResponse(
                item_id=item.id,
                ruc_empresa=item.ruc_empresa,
                periodo=item.periodo,
                tipo_cp=item.tipo_cp,
                serie=item.serie,
                numero=item.numero,
                ruc_emisor=item.ruc_emisor,
                razon_emisor=item.razon_emisor,
                fecha_emision=item.fecha_emision,
                total_cp=float(item.total_cp) if item.total_cp is not None else None,
                moneda=item.moneda,
                status=status,
                storage_path=ev.storage_path if ev else None,
                error_message=ev.error_message if ev else None,
                detalle_json=det.detalle_json if det else None,
            )
        )

    return schemas.XMLReportResponse(
        ruc=ruc,
        periodo=periodo,
        total_items=total_items,
        ok=ok,
        error=error,
        not_found=not_found,
        auth=auth,
        pending=pending,
        items=items,
    )


@router.get("/report/export", response_model=schemas.XMLReportExportResponse)
def export_report(ruc: str, periodo: str, db: Session = Depends(get_db)):
    res = build_reporte_detalle(db, ruc=ruc, periodo=periodo)
    msg = f"Reporte generado con {res['rows']} filas."
    return schemas.XMLReportExportResponse(
        ruc=ruc,
        periodo=periodo,
        path=res["path"],
        rows=res["rows"],
        message=msg,
    )


@router.get("/runs", response_model=List[schemas.XMLRunStatusResponse])
def list_runs(ruc: Optional[str] = None, periodo: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(RCERun).filter(RCERun.modulo == "XML")
    if ruc:
        q = q.filter(RCERun.ruc_empresa == ruc)
    if periodo:
        q = q.filter(RCERun.periodo == periodo)
    return q.order_by(RCERun.started_at.desc()).limit(50).all()


@router.get("/repository", response_model=schemas.XMLRepositoryResponse)
def repository(
    periodo: Optional[str] = None,
    ruc_empresa: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)

    q = (
        db.query(RCEPropuestaItem, CPEEvidencia, Empresa)
        .outerjoin(
            CPEEvidencia,
            and_(
                CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id,
                CPEEvidencia.tipo == "XML",
            ),
        )
        .join(Empresa, Empresa.ruc == RCEPropuestaItem.ruc_empresa)
    )

    if periodo:
        q = q.filter(RCEPropuestaItem.periodo == periodo)
    if ruc_empresa:
        q = q.filter(RCEPropuestaItem.ruc_empresa == ruc_empresa)

    if search:
        like = f"%{search}%"
        q = q.filter(
            (RCEPropuestaItem.ruc_emisor.ilike(like))
            | (RCEPropuestaItem.serie.ilike(like))
            | (RCEPropuestaItem.numero.ilike(like))
            | (RCEPropuestaItem.razon_emisor.ilike(like))
        )

    if status:
        # Normalizamos "MISSING" a NOT_FOUND si el frontend lo usa.
        normalized = status.upper()
        if normalized == "MISSING":
            normalized = "NOT_FOUND"
        q = q.filter(CPEEvidencia.status == normalized)

    total = q.count()
    pages = (total + page_size - 1) // page_size

    rows = (
        q.order_by(RCEPropuestaItem.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for item, ev, emp in rows:
        status_xml = ev.status if ev else "PENDING"
        items.append(
            schemas.XMLRepositoryItemResponse(
                id=item.id,
                ruc_empresa=item.ruc_empresa,
                razon_social_empresa=emp.razon_social if emp else None,
                ruc_emisor=item.ruc_emisor,
                razon_social_emisor=item.razon_emisor,
                tipo_comprobante=item.tipo_cp,
                serie=item.serie,
                numero=item.numero,
                fecha_emision=item.fecha_emision,
                moneda=item.moneda,
                total=float(item.total_cp) if item.total_cp is not None else None,
                status_xml=status_xml,
                xml_path=ev.storage_path if ev else None,
                error_message=ev.error_message if ev else None,
            )
        )

    return schemas.XMLRepositoryResponse(
        total=total,
        page=page,
        pages=pages,
        items=items,
    )


@router.post("/retry", response_model=schemas.XMLRetryResponse)
def retry_item(item_id: int, db: Session = Depends(get_db)):
    ev = (
        db.query(CPEEvidencia)
        .filter(CPEEvidencia.propuesta_item_id == item_id, CPEEvidencia.tipo == "XML")
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada para ese item")

    ev.status = "PENDING"
    ev.error_message = None
    ev.next_retry_at = None
    ev.attempt_count = 0
    db.commit()

    return schemas.XMLRetryResponse(ok=True, item_id=item_id, message="Reintento marcado")
