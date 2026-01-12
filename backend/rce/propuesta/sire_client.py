import time
import requests
from typing import Dict, Any, Tuple

API_BASE = "https://api-sire.sunat.gob.pe"
HTTP_TIMEOUT = 30
POLL_SECONDS = 3
POLL_TIMEOUT_SECONDS = 180

class SireApiError(RuntimeError):
    pass

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
        raise SireApiError(f"generar_ticket {r.status_code}: {r.text[:300]}")
    j = r.json()
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
        raise SireApiError(f"estado_ticket {r.status_code}: {r.text[:300]}")
    return r.json()

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
        raise SireApiError(f"descarga {r.status_code}: {r.text[:300]}")
    return r.content
