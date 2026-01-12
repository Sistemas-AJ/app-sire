from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmpresaBase(BaseModel):
    ruc: str
    razon_social: str
    usuario_sol: Optional[str] = None
    clave_sol: Optional[str] = None
    activo: bool = True

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaResponse(EmpresaBase):
    estado_sesion: str
    ultima_revision: Optional[datetime]
    last_run_status: str
    last_run_at: Optional[datetime]
    last_run_error: Optional[str]

    class Config:
        orm_mode = True

class AutomationRunRequest(BaseModel):
    mode: str = "todo" # 'todo' | 'solo_fallidos'
    days_back: int = 7
    show_browser: bool = True # Nuevo param
