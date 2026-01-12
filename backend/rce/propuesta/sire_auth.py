import requests
from datetime import datetime, timedelta, timezone
from typing import Tuple

class SireAuthError(RuntimeError):
    pass


def get_token_sire(
    client_id: str,
    client_secret: str,
    ruc: str,
    usuario_sol: str,
    clave_sol: str,
    scope: str = "https://api-sire.sunat.gob.pe",
    grant_type: str = "password",
    timeout: int = 30,
) -> Tuple[str, str]:
    """
    Retorna:
      - access_token (SIN 'Bearer')
      - expires_at ISO UTC
    """
    if not client_id or not client_secret:
        raise SireAuthError("Falta client_id/client_secret")
    if not ruc or not usuario_sol or not clave_sol:
        raise SireAuthError("Falta ruc/usuario_sol/clave_sol")

    token_url = f"https://api-seguridad.sunat.gob.pe/v1/clientessol/{client_id}/oauth2/token/"

    data = {
        "grant_type": grant_type,
        "scope": scope,
        "client_id": client_id,
        "client_secret": client_secret,
        "username": f"{ruc}{usuario_sol}",  # OJO: con espacio
        "password": clave_sol,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    r = requests.post(token_url, data=data, headers=headers, timeout=timeout)
    if r.status_code >= 400:
        raise SireAuthError(f"Token error {r.status_code}: {r.text[:500]}")

    j = r.json()
    access_token = j.get("access_token")
    expires_in = j.get("expires_in", 3000)

    if not access_token:
        raise SireAuthError(f"Respuesta sin access_token: {j}")

    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))).isoformat()
    return access_token, expires_at
