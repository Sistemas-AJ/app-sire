from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, date

class EmpresaBase(BaseModel):
    ruc: str
    razon_social: str
    usuario_sol: Optional[str] = None
    clave_sol: Optional[str] = None
    activo: bool = True
    propuesta_activa: bool = False

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaUpdate(BaseModel):
    razon_social: Optional[str] = None
    usuario_sol: Optional[str] = None
    clave_sol: Optional[str] = None
    activo: Optional[bool] = None

class EmpresaResponse(EmpresaBase):
    estado_sesion: str
    ultima_revision: Optional[datetime]
    last_run_status: str
    last_run_at: Optional[datetime]
    last_run_error: Optional[str]

    class Config:
        orm_mode = True

class EmpresaCredencialesRequest(BaseModel):
    usuario_sol: Optional[str] = None
    clave_sol: Optional[str] = None
    sire_client_id: Optional[str] = None
    sire_client_secret: Optional[str] = None
    activo: Optional[bool] = None

class EmpresaCredencialesResponse(BaseModel):
    ok: bool
    ruc: str
    has_sol: bool
    has_sire: bool

class PropuestaRunRequest(BaseModel):
    periodo: str
    fec_ini: str
    fec_fin: str
    ruc: Optional[str] = None
    rucs: Optional[List[str]] = None

class PropuestaRunItem(BaseModel):
    ruc: str
    periodo: str
    ticket: Optional[str] = None
    csv: Optional[str] = None
    xlsx: Optional[str] = None
    zip: Optional[str] = None

class PropuestaRunResponse(BaseModel):
    ok: bool
    results: List[PropuestaRunItem] = []
    errors: List[str] = []

class PropuestaFileResponse(BaseModel):
    ruc_empresa: str
    periodo: str
    num_ticket: Optional[str] = None
    cod_proceso: Optional[str] = None
    storage_path: str
    filename: Optional[str] = None
    sha256: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class PropuestaItemResponse(BaseModel):
    id: int
    ruc_empresa: str
    periodo: str
    tipo_cp: str
    serie: str
    numero: str
    ruc_emisor: str
    razon_emisor: Optional[str] = None
    fecha_emision: date
    total_cp: Optional[float] = None
    moneda: Optional[str] = None

    class Config:
        orm_mode = True

class XMLRunRequest(BaseModel):
    periodo: str
    ruc: Optional[str] = None
    rucs: Optional[List[str]] = None
    limit: Optional[int] = None
    headless: bool = True

class XMLRunResponse(BaseModel):
    ok: bool
    processed_rucs: List[str] = []
    errors: List[str] = []

class XMLProgressResponse(BaseModel):
    ruc: str
    periodo: str
    total_items: int
    total_evidencias: int
    ok: int
    error: int
    not_found: int
    auth: int
    pending: int
    remaining: int

class EvidenciaResponse(BaseModel):
    propuesta_item_id: int
    tipo: str
    status: str
    storage_path: Optional[str] = None
    sha256: Optional[str] = None
    error_message: Optional[str] = None
    attempt_count: int
    last_attempt_at: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DetalleResponse(BaseModel):
    propuesta_item_id: int
    extractor_version: str
    detalle_json: Any
    source_sha256: Optional[str] = None
    extracted_at: datetime

    class Config:
        orm_mode = True

class AutomationRunRequest(BaseModel):
    mode: str = "todo" # 'todo' | 'solo_fallidos'
    days_back: int = 7
    show_browser: bool = True # Nuevo param
