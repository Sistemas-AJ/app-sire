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

class PropuestaAvailabilityResponse(BaseModel):
    periodo: str
    available_rucs: List[str]
    message: str

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

class XMLStopRequest(BaseModel):
    ruc: Optional[str] = None
    periodo: Optional[str] = None

class XMLStopResponse(BaseModel):
    ok: bool
    message: str

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

class XMLProgressGlobalResponse(BaseModel):
    periodo: str
    total_empresas: int
    total_items: int
    total_evidencias: int
    ok: int
    error: int
    not_found: int
    auth: int
    pending: int
    remaining: int

class XMLReportItemResponse(BaseModel):
    item_id: int
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
    status: str
    storage_path: Optional[str] = None
    error_message: Optional[str] = None
    detalle_json: Optional[Any] = None

class XMLReportResponse(BaseModel):
    ruc: str
    periodo: str
    total_items: int
    ok: int
    error: int
    not_found: int
    auth: int
    pending: int
    items: List[XMLReportItemResponse]

class XMLReportExportResponse(BaseModel):
    ruc: str
    periodo: str
    path: str
    rows: int
    message: str

class XMLRunStatusResponse(BaseModel):
    id: int
    ruc_empresa: str
    periodo: str
    modulo: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    stats_json: Optional[Any] = None

    class Config:
        orm_mode = True

class XMLRepositoryItemResponse(BaseModel):
    id: int
    ruc_empresa: str
    razon_social_empresa: Optional[str] = None
    ruc_emisor: str
    razon_social_emisor: Optional[str] = None
    tipo_comprobante: str
    serie: str
    numero: str
    fecha_emision: date
    moneda: Optional[str] = None
    total: Optional[float] = None
    status_xml: str
    xml_path: Optional[str] = None
    error_message: Optional[str] = None

class XMLRepositoryResponse(BaseModel):
    total: int
    page: int
    pages: int
    items: List[XMLRepositoryItemResponse]

class XMLRetryResponse(BaseModel):
    ok: bool
    item_id: int
    message: str

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
    mode: str = "todo" # todo | pendientes | solo_fallidos
    days_back: Optional[int] = 7
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    rucs: Optional[List[str]] = None
    show_browser: bool = True # Nuevo param

class BuzonRunItem(BaseModel):
    id: int
    ruc_empresa: str
    fecha_desde: date
    fecha_hasta: Optional[date] = None
    status: str
    retry_mode: Optional[str] = None
    headless: bool
    stop_requested: bool
    stats_json: Optional[Any] = None
    last_error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class BuzonRunResponse(BaseModel):
    ok: bool
    runs: List[BuzonRunItem] = []
    errors: List[str] = []
