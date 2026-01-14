# backend/rce/sol/consulta_individual.py
import os
import re
import zipfile
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Page

@dataclass(frozen=True)
class CredencialesSOL:
    ruc: str
    usuario: str
    clave_sol: str

@dataclass(frozen=True)
class BusquedaComprobante:
    ruc_emisor: str
    serie: str
    numero: str
    tipo_label: str = "Factura"  # lo que aparece en el dropdown (PrimeNG)

@dataclass(frozen=True)
class DescargaResult:
    ok: bool
    xml_path: Optional[str] = None
    error: Optional[str] = None


def _guardar_y_extraer_zip(download, out_dir: str, final_xml_name: str) -> str:
    """
    Guarda el zip descargado y extrae el XML.
    Devuelve path final del XML.
    """
    os.makedirs(out_dir, exist_ok=True)

    temp_zip_path = os.path.join(out_dir, "temp_sunat_download.zip")
    final_xml_path = os.path.join(out_dir, final_xml_name)

    download.save_as(temp_zip_path)

    try:
        with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
            archivos_internos = zip_ref.namelist()
            if not archivos_internos:
                raise RuntimeError("El ZIP descargado estaba vacío.")

            # Preferir el primer .xml; si no, el primero que haya
            xml_candidates = [n for n in archivos_internos if n.lower().endswith(".xml")]
            nombre_archivo_original = xml_candidates[0] if xml_candidates else archivos_internos[0]

            zip_ref.extract(nombre_archivo_original, out_dir)

            origen = os.path.join(out_dir, nombre_archivo_original)
            # si viene dentro de carpeta, origen puede no existir directo; arma path correcto:
            origen = os.path.join(out_dir, *nombre_archivo_original.split("/"))

            os.replace(origen, final_xml_path)

        return final_xml_path
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)


def consultar_y_descargar_xml_individual(
    page: Page,
    busqueda: BusquedaComprobante,
    out_dir: str,
    iframe_selector: str = "#iframeApplication",
    timeout_resultado_ms: int = 45000,
) -> DescargaResult:
    """
    Asume que ya estás logueado y en la pantalla 'Nueva Consulta de comprobantes de pago'.
    Entra al iframe, llena campos y descarga el XML.
    """
    try:
        frame = page.frame_locator(iframe_selector)

        # Espera el componente angular
        frame.locator("consulta-comprobante-individual").wait_for(state="visible", timeout=15000)

        print("📝 Llenando datos del comprobante...")

        # Recibido
        print("  🔘 Seleccionando 'Recibido'...")
        frame.locator("label[for='recibido']").click()
        page.wait_for_timeout(1000)

        # RUC emisor
        print(f"  🆔 RUC Emisor: {busqueda.ruc_emisor}")
        frame.locator("input[name='rucEmisor']").fill(busqueda.ruc_emisor)

        # Tipo comprobante (PrimeNG)
        print(f"  🔽 Seleccionando tipo: {busqueda.tipo_label}")
        dropdown = frame.locator("p-dropdown[formcontrolname='tipoComprobanteI']")
        dropdown.click()

        frame.locator(".p-dropdown-item").get_by_text(
            re.compile(rf"^{re.escape(busqueda.tipo_label)}$"),
            exact=True
        ).click()

        # Serie y número
        print(f"  🔢 Serie: {busqueda.serie} | Número: {busqueda.numero}")
        frame.locator("input[name='serieComprobante']").fill(busqueda.serie)
        frame.locator("input[name='numeroComprobante']").fill(busqueda.numero)

        # Consultar
        print("🔍 Ejecutando consulta...")
        frame.locator("button:has-text('Consultar')").click()

        # Esperar resultado (botonera)
        print("📥 Esperando resultados...")
        button_container = frame.locator(".button-container")
        button_container.wait_for(state="visible", timeout=timeout_resultado_ms)

        # Descargar XML (preferente)
        print("  🖱️ Localizando botón XML por tooltip...")
        btn_xml = frame.locator("button[ngbtooltip='Descargar XML']")
        btn_xml.wait_for(state="visible", timeout=5000)

        print("  📥 Iniciando descarga del XML...")
        with page.expect_download() as download_info:
            btn_xml.click()

        download = download_info.value

        final_name = f"{busqueda.ruc_emisor}_{busqueda.serie}_{busqueda.numero}.xml"
        xml_path = _guardar_y_extraer_zip(download, out_dir=out_dir, final_xml_name=final_name)
        try:
            close_btn = frame.locator("button.close-without-header, button[aria-label='Close'].close-without-header")
            close_btn.wait_for(state="visible", timeout=3000)
            close_btn.click()
            page.wait_for_timeout(500)
        except Exception:
            # Si no está (o cambió), no bloqueamos el job
            pass

        print(f"✅ XML guardado en: {xml_path}")
        return DescargaResult(ok=True, xml_path=xml_path)

    except Exception as e:
        return DescargaResult(ok=False, error=str(e))
