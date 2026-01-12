import os
import time
import re
import zipfile
import shutil

from playwright.sync_api import sync_playwright
from core.config import init_dirs
from automation.auth import intentar_login_automatico, handle_post_login_popups
from automation.utils import goto_menu, buscar_y_clickear, get_buzon_frame


# --- DATOS PROPORCIONADOS ---
CREDENTIALS = {
    "ruc": "20529929821",
    "usuario": "TIERTHRI",
    "clave_sol": "ophicanas"
}

BUSQUEDA = {
    "ruc_emisor": "20526422300",
    "serie": "F001",
    "numero": "100286"
}

def navegar_menu_jerarquico(page, ruta_menus):
    print(f"📂 Iniciando navegación de ruta: {' > '.join(ruta_menus)}")
    for i, menu_texto in enumerate(ruta_menus):
        # Usamos ignore_case=True para ser más flexibles con SUNAT
        selector_actual = page.locator("span.spanNivelDescripcion").get_by_text(menu_texto, exact=True).filter(visible=True).first
        
        if i + 1 < len(ruta_menus):
            siguiente_texto = ruta_menus[i+1]
            siguiente_visible = page.locator("span.spanNivelDescripcion").get_by_text(siguiente_texto, exact=True).filter(visible=True).count()
            if siguiente_visible > 0:
                print(f"  ⏭️ Saltando '{menu_texto}': Ya está expandido.")
                continue

        print(f"  👆 Click en '{menu_texto}'")
        selector_actual.wait_for(state="visible", timeout=10000)
        selector_actual.click()
        page.wait_for_timeout(1500)

def descargar_factura_individual():
    init_dirs()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()

        try:
            print("🚀 Iniciando sesión...")
            if not goto_menu(page): return

            class MockEmp:
                ruc = CREDENTIALS["ruc"]
                usuario_sol = CREDENTIALS["usuario"]
                clave_sol = CREDENTIALS["clave_sol"]

            if not intentar_login_automatico(page, MockEmp()):
                print("❌ Error en Login.")
                return
            
            handle_post_login_popups(page)

            # --- NAVEGACIÓN ---
            print("📂 Navegando a Consulta de Factura Individual...")
            menus = [
                "Comprobantes de pago", 
                "Comprobantes de Pago", 
                "Consulta de Comprobantes de Pago", 
                "Nueva Consulta de comprobantes de pago"
            ]
            navegar_menu_jerarquico(page, menus)

            # --- ENTRADA AL IFRAME ---
            print("⏳ Accediendo al formulario (Angular Iframe)...")
            # Usamos frame_locator para mayor estabilidad con Angular
            frame = page.frame_locator("#iframeApplication")
            
            # Esperar a que el contenedor principal de la consulta aparezca
            frame.locator("consulta-comprobante-individual").wait_for(state="visible", timeout=15000)

            print("📝 Llenando datos del comprobante...")

            # 1. Marcar 'Recibido' (Click en el label porque el input suele estar oculto)
            print("  🔘 Seleccionando 'Recibido'...")
            frame.locator("label[for='recibido']").click()
            page.wait_for_timeout(1000) # Esperar habilitación de campos

            # 2. RUC Emisor
            print(f"  🆔 RUC Emisor: {BUSQUEDA['ruc_emisor']}")
            frame.locator("input[name='rucEmisor']").fill(BUSQUEDA["ruc_emisor"])

            # 3. Tipo de Comprobante (PrimeNG Dropdown)
            print("  🔽 Seleccionando tipo: FACTURA")
            dropdown = frame.locator("p-dropdown[formcontrolname='tipoComprobanteI']")
            dropdown.click()
            
            # SOLUCIÓN AL STRICT MODE: 
            # Buscamos el elemento que contenga EXACTAMENTE "Factura"
            frame.locator(".p-dropdown-item").get_by_text(re.compile(r"^Factura$"), exact=True).click()

            # 4. Serie y Número
            print(f"  🔢 Serie: {BUSQUEDA['serie']} | Número: {BUSQUEDA['numero']}")
            frame.locator("input[name='serieComprobante']").fill(BUSQUEDA["serie"])
            frame.locator("input[name='numeroComprobante']").fill(BUSQUEDA["numero"])

            # 5. Consultar
            print("🔍 Ejecutando consulta...")
            frame.locator("button:has-text('Consultar')").click()

            # --- DESCARGA ---
            # --- DESCARGA ---
            print("📥 Esperando que aparezcan los resultados...")
            
            # 1. Esperamos a que el contenedor de botones sea visible
            button_container = frame.locator(".button-container")
            button_container.wait_for(state="visible", timeout=45000)

            try:
                # 2. Localizamos el botón específicamente por su tooltip de Angular
                print("  🖱️ Localizando botón XML por tooltip...")
                btn_xml = frame.locator("button[ngbtooltip='Descargar XML']")
                
                # Aseguramos que sea visible antes de intentar el click
                btn_xml.wait_for(state="visible", timeout=5000)

                # 3. Protocolo de descarga
                print("  📥 Iniciando descarga del XML...")
                with page.expect_download() as download_info:
                    btn_xml.click()
                
                print("📥 Descargando archivo comprimido...")
                download = download_info.value
                
                # 1. Definimos rutas temporales y finales
                temp_zip_path = os.path.join(os.getcwd(), "temp_sunat_download.zip")
                final_xml_name = f"{BUSQUEDA['ruc_emisor']}_{BUSQUEDA['serie']}_{BUSQUEDA['numero']}.xml"
                final_xml_path = os.path.join(os.getcwd(), final_xml_name)

                # 2. Guardamos el ZIP físicamente
                download.save_as(temp_zip_path)

                # 3. Procesamos el ZIP
                try:
                    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                        # Obtenemos la lista de archivos dentro del zip
                        archivos_internos = zip_ref.namelist()
                        
                        if archivos_internos:
                            # Extraemos el primer archivo (el XML)
                            nombre_archivo_original = archivos_internos[0]
                            zip_ref.extract(nombre_archivo_original, os.getcwd())
                            
                            # 4. Renombramos al nombre estándar que tú definiste
                            # (A veces SUNAT le pone nombres larguísimos al archivo interno)
                            os.replace(os.path.join(os.getcwd(), nombre_archivo_original), final_xml_path)
                            
                            print(f"✅ ¡ÉXITO ROTUNDO! XML extraído y guardado en: {final_xml_path}")
                        else:
                            print("❌ El ZIP descargado estaba vacío.")
                
                finally:
                    # 5. Limpieza: borramos el ZIP temporal para no ensuciar la carpeta
                    if os.path.exists(temp_zip_path):
                        os.remove(temp_zip_path)

            except Exception as e:
                print(f"⚠️ Error en el proceso de descarga/descompresión: {e}")
                # Alternativa: Buscar el botón que tiene el icono de código (fa-file-code)
                try:
                    btn_xml_alt = frame.locator("button:has(i.fa-file-code)").first
                    with page.expect_download() as download_info:
                        btn_xml_alt.click()
                    print("✅ Descargado usando selector de icono.")
                except:
                    print(f"❌ Error final: No se pudo hallar el botón de descarga. {e}")
                    page.screenshot(path="debug_pantalla_final.png")

        except Exception as e:
            print(f"🔥 Error: {e}")
            page.screenshot(path="error_fatal.png")
        
        finally:
            print("🏁 Proceso terminado.")
            time.sleep(4)
            browser.close()

if __name__ == "__main__":
    descargar_factura_individual()