from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
import codecs

from core.database import (
    get_db,
    Empresa,
    EmpresaSire,
    Notificacion,
    RCERun,
    RCEPropuestaFile,
    RCEPropuestaItem,
    CPEEvidencia,
    CPEDetalle,
)
from api import schemas

router = APIRouter(
    prefix="/empresas",
    tags=["empresas"]
)

@router.get("/", response_model=List[schemas.EmpresaResponse])
def listar_empresas(db: Session = Depends(get_db)):
    return db.query(Empresa).filter(Empresa.activo == True).all()

@router.post("/", response_model=schemas.EmpresaResponse)
def crear_empresa(empresa: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    db_empresa = db.query(Empresa).filter(Empresa.ruc == empresa.ruc).first()
    if db_empresa:
        raise HTTPException(status_code=400, detail="Empresa ya registrada")
    
    nuevo = Empresa(**empresa.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.put("/{ruc}", response_model=schemas.EmpresaResponse)
def actualizar_empresa(ruc: str, payload: schemas.EmpresaUpdate, db: Session = Depends(get_db)):
    emp = db.query(Empresa).filter(Empresa.ruc == ruc).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if payload.razon_social is not None:
        emp.razon_social = payload.razon_social
    if payload.usuario_sol is not None:
        emp.usuario_sol = payload.usuario_sol
    if payload.clave_sol is not None:
        emp.clave_sol = payload.clave_sol
    if payload.activo is not None:
        emp.activo = payload.activo

    db.commit()
    db.refresh(emp)
    return emp

@router.delete("/{ruc}")
def eliminar_empresa(ruc: str, db: Session = Depends(get_db)):
    emp = db.query(Empresa).filter(Empresa.ruc == ruc).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    item_ids = [
        r[0]
        for r in db.query(RCEPropuestaItem.id).filter(RCEPropuestaItem.ruc_empresa == ruc).all()
    ]
    if item_ids:
        db.query(CPEDetalle).filter(CPEDetalle.propuesta_item_id.in_(item_ids)).delete(synchronize_session=False)
        db.query(CPEEvidencia).filter(CPEEvidencia.propuesta_item_id.in_(item_ids)).delete(synchronize_session=False)
    db.query(RCEPropuestaItem).filter(RCEPropuestaItem.ruc_empresa == ruc).delete(synchronize_session=False)
    db.query(RCEPropuestaFile).filter(RCEPropuestaFile.ruc_empresa == ruc).delete(synchronize_session=False)
    db.query(RCERun).filter(RCERun.ruc_empresa == ruc).delete(synchronize_session=False)
    db.query(Notificacion).filter(Notificacion.ruc_empresa == ruc).delete(synchronize_session=False)
    db.query(EmpresaSire).filter(EmpresaSire.ruc_empresa == ruc).delete(synchronize_session=False)

    db.delete(emp)
    db.commit()
    return {"ok": True, "ruc": ruc}

@router.post("/{ruc}/credenciales", response_model=schemas.EmpresaCredencialesResponse)
def set_credenciales(ruc: str, payload: schemas.EmpresaCredencialesRequest, db: Session = Depends(get_db)):
    emp = db.query(Empresa).filter(Empresa.ruc == ruc).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if payload.usuario_sol is None and payload.clave_sol is None and payload.sire_client_id is None and payload.sire_client_secret is None and payload.activo is None:
        raise HTTPException(status_code=400, detail="No se enviaron credenciales para actualizar")

    if payload.usuario_sol is not None:
        emp.usuario_sol = payload.usuario_sol
    if payload.clave_sol is not None:
        emp.clave_sol = payload.clave_sol
    if payload.activo is not None:
        emp.activo = payload.activo

    sire_payload = payload.sire_client_id is not None or payload.sire_client_secret is not None
    if sire_payload:
        if not (payload.sire_client_id and payload.sire_client_secret):
            raise HTTPException(status_code=400, detail="Faltan credenciales SIRE (client_id/secret)")
        usuario = emp.usuario_sol or payload.usuario_sol
        if not usuario:
            raise HTTPException(status_code=400, detail="usuario_sol es requerido para credenciales SIRE")

        username = f"{ruc}{usuario}"
        sire = db.query(EmpresaSire).filter(EmpresaSire.ruc_empresa == ruc).first()
        if not sire:
            sire = EmpresaSire(
                ruc_empresa=ruc,
                client_id=payload.sire_client_id,
                client_secret=payload.sire_client_secret,
                username=username,
                activo=True,
            )
            db.add(sire)
        else:
            sire.client_id = payload.sire_client_id
            sire.client_secret = payload.sire_client_secret
            sire.username = username
        emp.propuesta_activa = True

    db.commit()
    return schemas.EmpresaCredencialesResponse(
        ok=True,
        ruc=ruc,
        has_sol=bool(emp.usuario_sol and emp.clave_sol),
        has_sire=bool(db.query(EmpresaSire).filter(EmpresaSire.ruc_empresa == ruc).first()),
    )


@router.patch("/{ruc}/sire", response_model=schemas.EmpresaCredencialesResponse)
def update_sire_creds(ruc: str, payload: schemas.EmpresaCredencialesRequest, db: Session = Depends(get_db)):
    """
    Actualiza credenciales SIRE y/o SOL en un solo endpoint.
    """
    return set_credenciales(ruc, payload, db)

@router.post("/import")
async def importar_empresas(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.txt') or filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Formato no soportado. Use .csv, .txt o .xlsx")
    
    content = await file.read()
    
    try:
        import pandas as pd
        import io
        
        df = None
        if filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(content))
        else:
            # CSV o TXT: Intentar motor python con sep=None para autodetección
            try:
                # Primero intentamos lectura estándar (coma)
                df = pd.read_csv(io.BytesIO(content))
                
                # Si solo detectó 1 columna, probablemente el separador falló
                if len(df.columns) < 2:
                     # Intentar autodetect
                     try:
                         stream = io.StringIO(content.decode("utf-8", errors="ignore"))
                         df = pd.read_csv(stream, sep=None, engine='python')
                     except:
                         pass
            except:
                raise Exception("Error leyendo archivo de texto/csv")

        # Normalizar columnas: 
        # 1. Strip
        # 2. Lower
        # 3. Replace spaces with underscore
        # 4. Remove accents (basic)
        def clean_col(c):
            c = str(c).strip().lower()
            c = c.replace(' ', '_').replace('.', '')
            c = c.replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ú', 'u')
            # Mapeos comunes
            if 'razon' in c and 'social' in c: return 'razon_social'
            if 'clave' in c: return 'clave_sol'
            if 'usuario' in c: return 'usuario_sol'
            return c

        df.columns = [clean_col(c) for c in df.columns]
        
        found_cols = list(df.columns)
        # Validar si RUC existe
        if 'ruc' not in found_cols:
             raise Exception(f"No se encontró la columna RUC. Columnas detectadas: {found_cols}")
        
        required_cols = ['ruc', 'razon_social', 'usuario_sol', 'clave_sol']
        # Verificar que existan al menos RUC y RAZON SOCIAL o similar?
        # El requerimiento dice "si las columnas se mantengan con ese nombre"
        
        count_ok = 0
        errors = []
        
        # Rellenar NaN con None o string vacio
        df = df.fillna('')
        
        for index, row in df.iterrows():
            try:
                ruc = str(row.get('ruc', '')).strip()
                if not ruc: continue
                
                # Limpiar ruc de posibles '.0' si vino de excel como numero
                if ruc.endswith('.0'): ruc = ruc[:-2]
                
                # Validación de longitud de RUC (Max 11 caracteres)
                if len(ruc) > 11:
                    errors.append(f"Fila {index}: RUC demasiado largo ({ruc}). Se requiere max 11.")
                    continue
                
                razon = str(row.get('razon_social', '')).strip()
                user = str(row.get('usuario_sol', '')).strip()
                clave = str(row.get('clave_sol', '')).strip()
                
                existing = db.query(Empresa).filter(Empresa.ruc == ruc).first()
                if existing:
                    if razon: existing.razon_social = razon
                    if user: existing.usuario_sol = user
                    if clave: existing.clave_sol = clave
                else:
                    new_emp = Empresa(
                        ruc=ruc,
                        razon_social=razon if razon else 'Sin Nombre',
                        usuario_sol=user,
                        clave_sol=clave
                    )
                    db.add(new_emp)
                count_ok += 1
            except Exception as e:
                errors.append(f"Fila {index}: {str(e)}")
                
        db.commit()
        return {"message": f"Procesados {count_ok} registros", "errors": errors}

    except ImportError:
        raise HTTPException(status_code=500, detail="Librería pandas/openpyxl no instalada en el servidor.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando archivo: {str(e)}")
