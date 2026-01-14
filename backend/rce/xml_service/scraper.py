import os
import hashlib
import time
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import sync_playwright, Page

from core.config import init_dirs
from automation.auth import intentar_login_automatico, handle_post_login_popups
from automation.utils import goto_menu, buscar_y_clickear

from rce.sol.navigation import navegar_menu_jerarquico
from rce.sol.consulta_individual import BusquedaComprobante, consultar_y_descargar_xml_individual

from .config import (
    MENU_RUTA_CONSULTA,
    TIMEOUT_RESULTADO_MS,
    TIMEOUT_XML_BUTTON_MS,
    WAIT_ON_FAIL_SECONDS,
    DEFAULT_HEADLESS,
    REGISTROS_DIR,
)


@dataclass
class ScrapeResult:
    ok: bool
    xml_path: Optional[str] = None
    sha256: Optional[str] = None
    error: Optional[str] = None
    auth_error: bool = False

def _overlay_visible(page) -> bool:
    # overlay está dentro del iframe angular
    try:
        frame = page.frame_locator("#iframeApplication")
        ov = frame.locator("div.overlay:has-text('Cargando')")
        return ov.count() > 0 and ov.first.is_visible()
    except Exception:
        return False

def _recover_click_nueva_consulta(page) -> bool:
    """
    Recovery: click en el menú izquierdo 'Nueva Consulta de comprobantes de pago'
    y esperar que el componente Angular vuelva a estar disponible.
    """
    try:
        frame = page.frame_locator("#iframeApplication")
        try:
            # si hay modal "Error del Servicio", cerrarlo primero
            accept_btn = frame.locator("button:has-text('Aceptar')")
            if accept_btn.count() > 0 and accept_btn.first.is_visible():
                accept_btn.first.click()
                page.wait_for_timeout(800)
        except Exception:
            pass

        # click directo en el menú lateral (fuera del iframe)
        menu_li = page.locator("li#nivel4_11_38_1_1_1")
        if menu_li.count() > 0 and menu_li.first.is_visible():
            menu_li.first.click()
        else:
            # fallback: buscar el texto en cualquier lugar (main o frames)
            if not buscar_y_clickear(page, "Nueva Consulta de comprobantes de pago"):
                return False

        # esperar que el formulario angular esté listo otra vez
        # y que el overlay haya desaparecido
        try:
            frame.locator("div.overlay:has-text('Cargando')").wait_for(state="hidden", timeout=8000)
        except Exception:
            pass
        frame.locator("consulta-comprobante-individual").wait_for(state="visible", timeout=15000)
        return True
    except Exception:
        return False
    
def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class SolXMLScraper:
    def __init__(self, headless: bool = DEFAULT_HEADLESS):
        self.headless = headless
        self._p = None
        self._browser = None
        self._context = None
        self.page: Optional[Page] = None

    def start(self):
        init_dirs()
        self._p = sync_playwright().start()
        self._browser = self._p.chromium.launch(
            headless=self.headless,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self._context = self._browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=USER_AGENT
        )
        self.page = self._context.new_page()

    def stop(self):
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._p:
                self._p.stop()
        finally:
            self._p = None
            self._browser = None
            self._context = None
            self.page = None

    def login_and_navigate(self, ruc: str, usuario_sol: str, clave_sol: str) -> bool:
        assert self.page is not None

        if not goto_menu(self.page):
            return False

        class MockEmp:
            def __init__(self, ruc: str, usuario_sol: str, clave_sol: str):
                self.ruc = ruc
                self.usuario_sol = usuario_sol
                self.clave_sol = clave_sol

        if not intentar_login_automatico(self.page, MockEmp(ruc, usuario_sol, clave_sol)):
            return False

        handle_post_login_popups(self.page)

        # navegar una sola vez al formulario
        navegar_menu_jerarquico(self.page, MENU_RUTA_CONSULTA)
        return True

    def _reset_form_minimo(self):
        """
        Limpieza ligera: recarga el iframe si se cuelga (sin relogin).
        Si luego quieres algo más fino, implementamos 'limpiar inputs'.
        """
        assert self.page is not None
        try:
            # reload de página a veces es fuerte; preferimos ir por 'soft reset'
            # aquí dejamos como no-op por seguridad; si cuelga mucho, activamos:
            # self.page.reload(wait_until="domcontentloaded")
            pass
        except Exception:
            pass

    def descargar_xml(
        self,
        ruc_empresa: str,
        periodo: str,
        busqueda: BusquedaComprobante,
    ) -> ScrapeResult:
        """
        Intenta descargar 1 XML sin relogin.
        Si SUNAT no responde (no aparece botón XML), espera 10s y devuelve ERROR.
        """
        assert self.page is not None

        out_dir = os.path.join(REGISTROS_DIR, "periodos", periodo, ruc_empresa, "xml")
        os.makedirs(out_dir, exist_ok=True)

        # Ajustamos timeouts para tu regla: si no aparece el botón, no nos quedamos 45s
        res = consultar_y_descargar_xml_individual(
            self.page,
            busqueda,
            out_dir=out_dir,
            timeout_resultado_ms=TIMEOUT_RESULTADO_MS,
        )


        if not res.ok:
            # Heurística simple: si el error parece login/session, marcamos auth_error
            retried = False
            if _overlay_visible(self.page):
                print("🧯 Detectado overlay 'Cargando...'. Recovery: click Nueva Consulta…")
                if _recover_click_nueva_consulta(self.page):
                    retried = True
                    res = consultar_y_descargar_xml_individual(
                        self.page,
                        busqueda,
                        out_dir=out_dir,
                        timeout_resultado_ms=TIMEOUT_RESULTADO_MS,
                    )
                    if res.ok:
                        sha = _sha256_file(res.xml_path)
                        return ScrapeResult(ok=True, xml_path=res.xml_path, sha256=sha)
            err = (res.error or "").lower()
            auth_like = ("login" in err) or ("autentic" in err) or ("401" in err)
            time.sleep(WAIT_ON_FAIL_SECONDS if not retried else 2)
            self._reset_form_minimo()
            return ScrapeResult(ok=False, error=res.error, auth_error=auth_like)

        sha = _sha256_file(res.xml_path)
        return ScrapeResult(ok=True, xml_path=res.xml_path, sha256=sha)
