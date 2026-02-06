import os

from datetime import datetime

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

def run_one(ruc: str, periodo: str, fec_ini: str, fec_fin: str):
    with db_session() as db:
        emp = db.query(Empresa).filter(Empresa.ruc == ruc).first()
        if not emp:
            raise RuntimeError(f"No existe Empresa {ruc}")
        cred = db.query(EmpresaSire).filter(EmpresaSire.ruc_empresa == ruc).first()
        if not cred:
            raise RuntimeError(f"No existe EmpresaSire para {ruc}")

        # 1) token cache
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

        # 2) ticket
        ticket = generar_ticket_exportacion_propuesta(token, periodo, fec_ini, fec_fin)
        save_state(ruc, {"last_ticket": ticket, "last_ticket_periodo": periodo})

        # 3) esperar terminado
        reg = esperar_hasta_terminado(token, periodo, ticket)

        # 4) datos de descarga
        nom_zip, cod_tipo, cod_proc = extraer_params_descarga(reg)
        save_state(ruc, {"last_cod_proceso": cod_proc, "last_nom_archivo": f"propuesta_{periodo}.zip"})

        # 5) descargar bytes
        zip_bytes = descargar_archivo_reporte(
            token=token,
            per=periodo,
            numTicket=ticket,
            codProceso=cod_proc,
            nomArchivoReporte=nom_zip,
            codTipoArchivoReporte=cod_tipo,
        )
        digest = sha256_bytes(zip_bytes)

        # 6) guardar/extract/convert (solo si el hash cambió)
        out_dir = ensure_dirs(periodo, ruc)
        zip_path = f"{out_dir}/propuesta_{periodo}.zip"
        csv_path = f"{out_dir}/propuesta_{periodo}.csv"
        xlsx_path = f"{out_dir}/propuesta_{periodo}.xlsx"

        row = (
            db.query(RCEPropuestaFile)
            .filter(RCEPropuestaFile.ruc_empresa == ruc, RCEPropuestaFile.periodo == periodo)
            .first()
        )
        same_hash = row and row.sha256 == digest
        files_exist = all(map(lambda p: p and os.path.exists(p), [zip_path, csv_path, xlsx_path]))

        if same_hash and files_exist:
            print("🔁 ZIP sin cambios: se mantiene archivo existente.")
        else:
            csv_path = save_zip_and_extract_csv(zip_bytes, out_dir, periodo=periodo)
            csv_to_xlsx(csv_path, xlsx_path)

        # 7) registrar en BD
        if not row:
            row = RCEPropuestaFile(
                ruc_empresa=ruc,
                periodo=periodo,
                fec_ini=datetime.strptime(fec_ini, "%Y-%m-%d").date(),
                fec_fin=datetime.strptime(fec_fin, "%Y-%m-%d").date(),
                num_ticket=ticket,
                cod_proceso=cod_proc,
                storage_path=out_dir,
                filename=f"propuesta_{periodo}.zip",
                sha256=digest,
            )
            db.add(row)
        else:
            row.num_ticket = ticket
            row.cod_proceso = cod_proc
            row.storage_path = out_dir
            row.filename = f"propuesta_{periodo}.zip"
            row.sha256 = digest
            row.fec_ini = datetime.strptime(fec_ini, "%Y-%m-%d").date()
            row.fec_fin = datetime.strptime(fec_fin, "%Y-%m-%d").date()

        db.commit()

        print("✅ OK")
        print("  ticket:", ticket)
        print("  csv:", csv_path)
        print("  xlsx:", xlsx_path)

if __name__ == "__main__":
    # cambia el ruc al que quieras probar
    run_one(
        ruc="20529929821",
        periodo="202512",
        fec_ini="2025-01-01",
        fec_fin="2025-12-31",
    )
