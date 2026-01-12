import os
import time
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
    "tipo_cp": "01",  # 01 es el value para FACTURA en el select de SUNAT
    "serie": "F001",
    "numero": "100286"
}

def descargar_factura_individual():
    init_dirs()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, # Lo dejamos visible para validar el flujo
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()

        try:
            print("🚀 Iniciando sesión...")
            if not goto_menu(page): return

            # Clase Mock para usar tu helper de login
            class MockEmp:
                ruc = CREDENTIALS["ruc"]
                usuario_sol = CREDENTIALS["usuario"]
                clave_sol = CREDENTIALS["clave_sol"]

            if not intentar_login_automatico(page, MockEmp()):
                print("❌ Error en Login.")
                return
            
            handle_post_login_popups(page)

            # --- NAVEGACIÓN DIRECTA Y ROBUSTA ---
            print("📂 Navegando a Consulta de Factura Individual...")
            
            # Definimos la ruta exacta. 
            # Nota: Agregamos el texto completo para evitar ambigüedades.
            menus = [
                "Comprobantes de pago", 
                "Comprobantes de Pago", 
                "Consulta de Comprobantes de Pago", 
                "Nueva Consulta de comprobantes de pago"
            ]
            navegar_menu_jerarquico(page, menus)

            # --- ENTRADA AL IFRAME ---
            print("⏳ Esperando carga del formulario (iframe)...")
            page.wait_for_timeout(3000)

            frame = get_buzon_frame(page)
            if not frame:
                print("❌ No se encontró el iframeApplication.")
                return

            # Esperamos a que el formulario cargue
            frame.wait_for_selector("select[name='codTipoComprobante']", timeout=15000)

            print("📝 Llenando datos del comprobante...")
            # 1. Seleccionar Tipo: Factura
            frame.select_option("select[name='codTipoComprobante']", value=BUSQUEDA["tipo_cp"])
            
            # 2. RUC Emisor
            frame.fill("input[name='numRucEmisor']", BUSQUEDA["ruc_emisor"])
            
            # 3. Serie y Número
            frame.fill("input[name='numSerie']", BUSQUEDA["serie"])
            frame.fill("input[name='numCorrelativo']", BUSQUEDA["numero"])

            # 4. Consultar
            print("🔍 Ejecutando consulta...")
            frame.get_by_role("button", name="Consultar").click()

            # --- DESCARGA ---
            print("⏳ Esperando resultado y botones de descarga...")
            # Aquí SUNAT suele tardar. Esperamos a que aparezca el botón de XML
            # El selector suele ser un link que contiene el texto 'XML'
            try:
                # Esperamos que el botón sea visible
                btn_xml = frame.locator("a:has-text('XML')").first
                btn_xml.wait_for(state="visible", timeout=10000)

                print("📥 Descargando archivo XML...")
                with page.expect_download() as download_info:
                    btn_xml.click()
                
                download = download_info.value
                filename = f"{BUSQUEDA['ruc_emisor']}_{BUSQUEDA['serie']}_{BUSQUEDA['numero']}.xml"
                save_path = os.path.join(os.getcwd(), filename)
                download.save_as(save_path)
                
                print(f"✅ EXITO: Guardado en {save_path}")

                # Si también quieres el PDF, solo repites con el botón 'Visor' o 'PDF'
                # btn_pdf = frame.locator("a:has-text('Imprimir')").first ...

            except Exception as e:
                print(f"⚠️ No se encontró el botón de descarga. ¿Los datos son correctos? {e}")
                page.screenshot(path="debug_resultado_vacio.png")

        except Exception as e:
            print(f"🔥 Error: {e}")
            page.screenshot(path="error_fatal.png")
        
        finally:
            print("🏁 Proceso terminado.")
            time.sleep(4)
            browser.close()

def navegar_menu_jerarquico(page, ruta_menus):
    print(f"📂 Iniciando navegación de ruta: {' > '.join(ruta_menus)}")
    
    for i, menu_texto in enumerate(ruta_menus):
        # 1. Buscamos el elemento actual que sea visible
        # Usamos exact=True para evitar que "Comprobantes de Pago" coincida con "Consulta de Comprobantes..."
        selector_actual = page.locator("span.spanNivelDescripcion").get_by_text(menu_texto, exact=True).filter(visible=True).first
        
        # 2. Verificamos si es necesario hacer click
        # Si NO es el último elemento, revisamos si el SIGUIENTE ya está a la vista
        if i + 1 < len(ruta_menus):
            siguiente_texto = ruta_menus[i+1]
            siguiente_visible = page.locator("span.spanNivelDescripcion").get_by_text(siguiente_texto, exact=True).filter(visible=True).count()
            
            if siguiente_visible > 0:
                print(f"  ⏭️ Saltando '{menu_texto}': Ya está expandido.")
                continue

        # 3. Si no es visible el siguiente, hacemos click para expandir
        print(f"  👆 Click en '{menu_texto}'")
        selector_actual.wait_for(state="visible", timeout=10000)
        selector_actual.click()
        
        # 4. Espera crucial: SUNAT tiene animaciones lentas al abrir menús
        page.wait_for_timeout(1500)

if __name__ == "__main__":
    descargar_factura_individual()