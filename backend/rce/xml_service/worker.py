import time

from core.database import db_session, RCERun, RCEPropuestaItem, CPEEvidencia
from .job import run_xml_job_for_empresa_periodo

POLL_SECONDS = 3


def pick_next_run():
    with db_session() as db:
        run = (
            db.query(RCERun)
            # Solo ejecutar trabajos encolados explícitamente.
            # ERROR/PARTIAL se reintentan solo cuando el frontend vuelve a encolarlos.
            .filter(RCERun.modulo == "XML", RCERun.status == "PENDING")
            .order_by(RCERun.started_at.asc().nullsfirst(), RCERun.id.asc())
            .first()
        )
        if not run:
            return None
        return run.id, run.ruc_empresa, run.periodo, run.stats_json or {}


def _has_pending_items(ruc: str, periodo: str) -> bool:
    with db_session() as db:
        # Hay trabajo si existe item sin OK/NOT_FOUND
        q = (
            db.query(RCEPropuestaItem.id)
            .outerjoin(
                CPEEvidencia,
                (CPEEvidencia.propuesta_item_id == RCEPropuestaItem.id)
                & (CPEEvidencia.tipo == "XML"),
            )
            .filter(RCEPropuestaItem.ruc_empresa == ruc, RCEPropuestaItem.periodo == periodo)
            .filter((CPEEvidencia.id == None) | (CPEEvidencia.status.notin_(["OK", "NOT_FOUND"])))
        )
        return db.query(q.exists()).scalar()


def main():
    print("🔧 XML Worker iniciado. Esperando jobs...")
    while True:
        picked = pick_next_run()
        if not picked:
            time.sleep(POLL_SECONDS)
            continue

        run_id, ruc, periodo, stats = picked
        limit = stats.get("limit")
        headless = stats.get("headless", True)

        if not _has_pending_items(ruc, periodo):
            with db_session() as db:
                run = db.query(RCERun).filter(RCERun.id == run_id).first()
                if run:
                    run.status = "OK"
                    run.error_message = None
                    db.commit()
            continue

        try:
            run_xml_job_for_empresa_periodo(ruc, periodo, limit=limit, headless=headless, run_id=run_id)
        except Exception as e:
            with db_session() as db:
                run = db.query(RCERun).filter(RCERun.id == run_id).first()
                if run:
                    run.status = "ERROR"
                    run.error_message = str(e)
                    db.commit()


if __name__ == "__main__":
    main()
