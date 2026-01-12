from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Usuario: Lopez, Pass: Lopez, Host: localhost (tu máquina), Puerto: 5434 (mapeado en Docker), BD: pgsunat
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://Lopez:Lopez@postgres:5432/pgsunat"
)

engine = create_engine(DATABASE_URL, echo=False)
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

if __name__ == "__main__":
    # Si ejecutas este archivo directo, inicializa la BD
    init_db()