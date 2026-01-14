import os

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_REGISTROS = os.path.join(_BASE_DIR, "data", "registros")
REGISTROS_DIR = os.getenv("SIRE_REGISTROS_DIR", _DEFAULT_REGISTROS)

MENU_RUTA_CONSULTA = [
    "Comprobantes de pago",
    "Comprobantes de Pago",
    "Consulta de Comprobantes de Pago",
    "Nueva Consulta de comprobantes de pago",
]

# timeouts
TIMEOUT_ANGULAR_MS = 15000
TIMEOUT_RESULTADO_MS = 15000          # rápido para “si SUNAT cuelga, saltar”
TIMEOUT_XML_BUTTON_MS = 2000          # si no aparece, asumimos colgado o sin resultado
WAIT_ON_FAIL_SECONDS = 10             # tu regla: espera 10s y sigue

# retries por comprobante (además de esperar 10s)
MAX_ATTEMPTS_PER_ITEM = 2

# modo navegador
DEFAULT_HEADLESS = True
