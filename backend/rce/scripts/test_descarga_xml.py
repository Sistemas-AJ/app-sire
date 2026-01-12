# backend/rce/scripts/test_descarga_xml.py
import os
import time

from playwright.sync_api import sync_playwright

from core.config import init_dirs
from automation.auth import intentar_login_automatico, handle_post_login_popups
from automation.utils import goto_menu

from rce.sol.navigation import navegar_menu_jerarquico
from rce.sol.consulta_individual import (
    CredencialesSOL,
    BusquedaComprobante,
    consultar_y_descargar_xml_individual,
)


CREDENTIALS = CredencialesSOL(
    ruc="20529929821",
    usuario="TIERTHRI",
    clave_sol="ophicanas",
)

BUSQUEDA = BusquedaComprobante(
    ruc_emisor="20526422300",
    serie="F001",
    numero="100286",
    tipo_label="Factura",
)


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
            if not goto_menu(page):
                return

            class MockEmp:
                ruc = CREDENTIALS.ruc
                usuario_sol = CREDENTIALS.usuario
                clave_sol = CREDENTIALS.clave_sol

            if not intentar_login_automatico(page, MockEmp()):
                print("❌ Error en Login.")
                return

            handle_post_login_popups(page)

            # Navegación a pantalla
            print("📂 Navegando a Consulta de Factura Individual...")
            menus = [
                "Comprobantes de pago",
                "Comprobantes de Pago",
                "Consulta de Comprobantes de Pago",
                "Nueva Consulta de comprobantes de pago"
            ]
            navegar_menu_jerarquico(page, menus)

            # Carpeta salida (por ahora local)
            out_dir = os.path.join(os.getcwd(), "downloads_xml")
            result = consultar_y_descargar_xml_individual(page, BUSQUEDA, out_dir=out_dir)

            if not result.ok:
                print(f"❌ Falló descarga: {result.error}")
                page.screenshot(path="debug_descarga_xml.png")
                return

            print(f"🎉 OK: {result.xml_path}")

        except Exception as e:
            print(f"🔥 Error fatal: {e}")
            page.screenshot(path="error_fatal.png")

        finally:
            print("🏁 Proceso terminado.")
            time.sleep(3)
            browser.close()


if __name__ == "__main__":
    descargar_factura_individual()
