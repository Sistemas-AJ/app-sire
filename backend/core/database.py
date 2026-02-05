from sqlalchemy import (
    Column, String, Integer, Boolean, Date, DateTime, Numeric, Text,
    ForeignKey, UniqueConstraint, Index, JSON, create_engine
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from contextlib import contextmanager
from sqlalchemy.sql import func
from datetime import datetime
import os

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Usuario: Lopez, Pass: Lopez, BD: pgsunat
# Dentro de Docker usamos el servicio "postgres:5432"; desde host/WSL usamos "localhost:5434".
if "DATABASE_URL" in os.environ:
    DATABASE_URL = os.environ["DATABASE_URL"]
else:
    in_docker = os.path.exists("/.dockerenv")
    default_host = "postgres" if in_docker else "localhost"
    default_port = "5432" if in_docker else "5434"
    DATABASE_URL = f"postgresql+psycopg2://Lopez:Lopez@{default_host}:{default_port}/pgsunat"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DEFINICIÓN DE MODELOS (TABLAS) ---

class Empresa(Base):
    __tablename__ = 'empresas'

    ruc = Column(String(11), primary_key=True, index=True)
    razon_social = Column(String(200), nullable=False)
    usuario_sol = Column(String(50), nullable=True) # Opcional si login es manual
    clave_sol = Column(String(50), nullable=True)   # Opcional
    # Estado de la sesión guardada en JSON: 'OK', 'EXPIRED', 'ERROR'
    estado_sesion = Column(String(20), default='EXPIRED') 
    activo = Column(Boolean, default=True)
    # Indica si tiene credenciales SIRE registradas para propuestas
    propuesta_activa = Column(Boolean, default=False)
    ultima_revision = Column(DateTime, nullable=True)

    # Estado de la última ejecución del script (Fase 1)
    # Valores: 'PENDIENTE', 'COMPLETADO', 'SIN_NOVEDADES', 'ERROR', 'INCOMPLETO'
    last_run_status = Column(String(20), default='PENDIENTE')
    last_run_at = Column(DateTime, nullable=True)
    last_run_error = Column(Text, nullable=True) # Para guardar el error de la última ejecución
    
    # Relación con notificaciones (1 a muchos)
    notificaciones = relationship("Notificacion", back_populates="empresa")

    def __repr__(self):
        return f"<Empresa(ruc='{self.ruc}', razon='{self.razon_social}')>"


class Notificacion(Base):
    __tablename__ = 'notificaciones'

    id = Column(Integer, primary_key=True, index=True)
    ruc_empresa = Column(String(11), ForeignKey('empresas.ruc'), nullable=False)
    
    # El código que usa SUNAT internamente para identificar el msj
    codigo_notificacion = Column(String(50), nullable=False) 
    
    asunto = Column(Text, nullable=True)
    fecha_emision = Column(DateTime, nullable=True) # Fecha que dice SUNAT (Usado actualmente como TIMESTAMP)
    fecha_recibido_sunat = Column(DateTime, nullable=True) # Fecha real del documento (Scraped)
    fecha_leido = Column(DateTime, nullable=True)   # Fecha que tu sistema lo leyó
    
    # Estado según SUNAT ('0': No leido, '1': Leido) o texto
    estado_sunat = Column(String(20), nullable=True) 
    
    # Ruta donde guardaste el PDF descargado
    ruta_pdf_local = Column(Text, nullable=True)
    
    # Bandera para tu lógica interna (ej: ¿Ya avisé por Slack?)
    procesado = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa
    empresa = relationship("Empresa", back_populates="notificaciones")

    # Constraint: Evitar guardar la misma notificación dos veces para la misma empresa
    __table_args__ = (
        UniqueConstraint('ruc_empresa', 'codigo_notificacion', name='uq_notificacion_empresa'),
    )

    def __repr__(self):
        return f"<Notificacion(id={self.id}, asunto='{self.asunto[:20]}...')>"


class BuzonRun(Base):
    __tablename__ = "buzon_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc_empresa = Column(String(11), ForeignKey("empresas.ruc"), nullable=False)

    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=True)

    status = Column(String(20), nullable=False, default="PENDING")
    retry_mode = Column(String(20), nullable=True)  # todo/pendientes/solo_fallidos
    headless = Column(Boolean, default=True)
    stop_requested = Column(Boolean, default=False)
    queued = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    last_error = Column(Text, nullable=True)
    stats_json = Column(JSON, nullable=True)
    evidencia_path = Column(Text, nullable=True)

    empresa = relationship("Empresa")

    __table_args__ = (
        Index("ix_buzon_runs_ruc_fecha", "ruc_empresa", "fecha_desde"),
        Index("ix_buzon_runs_status", "status"),
    )


class RCERun(Base):
    __tablename__ = "rce_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc_empresa = Column(String(11), ForeignKey("empresas.ruc"), nullable=False)

    periodo = Column(String(6), nullable=False)  # YYYYMM
    modulo = Column(String(30), nullable=False, default="RCE")  # futuro: SOL_XML, EXTRACT, etc.
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING/RUNNING/OK/ERROR/PARTIAL

    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    stats_json = Column(JSON, nullable=True)  # {"items":29,"xml_ok":20,...}

    empresa = relationship("Empresa")  # si tienes Empresa en otro módulo

    __table_args__ = (
        Index("ix_rce_runs_ruc_periodo", "ruc_empresa", "periodo"),
    )


class RCEPropuestaFile(Base):
    __tablename__ = "rce_propuesta_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc_empresa = Column(String(11), ForeignKey("empresas.ruc"), nullable=False)
    periodo = Column(String(6), nullable=False)

    num_ticket = Column(String(20), nullable=True)
    cod_proceso = Column(String(10), nullable=True)

    storage_path = Column(Text, nullable=False)         # donde guardaste el ZIP/CSV
    filename = Column(Text, nullable=True)
    sha256 = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("ruc_empresa", "periodo", name="uq_rce_propuesta_file_ruc_periodo"),
        Index("ix_rce_propuesta_files_ruc_periodo", "ruc_empresa", "periodo"),
    )

class EmpresaSire(Base):
    __tablename__ = "empresas_sire"

    # 1 a 1 con Empresa
    ruc_empresa = Column(String(11), ForeignKey("empresas.ruc"), primary_key=True)

    client_id = Column(String(120), nullable=False)
    client_secret = Column(String(200), nullable=False)

    # username requerido por tu OAuth: "ruc + usuario_sol"
    # lo guardamos explícito para no recalcular y para auditoría
    username = Column(String(100), nullable=False)

    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    empresa = relationship("Empresa")

    __table_args__ = (
        UniqueConstraint("username", name="uq_empresas_sire_username"),
        Index("ix_empresas_sire_ruc", "ruc_empresa"),
    )

class RCEPropuestaItem(Base):
    __tablename__ = "rce_propuesta_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    ruc_empresa = Column(String(11), ForeignKey("empresas.ruc"), nullable=False)
    periodo = Column(String(6), nullable=False)  # YYYYMM

    car_sunat = Column(String(40), nullable=True)

    fecha_emision = Column(Date, nullable=False)
    fecha_vcto_pago = Column(Date, nullable=True)

    tipo_cp = Column(String(2), nullable=False)        # 01/07/08 ...
    serie = Column(String(10), nullable=False)
    numero = Column(String(20), nullable=False)

    tipo_doc_identidad = Column(String(2), nullable=True)
    ruc_emisor = Column(String(11), nullable=False)
    razon_emisor = Column(String(200), nullable=True)

    bi_gravado_dg = Column(Numeric(18, 2), nullable=True)
    igv_dg = Column(Numeric(18, 2), nullable=True)
    bi_gravado_dgng = Column(Numeric(18, 2), nullable=True)
    igv_dgng = Column(Numeric(18, 2), nullable=True)
    bi_gravado_dng = Column(Numeric(18, 2), nullable=True)
    igv_dng = Column(Numeric(18, 2), nullable=True)
    valor_adq_ng = Column(Numeric(18, 2), nullable=True)
    isc = Column(Numeric(18, 2), nullable=True)
    icbper = Column(Numeric(18, 2), nullable=True)
    otros_trib = Column(Numeric(18, 2), nullable=True)
    total_cp = Column(Numeric(18, 2), nullable=False)

    moneda = Column(String(3), nullable=False)
    tipo_cambio = Column(Numeric(18, 6), nullable=True)

    detraccion = Column(String(5), nullable=True)
    est_comp = Column(String(10), nullable=True)
    incal = Column(String(10), nullable=True)
    clasif_bss_sss = Column(String(50), nullable=True)

    raw_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones (para no duplicar datos en evidencias/detalle)
    evidencias = relationship("CPEEvidencia", back_populates="propuesta_item", cascade="all, delete-orphan")
    detalle = relationship("CPEDetalle", back_populates="propuesta_item", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint(
            "ruc_empresa", "periodo", "ruc_emisor", "tipo_cp", "serie", "numero", "fecha_emision",
            name="uq_rce_item_key"
        ),
        Index("ix_rce_items_lookup", "ruc_empresa", "periodo", "ruc_emisor", "tipo_cp", "serie", "numero"),
        Index("ix_rce_items_periodo", "ruc_empresa", "periodo"),
    )


class CPEEvidencia(Base):
    """
    Solo estado/evidencia (XML/PDF/TXT) para un item de propuesta.
    No duplica ruc_emisor/tipo/serie/numero porque todo eso vive en rce_propuesta_items.
    """
    __tablename__ = "cpe_evidencias"

    id = Column(Integer, primary_key=True, autoincrement=True)

    propuesta_item_id = Column(Integer, ForeignKey("rce_propuesta_items.id", ondelete="CASCADE"), nullable=False)

    tipo = Column(String(5), nullable=False)  # XML/PDF/TXT
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING/OK/ERROR/NOT_FOUND/AUTH/CAPTCHA

    storage_path = Column(Text, nullable=True)
    sha256 = Column(String(64), nullable=True)

    error_message = Column(Text, nullable=True)

    # Operación / reintentos
    attempt_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    downloaded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    propuesta_item = relationship("RCEPropuestaItem", back_populates="evidencias")

    __table_args__ = (
        UniqueConstraint("propuesta_item_id", "tipo", name="uq_cpe_evidencia_item_tipo"),
        Index("ix_cpe_evidencias_status", "status"),
        Index("ix_cpe_evidencias_tipo_status", "tipo", "status"),
        Index("ix_cpe_evidencias_retry", "next_retry_at"),
        Index("ix_cpe_evidencias_item", "propuesta_item_id"),
    )


class CPEDetalle(Base):
    """
    Resultado de extracción del XML (líneas/impuestos) + reglas contables.
    También referenciado al item de propuesta.
    """
    __tablename__ = "cpe_detalle"

    id = Column(Integer, primary_key=True, autoincrement=True)

    propuesta_item_id = Column(Integer, ForeignKey("rce_propuesta_items.id", ondelete="CASCADE"), nullable=False)

    extracted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    extractor_version = Column(String(20), nullable=False, default="v1")

    detalle_json = Column(JSON, nullable=False)
    reglas_json = Column(JSON, nullable=True)

    # opcional pero muy útil para auditoría: hash del XML usado para extraer
    source_sha256 = Column(String(64), nullable=True)

    propuesta_item = relationship("RCEPropuestaItem", back_populates="detalle")

    __table_args__ = (
        UniqueConstraint("propuesta_item_id", "extractor_version", name="uq_cpe_detalle_item_version"),
        Index("ix_cpe_detalle_item", "propuesta_item_id"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)

    user = relationship("User")
# --- FUNCIÓN DE INICIALIZACIÓN ---

def init_db():
    """
    Crea las tablas si no existen.
    No sobrescribe datos existentes.
    """
    print("🔄 Conectando a PostgreSQL y verificando tablas...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas verificadas/creadas exitosamente.")
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")

# --- UTILIDAD PARA OBTENER SESIÓN ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    # Si ejecutas este archivo directo, inicializa la BD
    init_db()
