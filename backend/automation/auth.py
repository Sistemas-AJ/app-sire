import time
from automation.utils import goto_menu, check_session

def intentar_login_automatico(page, emp) -> bool:
    """Intenta loguearse automáticamente con las credenciales de la empresa."""
    print("🔓 Iniciando Protocolo de Login...")
    if not goto_menu(page): return False

def handle_post_login_popups(page):
    """
    Intenta cerrar modales/popups que aparecen tras el login o al cargar el menú.
    Busca en el main frame y en todos los iframes.
    Retorna True si logra 'limpiar' la vista o si ve el botón de Buzón.
    """
    print("🛡️ Verificando y limpiando posibles modales (Informativos, Validación)...")
    
    # Textos fallback por si cambian los IDs
    OPCIONES_FINALIZAR = ["#btnFinalizarValidacionDatos", "button:has-text('Finalizar')"]
    OPCIONES_CONTINUAR = ["#btnCerrar", "button:has-text('Continuar sin confirmar')"]

    for i in range(10): # Aumentamos intentos a 10 (~10s)
        try:
            found_modal = False
            
            # Buscar en todos los frames (incluyendo main)
            frames_to_check = [page.main_frame] + page.frames
            
            for frame in frames_to_check:
                try:
                    # 1. Popup "Informativo"
                    for selector in OPCIONES_FINALIZAR:
                        btn = frame.locator(selector)
                        if btn.count() > 0 and btn.first.is_visible():
                            print(f"   ⚠️ Detectado popup Informativo en frame '{frame.name}'. Click en '{selector}'...")
                            btn.first.click()
                            page.wait_for_timeout(2000)
                            found_modal = True
                            break # Romper loop de selectores
                    if found_modal: break # Romper loop de frames

                    # 2. Pantalla "Valida tus datos"
                    for selector in OPCIONES_CONTINUAR:
                        btn = frame.locator(selector)
                        if btn.count() > 0 and btn.first.is_visible():
                            print(f"   ⚠️ Detectada pantalla de Validación en frame '{frame.name}'. Click en '{selector}'...")
                            btn.first.click()
                            page.wait_for_timeout(3000)
                            found_modal = True
                            break
                    if found_modal: break
                except:
                    continue

            if not found_modal:
                # Si no encontramos modales
                # Verificar éxito (Buzón visible y habilitado) para salir antes
                # Buscamos botón buzón en cualquier frame tambien
                buzon_visible = False
                for frame in frames_to_check:
                    try:
                        if frame.get_by_text("Buzón Electrónico").is_visible():
                            buzon_visible = True
                            break
                    except: pass
                
                if buzon_visible:
                    # Check final: si el buzon es visible, ¿seguro que no hay modal?
                    # Si acabamos de cerrar uno, esperamos. Si i > 0 y todo tranquilo, salimos.
                    if i > 1: return True
                
                page.wait_for_timeout(1000)
                continue
            
        except Exception as e:
            print(f"   ⚠️ Excepción leve en handler de modales: {e}")
            page.wait_for_timeout(1000)
            
    return True

def intentar_login_automatico(page, emp) -> bool:
    """Intenta loguearse automáticamente con las credenciales de la empresa."""
    print("🔓 Iniciando Protocolo de Login...")
    if not goto_menu(page): return False

    if check_session(page):
        print("   ✅ Falsa alarma: Ya estábamos logueados.")
        # Aun asi pasamos el handler por si acaso quedo un modal colgado de la session anterior
        handle_post_login_popups(page)
        return True

    try:
        page.wait_for_selector("#txtRuc", timeout=8000)
        print(f"⌨️  Escribiendo credenciales para {emp.ruc}...")
        page.fill("#txtRuc", emp.ruc)
        page.fill("#txtUsuario", emp.usuario_sol)
        page.fill("#txtContrasena", emp.clave_sol)
        page.click("#btnAceptar")

        print("⏳ Esperando transición post-login...")
        page.wait_for_timeout(3000)

        # Usar la función compartida
        handle_post_login_popups(page)

        if not goto_menu(page): return False

        if not goto_menu(page): return False

        if check_session(page):
            print("🚀 Login Exitoso y Confirmado.")
            return True
        else:
            print("❌ Login fallido (No se detectó sesión activa).")
            return False
    except Exception as e:
        print(f"❌ Error crítico durante el login: {e}")
        return False
