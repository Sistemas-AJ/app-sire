import os

# --- CONFIGURACIÓN ---
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SESSION_DIR = os.getenv("SESSION_DIR", os.path.join(_BASE_DIR, "sessions"))
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(_BASE_DIR, "debug"))
URL_MENU = "https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm"

def init_dirs():
    """Crea los directorios necesarios si no existen."""
    os.makedirs(SESSION_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)
