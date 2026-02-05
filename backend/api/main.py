from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db
from core.config import init_dirs
from api.routers import empresas, automatizacion, dashboard, files, propuesta, xml_service, auth

app = FastAPI(title="SUNAT Automation API de Buzones SOL", version="1.0.0")

# CORS (Permitir frontend local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar DB al arranque (opcional, mejor usar migraciones reales como Alembic)
@app.on_event("startup")
def startup_event():
    init_db() # Crea tablas si no existen
    init_dirs()

# Routers
app.include_router(empresas.router)
app.include_router(automatizacion.router)
app.include_router(dashboard.router)
app.include_router(files.router)
app.include_router(propuesta.router)
app.include_router(xml_service.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "SUNAT Automation API is running 🚀"}
