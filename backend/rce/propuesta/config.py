import os

API_BASE = os.getenv("SIRE_API_BASE", "https://api-sire.sunat.gob.pe")

# dónde guardas cache de tokens/tickets
SESSIONS_DIR = os.getenv("SIRE_SESSIONS_DIR", "/app/sessions_propuesta")

# dónde guardas resultados
REGISTROS_DIR = os.getenv("SIRE_REGISTROS_DIR", "/app/registros")

# polling
POLL_SECONDS = int(os.getenv("SIRE_POLL_SECONDS", "3"))
POLL_TIMEOUT_SECONDS = int(os.getenv("SIRE_POLL_TIMEOUT_SECONDS", "180"))

# timeouts HTTP
HTTP_TIMEOUT = int(os.getenv("SIRE_HTTP_TIMEOUT", "30"))

# endpoint de token (ajústalo a tu realidad)
TOKEN_URL = os.getenv("SIRE_TOKEN_URL", "")  # <- tú lo defines
