import time
from typing import Optional
from datetime import datetime, timezone

from core.database import db_session
from .repository import (
    get_empresa,
    fetch_items_pendientes_xml,
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

def tipo_label_from_tipo_cp(tipo_cp: str) -> str:
    return TIPO_CP_TO_LABEL.get(tipo_cp, "Factura")

def run_xml_job_for_empresa_periodo(
    ruc_empresa: str,
    periodo: str,
    limit: Optional[int] = None,
    headless: bool = False,
):
    with db_session() as db:
        emp = get_empresa(db, ruc_empresa)
        if not emp:
            raise RuntimeError(f"No existe empresa activa {ruc_empresa}")

        items = fetch_items_pendientes_xml(db, ruc_empresa, periodo, limit=limit)
        print(f"📌 Pendientes XML: {len(items)} | empresa={ruc_empresa} periodo={periodo}")

        if not items:
            return

    # scraper fuera del scope DB para no tener session abierta en todo el loop
    scraper = SolXMLScraper(headless=headless)
    scraper.start()
    try:
        ok_login = scraper.login_and_navigate(emp.ruc, emp.usuario_sol, emp.clave_sol)
        if not ok_login:
            raise RuntimeError("No se pudo loguear/navegar en SOL")

        for item in items:
            # reabrimos sesión DB por item (simple y seguro)
            with db_session() as db:
                ev = get_or_create_evidencia_xml(db, item.id)

                # Tipo 14 (Servicios): no hay etiqueta XML para descargar.
                if str(item.tipo_cp).strip() == "14":
                    mark_attempt(
                        db,
                        ev,
                        status="NOT_FOUND",
                        error_message="SERVICIOS (tipo_cp=14): sin etiqueta para descarga",
                        wait_seconds=0,
                    )
                    ev.attempt_count = MAX_ATTEMPTS_PER_ITEM
                    db.commit()
                    print(f"⏭️ SERVICIOS item_id={item.id} tipo_cp=14 marcado NOT_FOUND")
                    continue

                # idempotencia: si ya está OK o marcado NOT_FOUND, saltar
                if ev.status == "OK":
                    print(f"⏭️ SKIP OK item_id={item.id}")
                    continue
                if ev.status == "NOT_FOUND":
                    print(f"⏭️ SKIP NOT_FOUND item_id={item.id}")
                    continue

            # intentamos descargar (sin DB abierta)
            busq = _to_busqueda(item)

            result = scraper.descargar_xml(item.ruc_empresa, item.periodo, busq)

            with db_session() as db:
                ev = get_or_create_evidencia_xml(db, item.id)

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
                    try:
                        detalle_json = parse_detalle(result.xml_path)
                        save_detalle(
                            db,
                            propuesta_item_id=item.id,
                            detalle_json=detalle_json,
                            source_sha256=result.sha256,
                        )
                    except Exception as e:
                        print(f"⚠️ Detalle no extraído item_id={item.id}: {e}")
                    db.commit()
                    print(f"✅ OK item_id={item.id} xml={result.xml_path}")
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
                    print(f"❌ {status} item_id={item.id} err={result.error}")

                    # si fue AUTH, podrías relogin inmediato:
                    if status == "AUTH":
                        print("🔁 Re-login por AUTH…")
                        try:
                            ok = scraper.login_and_navigate(emp.ruc, emp.usuario_sol, emp.clave_sol)
                            if not ok:
                                print("⚠️ Re-login falló, continuando con el siguiente…")
                        except Exception as e:
                            print(f"⚠️ Re-login excepción: {e}")

            # pequeña pausa para no matar UI
            time.sleep(0.8)

    finally:
        scraper.stop()


def _to_busqueda(item) -> "BusquedaComprobante":
    # Mapeo tipo_cp → label del dropdown (ajusta si aparecen más)
    tipo_label = tipo_label_from_tipo_cp(item.tipo_cp)

    from rce.sol.consulta_individual import BusquedaComprobante
    return BusquedaComprobante(
        ruc_emisor=item.ruc_emisor,
        serie=item.serie,
        numero=item.numero,
        tipo_label=tipo_label,
    )
