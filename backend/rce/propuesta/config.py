import os

API_BASE = os.getenv("SIRE_API_BASE", "https://api-sire.sunat.gob.pe")

# dónde guardas cache de tokens/tickets
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_SESSIONS = os.path.join(_BASE_DIR, "data", "sessions_propuesta")
_DEFAULT_REGISTROS = os.path.join(_BASE_DIR, "data", "registros")
SESSIONS_DIR = os.getenv("SIRE_SESSIONS_DIR", _DEFAULT_SESSIONS)

# dónde guardas resultados
REGISTROS_DIR = os.getenv("SIRE_REGISTROS_DIR", _DEFAULT_REGISTROS)

# polling
POLL_SECONDS = int(os.getenv("SIRE_POLL_SECONDS", "3"))
POLL_TIMEOUT_SECONDS = int(os.getenv("SIRE_POLL_TIMEOUT_SECONDS", "180"))

# timeouts HTTP
HTTP_TIMEOUT = int(os.getenv("SIRE_HTTP_TIMEOUT", "30"))

# endpoint de token (ajústalo a tu realidad)
TOKEN_URL = os.getenv("SIRE_TOKEN_URL", "")  # <- tú lo defines
