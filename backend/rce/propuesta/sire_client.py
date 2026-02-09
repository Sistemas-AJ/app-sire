import time
import requests
from typing import Dict, Any, Tuple

API_BASE = "https://api-sire.sunat.gob.pe"
HTTP_TIMEOUT = 30
POLL_SECONDS = 3
POLL_TIMEOUT_SECONDS = 180

class SireApiError(RuntimeError):
    pass


def _safe_json(r: requests.Response, context: str) -> Dict[str, Any]:
    try:
        return r.json()
    except ValueError as e:
        body = (r.text or "")[:300]
        raise SireApiError(f"{context}: respuesta JSON inválida de SUNAT ({e}). body={body}")


def _normalize_http_error(r: requests.Response, context: str) -> str:
    body = (r.text or "")[:500]
    try:
        j = r.json()
    except ValueError:
        return f"{context} {r.status_code}: {body}"

    # Caso negocio conocido: no hay comprobantes en el periodo consultado.
    if r.status_code == 422:
        for err in (j.get("errors") or []):
            if str(err.get("cod")) == "1070":
                return "CSV vacío o sin encabezados (sin compras en el periodo)."

    msg = j.get("msg") or j.get("message") or j.get("error_description") or j.get("error")
    if msg:
        return f"{context} {r.status_code}: {msg}"
    return f"{context} {r.status_code}: {body}"

def auth_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

def generar_ticket_exportacion_propuesta(
    token: str,
    per: str,
    fec_ini: str,
    fec_fin: str,
    codTipoArchivo: str = "1",
    codOrigenEnvio: str = "2",
    codTipoCDP: str = "01",
) -> str:
    url = f"{API_BASE}/v1/contribuyente/migeigv/libros/rce/propuesta/web/propuesta/{per}/exportacioncomprobantepropuesta"
    params = {
        "codTipoArchivo": codTipoArchivo,
        "codOrigenEnvio": codOrigenEnvio,
        "fecEmisionIni": fec_ini,
        "fecEmisionFin": fec_fin,
        
    }
    r = requests.get(url, headers=auth_headers(token), params=params, timeout=HTTP_TIMEOUT)
    if r.status_code >= 400:
        raise SireApiError(_normalize_http_error(r, "generar_ticket"))
    j = _safe_json(r, "generar_ticket")
    t = j.get("numTicket")
    if not t:
        raise SireApiError(f"Respuesta sin numTicket: {j}")
    return t

def consultar_estado_ticket(token: str, per: str, numTicket: str) -> Dict[str, Any]:
    url = f"{API_BASE}/v1/contribuyente/migeigv/libros/rvierce/gestionprocesosmasivos/web/masivo/consultaestadotickets"
    params = {
        "perIni": per,
        "perFin": per,
        "page": 1,
        "perPage": 40,
        "numTicket": numTicket,
    }
    r = requests.get(url, headers=auth_headers(token), params=params, timeout=HTTP_TIMEOUT)
    if r.status_code >= 400:
        raise SireApiError(_normalize_http_error(r, "estado_ticket"))
    return _safe_json(r, "estado_ticket")

def esperar_hasta_terminado(token: str, per: str, numTicket: str) -> Dict[str, Any]:
    t0 = time.time()
    while True:
        st = consultar_estado_ticket(token, per, numTicket)
        regs = st.get("registros") or []
        if regs:
            reg0 = regs[0]
            if reg0.get("codEstadoProceso") == "06" or (reg0.get("desEstadoProceso") or "").lower() == "terminado":
                return reg0

        if time.time() - t0 > POLL_TIMEOUT_SECONDS:
            raise SireApiError(f"Timeout esperando ticket {numTicket} periodo {per}")
        time.sleep(POLL_SECONDS)

def extraer_params_descarga(registro_ticket: Dict[str, Any]) -> Tuple[str, str, str]:
    cod_proceso = str(registro_ticket.get("codProceso") or "")
    arr = registro_ticket.get("archivoReporte") or []
    if not arr:
        raise SireApiError("No hay archivoReporte en el estado del ticket.")
    a0 = arr[0]
    nom = a0.get("nomArchivoReporte")
    cod_tipo = a0.get("codTipoAchivoReporte") or a0.get("codTipoArchivoReporte")
    if not nom or cod_tipo is None:
        raise SireApiError(f"archivoReporte incompleto: {a0}")
    return nom, str(cod_tipo), cod_proceso

def descargar_archivo_reporte(
    token: str,
    per: str,
    numTicket: str,
    codProceso: str,
    nomArchivoReporte: str,
    codTipoArchivoReporte: str,
    codLibro: str = "080000",
) -> bytes:
    url = f"{API_BASE}/v1/contribuyente/migeigv/libros/rvierce/gestionprocesosmasivos/web/masivo/archivoreporte"
    params = {
        "nomArchivoReporte": nomArchivoReporte,
        "codTipoArchivoReporte": codTipoArchivoReporte,
        "perTributario": per,
        "codProceso": codProceso,
        "numTicket": numTicket,
        "codLibro": codLibro,
    }
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=HTTP_TIMEOUT)
    if r.status_code >= 400:
        raise SireApiError(_normalize_http_error(r, "descarga"))
    return r.content
