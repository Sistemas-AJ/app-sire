import argparse
from core.database import db_session, Empresa
from .job import run_xml_job_for_empresa_periodo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--periodo", required=True, help="YYYYMM")
    ap.add_argument("--ruc", default=None, help="Procesar solo 1 empresa")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()

    periodo = args.periodo

    if args.ruc:
        run_xml_job_for_empresa_periodo(args.ruc, periodo, limit=args.limit, headless=args.headless)
        return

    # multiempresa: todas las activas (que tengan items en ese periodo)
    with db_session() as db:
        rucs = [e.ruc for e in db.query(Empresa).filter(Empresa.activo == True).all()]

    for ruc in rucs:
        print(f"\n=== Empresa {ruc} periodo={periodo} ===")
        try:
            run_xml_job_for_empresa_periodo(ruc, periodo, limit=args.limit, headless=args.headless)
        except Exception as e:
            print(f"❌ ERROR empresa {ruc}: {e}")


if __name__ == "__main__":
    main()
