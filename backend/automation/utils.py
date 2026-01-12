from core.config import URL_MENU

# --- FUNCIONES DE NAVEGACIÓN Y UTILS ---

def check_session(page) -> bool:
    """Verifica si la sesión sigue activa."""
    # Si está el login visible, estás fuera
    if page.locator("#txtRuc").count() > 0 and page.locator("#txtRuc").is_visible():
        return False

    # Señales positivas
    if page.get_by_text("Salir").count() > 0:
        return True

    for f in page.frames:
        u = (f.url or "").lower()
        if "sunat.gob.pe" in u and "api-seguridad" not in u and "menuinternet" not in u:
            return True

    return True

def goto_menu(page, retries=3):
    """Navega al menú principal con reintentos."""
    for i in range(retries):
        try:
            print(f"   ... Navegando al Menú SOL (intento {i+1}/{retries}) ...")
            page.goto(URL_MENU, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            if "api-seguridad.sunat.gob.pe" in page.url:
                print("   🚦 En api-seguridad. Esperando redirección...")
                try:
                    page.wait_for_url("**e-menu.sunat.gob.pe/**", timeout=15000)
                except Exception:
                    page.wait_for_timeout(1500)
                    continue
            return True

        except Exception as e:
            if "net::ERR_ABORTED" in str(e):
                page.wait_for_timeout(1500)
                continue
            print(f"   ❌ Falla navegando al menú: {e}")
            page.wait_for_timeout(1500)
    return False

def buscar_y_clickear(page, texto_boton):
    """Busca un botón por texto en main frame o iframes y le da click."""
    # 1. Main Page
    if page.get_by_text(texto_boton).count() > 0:
        print(f"   👆 Click en '{texto_boton}' (Main Page)")
        page.get_by_text(texto_boton).click()
        return True
    # 2. Frames
    for frame in page.frames:
        try:
            btn = frame.get_by_text(texto_boton)
            if btn.count() > 0 and btn.first.is_visible():
                print(f"   👆 Click en '{texto_boton}' (Frame: {frame.name})")
                btn.first.click()
                return True
        except: pass
    return False

def print_frames(page, label=""):
    """Imprime lista de frames para debug."""
    print(f"   [DEBUG] Frames {label}:")
    for f in page.frames:
        try:
            print("     -", f.name, (f.url or "")[:100])
        except: pass


def get_buzon_frame(page):
    """Busca el iframeApplication donde vive el buzón real"""
    page.wait_for_timeout(1000)
    for _ in range(40): # 20 segundos de intento
        f = page.frame(name="iframeApplication")
        # Validamos que tenga URL de visor (para no agarrar un frame vacío)
        if f and f.url and "ol-ti-itvisornoti" in f.url:
            return f
        page.wait_for_timeout(500)
    return None

import re
from datetime import datetime
import os

def get_smart_download_path(razon_social, base_dir="downloads"):
    """
    Genera ruta inteligente: downloads/RAZON_CORTO/AÑO/
    Ej: downloads/ADOLFO_JUR/2026/
    """
    # 1. Limpiar y acortar nombre
    # Solo letras y numeros, espacios a guion bajo
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', razon_social).upper()
    # Colapsar guiones bajos repetidos
    safe_name = re.sub(r'_+', '_', safe_name)
    # Tomar primeros 10 chars
    short_name = safe_name[:10]
    
    # 2. Año actual
    year = str(datetime.now().year)
    
    # 3. Construir ruta
    full_path = os.path.join(base_dir, short_name, year)
    
    # 4. Asegurar que existe
    os.makedirs(full_path, exist_ok=True)
    
    return full_path

