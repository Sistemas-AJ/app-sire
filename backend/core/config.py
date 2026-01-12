import os

# --- CONFIGURACIÓN ---
SESSION_DIR = "./sessions"
DEBUG_DIR = "./debug"
URL_MENU = "https://e-menu.sunat.gob.pe/cl-ti-itmenu/MenuInternet.htm"

def init_dirs():
    """Crea los directorios necesarios si no existen."""
    os.makedirs(SESSION_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)
