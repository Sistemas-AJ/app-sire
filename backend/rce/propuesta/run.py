import argparse
from datetime import datetime
from rce.propuesta.load_items import load_rce_items_from_csv
from core.database import db_session, Empresa, EmpresaSire, RCEPropuestaFile

from rce.propuesta.sire_auth import get_token_sire
from rce.propuesta.state_store import load_state, save_state, token_is_valid
from rce.propuesta.sire_client import (
    generar_ticket_exportacion_propuesta,
    esperar_hasta_terminado,
    extraer_params_descarga,
    descargar_archivo_reporte,
)
from rce.propuesta.file_ops import ensure_dirs, save_zip_and_extract_csv, csv_to_xlsx, sha256_bytes


def procesar_empresa(db, emp: Empresa, cred: EmpresaSire, periodo: str, fec_ini: str, fec_fin: str):
    ruc = emp.ruc

    # 1) token (cache json)
    st = load_state(ruc)
    if not token_is_valid(st):
        token, exp = get_token_sire(
            client_id=cred.client_id,
            client_secret=cred.client_secret,
            ruc=emp.ruc,
            usuario_sol=emp.usuario_sol,
            clave_sol=emp.clave_sol,
        )
        save_state(ruc, {"token": token, "token_expires_at": exp})
        st = load_state(ruc)
    token = st["token"]

    # 2) generar ticket
    ticket = generar_ticket_exportacion_propuesta(
        token=token,
        per=periodo,
        fec_ini=fec_ini,
        fec_fin=fec_fin,
    )
    save_state(ruc, {"last_ticket": ticket, "last_ticket_periodo": periodo})

    # 3) esperar proceso terminado
    reg = esperar_hasta_terminado(token, periodo, ticket)

    # 4) extraer params descarga
    nom_zip, cod_tipo, cod_proc = extraer_params_descarga(reg)
    save_state(ruc, {"last_cod_proceso": cod_proc, "last_nom_archivo": nom_zip})

    # 5) descargar zip bytes
    zip_bytes = descargar_archivo_reporte(
        token=token,
        per=periodo,
        numTicket=ticket,
        codProceso=cod_proc,
        nomArchivoReporte=nom_zip,
        codTipoArchivoReporte=cod_tipo,
    )
    digest = sha256_bytes(zip_bytes)

    # 6) guardar/extraer/convertir
    out_dir = ensure_dirs(periodo, ruc)
    csv_path = save_zip_and_extract_csv(zip_bytes, out_dir, zip_name=nom_zip)
    xlsx_path = f"{out_dir}/propuesta_{periodo}.xlsx"
    csv_to_xlsx(csv_path, xlsx_path)
    load_rce_items_from_csv(db, ruc, periodo, csv_path, delimiter=",")

    # 7) registrar en BD (upsert simple)
    row = (
        db.query(RCEPropuestaFile)
        .filter(RCEPropuestaFile.ruc_empresa == ruc, RCEPropuestaFile.periodo == periodo)
        .first()
    )
    if not row:
        row = RCEPropuestaFile(
            ruc_empresa=ruc,
            periodo=periodo,
            num_ticket=ticket,
            cod_proceso=cod_proc,
            storage_path=out_dir,
            filename=nom_zip,
            sha256=digest,
        )
        db.add(row)
    else:
        row.num_ticket = ticket
        row.cod_proceso = cod_proc
        row.storage_path = out_dir
        row.filename = nom_zip
        row.sha256 = digest

    db.commit()

    return {
        "ruc": ruc,
        "ticket": ticket,
        "csv": csv_path,
        "xlsx": xlsx_path,
        "zip": f"{out_dir}/{nom_zip}",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--periodo", required=True, help="YYYYMM")
    ap.add_argument("--fec-ini", required=True, help="YYYY-MM-DD")
    ap.add_argument("--fec-fin", required=True, help="YYYY-MM-DD")
    ap.add_argument("--ruc", default=None, help="Opcional: solo una empresa")
    args = ap.parse_args()

    periodo = args.periodo
    fec_ini = args.fec_ini
    fec_fin = args.fec_fin

    with db_session() as db:
        q = (
            db.query(Empresa, EmpresaSire)
            .join(EmpresaSire, EmpresaSire.ruc_empresa == Empresa.ruc)
            .filter(Empresa.activo == True)
            .filter(EmpresaSire.activo == True)
        )

        if args.ruc:
            q = q.filter(Empresa.ruc == args.ruc)

        pairs = q.all()
        print(f"📌 Empresas a procesar: {len(pairs)} | periodo={periodo} rango={fec_ini}..{fec_fin}")

        ok = 0
        fail = 0

        for emp, cred in pairs:
            print(f"\n==> {emp.ruc} | {emp.razon_social}")
            try:
                res = procesar_empresa(db, emp, cred, periodo, fec_ini, fec_fin)
                ok += 1
                print("✅ OK")
                print(f"   ticket: {res['ticket']}")
                print(f"   xlsx:   {res['xlsx']}")
            except Exception as e:
                fail += 1
                print(f"❌ ERROR {emp.ruc}: {e}")

        print(f"\n🏁 Terminado: OK={ok} ERROR={fail}")


if __name__ == "__main__":
    main()
