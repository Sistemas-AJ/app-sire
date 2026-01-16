import time
from typing import Optional
from datetime import datetime, timezone

from core.database import db_session, RCERun
from .repository import (
    get_empresa,
    fetch_items_pendientes_xml,
    get_or_create_evidencia,
    get_or_create_evidencia_xml,
    mark_attempt,
)
from .scraper import SolXMLScraper
from rce.xml_detail import parse_detalle, save_detalle
from .config import MAX_ATTEMPTS_PER_ITEM, WAIT_ON_FAIL_SECONDS

TIPO_CP_TO_LABEL = {
    "01": "Factura",
    "07": "Factura - Nota de Crédito",
    "08": "Factura - Nota de Débito",
}

_STOP_REQUESTED = set()

def request_stop(ruc: Optional[str] = None, periodo: Optional[str] = None) -> None:
    if ruc or periodo:
        _STOP_REQUESTED.add((ruc, periodo))
    else:
        _STOP_REQUESTED.add((None, None))

    with db_session() as db:
        base = db.query(RCERun).filter(RCERun.modulo == "XML")
        if ruc:
            base = base.filter(RCERun.ruc_empresa == ruc)
        if periodo:
            base = base.filter(RCERun.periodo == periodo)

        running = base.filter(RCERun.status == "RUNNING")
        running.update({"status": "STOP_REQUESTED"}, synchronize_session=False)

        pending = base.filter(RCERun.status == "PENDING")
        pending.update({"status": "STOPPED"}, synchronize_session=False)
        db.commit()

def _should_stop_db(run_id: Optional[int], ruc: str, periodo: str) -> bool:
    with db_session() as db:
        if run_id:
            run = db.query(RCERun).filter(RCERun.id == run_id).first()
            return bool(run and run.status in ("STOP_REQUESTED", "STOPPED"))
        q = (
            db.query(RCERun)
            .filter(RCERun.modulo == "XML", RCERun.ruc_empresa == ruc, RCERun.periodo == periodo)
            .filter(RCERun.status.in_(["STOP_REQUESTED", "STOPPED"]))
        )
        return db.query(q.exists()).scalar()


def _should_stop(ruc: str, periodo: str, run_id: Optional[int]) -> bool:
    return (
        (None, None) in _STOP_REQUESTED
        or (ruc, None) in _STOP_REQUESTED
        or (ruc, periodo) in _STOP_REQUESTED
        or _should_stop_db(run_id, ruc, periodo)
    )

def tipo_label_from_tipo_cp(tipo_cp: str) -> str:
    return TIPO_CP_TO_LABEL.get(tipo_cp, "Factura")

def run_xml_job_for_empresa_periodo(
    ruc_empresa: str,
    periodo: str,
    limit: Optional[int] = None,
    headless: bool = False,
    run_id: Optional[int] = None,
):
    # Nuevo run: limpiar stops previos para esta empresa/periodo
    _STOP_REQUESTED.discard((None, None))
    _STOP_REQUESTED.discard((ruc_empresa, periodo))
    _STOP_REQUESTED.discard((ruc_empresa, None))
    with db_session() as db:
        emp = get_empresa(db, ruc_empresa)
        if not emp:
            raise RuntimeError(f"No existe empresa activa {ruc_empresa}")

        emp_ruc = emp.ruc
        emp_usuario = emp.usuario_sol
        emp_clave = emp.clave_sol

        raw_items = fetch_items_pendientes_xml(db, ruc_empresa, periodo, limit=limit)
        items = [
            {
                "id": it.id,
                "ruc_empresa": it.ruc_empresa,
                "periodo": it.periodo,
                "tipo_cp": it.tipo_cp,
                "serie": it.serie,
                "numero": it.numero,
                "ruc_emisor": it.ruc_emisor,
            }
            for it in raw_items
        ]
        print(f"📌 Pendientes XML: {len(items)} | empresa={ruc_empresa} periodo={periodo}")

        if not items:
            if run_id:
                run = db.query(RCERun).filter(RCERun.id == run_id).first()
                if run:
                    run.status = "OK"
                    run.finished_at = datetime.now(timezone.utc)
                    run.stats_json = {"ok": 0, "error": 0, "auth": 0, "not_found": 0}
                    db.commit()
            return

        if run_id:
            run = db.query(RCERun).filter(RCERun.id == run_id).first()
            if run:
                run.status = "RUNNING"
                run.started_at = datetime.now(timezone.utc)
                db.commit()

    # scraper fuera del scope DB para no tener session abierta en todo el loop
    scraper = SolXMLScraper(headless=headless)
    scraper.start()
    ok_count = 0
    error_count = 0
    not_found_count = 0
    auth_count = 0
    stopped = False
    limit_reached = False
    processed_count = 0
    try:
        ok_login = scraper.login_and_navigate(emp_ruc, emp_usuario, emp_clave)
        if not ok_login:
            raise RuntimeError("No se pudo loguear/navegar en SOL")

        for item in items:
            if _should_stop(emp_ruc, periodo, run_id):
                stopped = True
                print(f"🛑 Stop solicitado. Deteniendo empresa {emp_ruc} periodo {periodo}.")
                break
            # reabrimos sesión DB por item (simple y seguro)
            with db_session() as db:
                ev = get_or_create_evidencia_xml(db, item["id"])

                # Tipo 14 (Servicios): no hay etiqueta XML para descargar.
                if str(item["tipo_cp"]).strip() == "14":
                    mark_attempt(
                        db,
                        ev,
                        status="NOT_FOUND",
                        error_message="SERVICIOS (tipo_cp=14): sin etiqueta para descarga",
                        wait_seconds=0,
                    )
                    ev.attempt_count = MAX_ATTEMPTS_PER_ITEM
                    db.commit()
                    not_found_count += 1
                    processed_count += 1
                    print(f"⏭️ SERVICIOS item_id={item['id']} tipo_cp=14 marcado NOT_FOUND")
                    continue

                # idempotencia: si ya está OK o marcado NOT_FOUND, saltar
                if ev.status == "OK":
                    print(f"⏭️ SKIP OK item_id={item['id']}")
                    continue
                if ev.status == "NOT_FOUND":
                    print(f"⏭️ SKIP NOT_FOUND item_id={item['id']}")
                    continue

            # intentamos descargar (sin DB abierta)
            busq = _to_busqueda(item)

            result = scraper.descargar_xml(item["ruc_empresa"], item["periodo"], busq)

            with db_session() as db:
                ev = get_or_create_evidencia_xml(db, item["id"])

                if result.ok:
                    mark_attempt(
                        db,
                        ev,
                        status="OK",
                        error_message=None,
                        storage_path=result.xml_path,
                        sha256=result.sha256,
                        downloaded_at=datetime.now(timezone.utc),
                        wait_seconds=0,
                    )
                    if result.pdf_path:
                        ev_pdf = get_or_create_evidencia(db, item["id"], "PDF")
                        mark_attempt(
                            db,
                            ev_pdf,
                            status="OK",
                            error_message=None,
                            storage_path=result.pdf_path,
                            wait_seconds=0,
                        )
                    try:
                        detalle_json = parse_detalle(result.xml_path)
                        save_detalle(
                            db,
                            propuesta_item_id=item["id"],
                            detalle_json=detalle_json,
                            source_sha256=result.sha256,
                        )
                    except Exception as e:
                        print(f"⚠️ Detalle no extraído item_id={item['id']}: {e}")
                    db.commit()
                    ok_count += 1
                    processed_count += 1
                    print(f"✅ OK item_id={item['id']} xml={result.xml_path}")
                else:
                    status = "AUTH" if result.auth_error else "ERROR"
                    mark_attempt(
                        db,
                        ev,
                        status=status,
                        error_message=result.error,
                        wait_seconds=WAIT_ON_FAIL_SECONDS,
                    )
                    db.commit()
                    if status == "AUTH":
                        auth_count += 1
                    else:
                        error_count += 1
                    processed_count += 1
                    print(f"❌ {status} item_id={item['id']} err={result.error}")

                    # si fue AUTH, podrías relogin inmediato:
                    if status == "AUTH":
                        print("🔁 Re-login por AUTH…")
                        try:
                            ok = scraper.login_and_navigate(emp_ruc, emp_usuario, emp_clave)
                            if not ok:
                                print("⚠️ Re-login falló, continuando con el siguiente…")
                        except Exception as e:
                            print(f"⚠️ Re-login excepción: {e}")

            # pequeña pausa para no matar UI
            time.sleep(0.8)
            if limit is not None and processed_count >= limit:
                limit_reached = True
                print(f"⏹️ Límite alcanzado ({limit}). Deteniendo empresa {emp_ruc} periodo {periodo}.")
                break

    finally:
        scraper.stop()
        if run_id:
            status = "OK"
            if stopped:
                status = "STOPPED"
            elif error_count > 0 or auth_count > 0:
                status = "PARTIAL"
            with db_session() as db:
                run = db.query(RCERun).filter(RCERun.id == run_id).first()
                if run:
                    run.status = status
                    run.finished_at = datetime.now(timezone.utc)
                    run.stats_json = {
                        "ok": ok_count,
                        "error": error_count,
                        "auth": auth_count,
                        "not_found": not_found_count,
                        "limit": limit,
                        "limit_reached": limit_reached,
                    }
                    if status == "STOPPED":
                        run.error_message = "Detenido por el usuario"
                    elif status != "OK" and run.error_message is None:
                        run.error_message = "Proceso con errores"
                    db.commit()


def _to_busqueda(item) -> "BusquedaComprobante":
    # Mapeo tipo_cp → label del dropdown (ajusta si aparecen más)
    tipo_label = tipo_label_from_tipo_cp(item["tipo_cp"])

    from rce.sol.consulta_individual import BusquedaComprobante
    return BusquedaComprobante(
        ruc_emisor=item["ruc_emisor"],
        serie=item["serie"],
        numero=item["numero"],
        tipo_label=tipo_label,
    )
