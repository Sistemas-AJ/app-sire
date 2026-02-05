import time
from datetime import datetime, date

from sqlalchemy import and_

from core.database import SessionLocal, Empresa, BuzonRun
import main_auto


POLL_SECONDS = 3
RUN_STATUSES = ("PENDING", "ERROR", "PARTIAL")


def _stop_requested(run_id: int) -> bool:
    db = SessionLocal()
    try:
        run = db.query(BuzonRun).filter(BuzonRun.id == run_id).first()
        return bool(run and run.stop_requested)
    finally:
        db.close()


def _ensure_daily_runs(db, today: date):
    empresas = db.query(Empresa).filter(Empresa.activo == True).all()
    for emp in empresas:
        exists = db.query(BuzonRun).filter(
            and_(
                BuzonRun.ruc_empresa == emp.ruc,
                BuzonRun.fecha_desde == today,
            )
        ).first()
        if exists:
            continue
        run = BuzonRun(
            ruc_empresa=emp.ruc,
            fecha_desde=today,
            fecha_hasta=today,
            status="PENDING",
            retry_mode="todo",
            headless=True,
            queued=False,
        )
        db.add(run)
    db.commit()


def _pick_next_run(db):
    return (
        db.query(BuzonRun)
        .filter(BuzonRun.status.in_(RUN_STATUSES), BuzonRun.queued == True)
        .order_by(BuzonRun.id.asc())
        .with_for_update(skip_locked=True)
        .first()
    )


def _summarize_stats(items):
    if not items:
        return {"ok": 0, "skipped": 0, "errors": 0, "analizados": 0}
    totals = {"ok": 0, "skipped": 0, "errors": 0, "analizados": 0}
    for item in items:
        totals["ok"] += int(item.get("descargas_ok", 0))
        totals["skipped"] += int(item.get("skipped", 0))
        totals["errors"] += int(item.get("errors", 0))
        totals["analizados"] += int(item.get("analizados", 0))
    return totals


def run_worker():
    print("🔧 Buzon Worker iniciado. Esperando jobs...")
    last_daily_reset = None

    while True:
        db = SessionLocal()
        try:
            today = datetime.now().date()
            if last_daily_reset != today:
                _ensure_daily_runs(db, today)
                last_daily_reset = today

            run = _pick_next_run(db)
            if not run:
                db.commit()
                time.sleep(POLL_SECONDS)
                continue

            if run.stop_requested:
                run.status = "STOPPED"
                run.finished_at = datetime.now()
                db.commit()
                continue

            run.status = "RUNNING"
            run.started_at = datetime.now()
            run.stop_requested = False
            db.commit()
            run_id = run.id
            ruc = run.ruc_empresa
            fecha_desde = run.fecha_desde
            fecha_hasta = run.fecha_hasta
            headless = bool(run.headless)
            retry_mode = run.retry_mode or "todo"
        finally:
            db.close()

        try:
            result = main_auto.run_automation_process(
                retry_mode=retry_mode in ("solo_fallidos", "pendientes"),
                days_back=90,
                headless=headless,
                rucs=[ruc],
                date_from=fecha_desde,
                date_to=fecha_hasta,
                stop_checker=lambda: _stop_requested(run_id),
            )
            stopped = bool(result.get("stopped"))
            items = result.get("items", [])
            totals = _summarize_stats(items)

            db = SessionLocal()
            try:
                run = db.query(BuzonRun).filter(BuzonRun.id == run_id).first()
                if not run:
                    continue
                run.stats_json = totals
                run.finished_at = datetime.now()
                run.queued = False
                if stopped:
                    run.status = "STOPPED"
                elif totals["errors"] > 0:
                    run.status = "PARTIAL"
                else:
                    run.status = "OK"
                db.commit()
            finally:
                db.close()
        except Exception as e:
            db = SessionLocal()
            try:
                run = db.query(BuzonRun).filter(BuzonRun.id == run_id).first()
                if run:
                    run.status = "ERROR"
                    run.last_error = str(e)
                    run.finished_at = datetime.now()
                    run.queued = False
                    db.commit()
            finally:
                db.close()
            print(f"🔥 Error en buzon worker: {e}")
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run_worker()
