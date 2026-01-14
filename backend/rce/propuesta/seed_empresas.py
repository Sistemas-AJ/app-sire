from typing import Dict, Any
from core.database import db_session, Empresa, EmpresaSire

def seed_empresas_y_sire(payload: Dict[str, Dict[str, Any]]) -> None:
    with db_session() as db:
        ins_emp, upd_emp, ins_sire, upd_sire = 0, 0, 0, 0

        for ruc, data in payload.items():
            ruc = str(ruc).strip()

            # --- EMPRESA BASE ---
            sol = data.get("sol") or {}
            usuario_sol = (sol.get("usuario") or "").strip() or None
            clave_sol = (sol.get("clave") or "").strip() or None

            emp = db.query(Empresa).filter(Empresa.ruc == ruc).first()
            if emp is None:
                emp = Empresa(
                    ruc=ruc,
                    razon_social=data.get("razon_social") or "SIN RAZON SOCIAL",
                    usuario_sol=usuario_sol,
                    clave_sol=clave_sol,
                    activo=bool(data.get("activo", True)),
                )
                db.add(emp)
                ins_emp += 1
            else:
                emp.razon_social = data.get("razon_social") or emp.razon_social
                emp.usuario_sol = usuario_sol
                emp.clave_sol = clave_sol
                emp.activo = bool(data.get("activo", emp.activo))
                upd_emp += 1

            # --- CREDENCIALES SIRE ---
            sire = data.get("sire") or {}
            if sire:
                client_id = (sire.get("client_id") or "").strip()
                client_secret = (sire.get("client_secret") or "").strip()
                if not client_id or not client_secret:
                    raise ValueError(f"Faltan client_id/client_secret para RUC {ruc}")

                # username = ruc + usuario_sol (según tu regla)
                username = (sire.get("username") or "").strip()
                if not username:
                    if not usuario_sol:
                        raise ValueError(f"No hay usuario_sol para construir username SIRE en RUC {ruc}")
                    username = f"{ruc}{usuario_sol}"

                cred = db.query(EmpresaSire).filter(EmpresaSire.ruc_empresa == ruc).first()
                if cred is None:
                    cred = EmpresaSire(
                        ruc_empresa=ruc,
                        client_id=client_id,
                        client_secret=client_secret,
                        username=username,
                        activo=True
                    )
                    db.add(cred)
                    ins_sire += 1
                else:
                    cred.client_id = client_id
                    cred.client_secret = client_secret
                    cred.username = username
                    cred.activo = True
                    upd_sire += 1

        db.commit()
        print(f"✅ Seed OK | empresas: +{ins_emp}/~{upd_emp} | sire: +{ins_sire}/~{upd_sire}")


if __name__ == "__main__":
    EMPRESAS = {
        "20600750233": {
            "razon_social": "MAXAD CONTRATISTAS GENERALES",
            "activo": True,
            "sol": {"usuario": "ERRITETR", "clave": "Maxad2060"},
            "sire": {"client_id": "b907060e-b47c-42aa-89c8-95549d951c20", "client_secret": "qaAW6n4CokkhO2JS+VE+TQ=="},
        }, 
        "20529929821": {
            "razon_social": "ADOLFO JURADO CONTRATISTAS GENERALES EIRL",
            "activo": True,
            "sol": {"usuario": "TIERTHRI", "clave": "ophicanas"},
            "sire": {"client_id": "7e655bfd-3091-4afd-85cc-4ff9e936e3f6", "client_secret": "fqUXAh9PVRuqiSCHyHEKhQ=="},
        },
        "20601080428": {
            "razon_social": "INSTITUTO MEDICO CASTILLA S.A.C.",
            "activo": True,
            "sol": {"usuario": "ONEVERRU", "clave": "imcSAC2023"},
            "sire": {"client_id": "30f1bef6-cfd5-4487-b681-80895e0952ba", "client_secret": "VK/wSBpL8ertsq8bOc6hBA=="},
        },

    }
    seed_empresas_y_sire(EMPRESAS)
