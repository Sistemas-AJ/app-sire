from core.database import db_session
from rce.propuesta.repository import get_empresas_activas


def run_listado_empresas():
    with db_session() as db:
        empresas = get_empresas_activas(db)
        print(f"📌 Empresas activas con credenciales: {len(empresas)}")
        for e in empresas:
            print(f" - {e.ruc} | {e.razon_social} | usuario_sol={e.usuario_sol}")

if __name__ == "__main__":
    run_listado_empresas()
