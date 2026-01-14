from sqlalchemy.orm import Session
from core.database import db_session, RCEPropuestaFile
from .repo import get_empresas_sire_activas
from .state_store import load_state, save_state, token_is_valid
from .sire_auth import get_token_sire
from .sire_client import (
    generar_ticket_exportacion_propuesta,
    esperar_hasta_terminado,
    extraer_params_descarga,
    descargar_archivo_reporte,
)
from .file_ops import ensure_dirs, save_zip_and_extract_csv, csv_to_xlsx, sha256_bytes

def procesar_empresa_periodo(db: Session, empresa, cred_sire, periodo: str, fec_ini: str, fec_fin: str):
    ruc = empresa.ruc
    state = load_state(ruc)

    # 1) Token
    if not token_is_valid(state):
        token, exp = get_token_sire(
            client_id=cred_sire.client_id,
            client_secret=cred_sire.client_secret,
            ruc=empresa.ruc,
            usuario_sol=empresa.usuario_sol,
            clave_sol=empresa.clave_sol
        )
        save_state(ruc, {"token": token, "token_expires_at": exp})
        state = load_state(ruc)

    token = state["token"]

    # 2) Ticket propuesta
    ticket = generar_ticket_exportacion_propuesta(
        token=token,
        per=periodo,
        codTipoArchivo="1",
        codOrigenEnvio="2",
        fecIni=fec_ini,
        fecFin=fec_fin,
        codTipoCDP="01",
    )
    save_state(ruc, {"last_ticket": ticket, "last_ticket_periodo": periodo})

    # 3) Estado
    reg = esperar_hasta_terminado(token, periodo, ticket)

    # 4) Params descarga
    nom, cod_tipo, cod_proceso = extraer_params_descarga(reg)
    save_state(ruc, {"last_cod_proceso": cod_proceso, "last_nom_archivo": f"propuesta_{periodo}.zip"})

    # 5) Descargar zip
    zip_bytes = descargar_archivo_reporte(
        token=token,
        per=periodo,
        numTicket=ticket,
        codProceso=cod_proceso,
        nomArchivoReporte=nom,
        codTipoArchivoReporte=cod_tipo,
    )
    digest = sha256_bytes(zip_bytes)

    # 6) Guardar/extract/convert
    out_dir = ensure_dirs(periodo, ruc)
    csv_path = save_zip_and_extract_csv(zip_bytes, out_dir=out_dir, periodo=periodo)
    xlsx_path = f"{out_dir}/propuesta_{periodo}.xlsx"
    csv_to_xlsx(csv_path, xlsx_path)

    # 7) Persistir file record (si ya existe por periodo, actualiza)
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
            cod_proceso=cod_proceso,
            storage_path=out_dir,
            filename=f"propuesta_{periodo}.zip",
            sha256=digest,
        )
        db.add(row)
    else:
        row.num_ticket = ticket
        row.cod_proceso = cod_proceso
        row.storage_path = out_dir
        row.filename = f"propuesta_{periodo}.zip"
        row.sha256 = digest

    db.commit()
    return {"ruc": ruc, "periodo": periodo, "csv": csv_path, "xlsx": xlsx_path, "ticket": ticket}

def run_pipeline(periodo: str, fec_ini: str, fec_fin: str):
    with db_session() as db:
        pairs = get_empresas_sire_activas(db)
        print(f"Empresas a procesar: {len(pairs)}")

        results = []
        for empresa, cred_sire in pairs:
            print(f"\n==> {empresa.ruc} {empresa.razon_social} periodo {periodo}")
            try:
                res = procesar_empresa_periodo(db, empresa, cred_sire, periodo, fec_ini, fec_fin)
                print(f"✅ OK {empresa.ruc}: {res['xlsx']}")
                results.append(res)
            except Exception as e:
                print(f"❌ ERROR {empresa.ruc}: {e}")
        return results
