from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.database import Empresa, RCEPropuestaItem, CPEEvidencia


def get_empresa(db: Session, ruc: str) -> Optional[Empresa]:
    return db.query(Empresa).filter(Empresa.ruc == ruc, Empresa.activo == True).first()


def fetch_items_pendientes_xml(
    db: Session,
    ruc_empresa: str,
    periodo: str,
    limit: int = 200,
) -> List[RCEPropuestaItem]:
    """
    Devuelve items que NO tienen evidencia XML OK.
    (Si no hay evidencia, también entra).
    """
    # Left join evidencias XML
    q = (
        db.query(RCEPropuestaItem)
        .outerjoin(
            CPEEvidencia,
            and_(
                CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id,
                CPEEvidencia.tipo == "XML",
            )
        )
        .filter(RCEPropuestaItem.ruc_empresa == ruc_empresa)
        .filter(RCEPropuestaItem.periodo == periodo)
        .filter(
            (CPEEvidencia.id == None) | (CPEEvidencia.status != "OK")
        )
        .order_by(RCEPropuestaItem.id.asc())
        .limit(limit)
    )
    return q.all()


def get_or_create_evidencia_xml(db: Session, item_id: int) -> CPEEvidencia:
    ev = (
        db.query(CPEEvidencia)
        .filter(CPEEvidencia.propuesta_item_id == item_id, CPEEvidencia.tipo == "XML")
        .first()
    )
    if ev:
        return ev
    ev = CPEEvidencia(
        propuesta_item_id=item_id,
        tipo="XML",
        status="PENDING",
        attempt_count=0,
    )
    db.add(ev)
    db.flush()  # para obtener id sin commit
    return ev


def mark_attempt(
    db: Session,
    ev: CPEEvidencia,
    status: str,
    error_message: Optional[str] = None,
    storage_path: Optional[str] = None,
    sha256: Optional[str] = None,
    downloaded_at: Optional[datetime] = None,
    wait_seconds: int = 0,
) -> None:
    now = datetime.now(timezone.utc)

    ev.attempt_count = (ev.attempt_count or 0) + 1
    ev.last_attempt_at = now
    ev.status = status
    ev.error_message = error_message

    if storage_path:
        ev.storage_path = storage_path
    if sha256:
        ev.sha256 = sha256
    if downloaded_at:
        ev.downloaded_at = downloaded_at

    if wait_seconds and status in ("ERROR", "AUTH"):
        ev.next_retry_at = now + timedelta(seconds=wait_seconds)
    else:
        ev.next_retry_at = None

    db.flush()
