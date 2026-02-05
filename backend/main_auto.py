import os
import time
import hashlib
from datetime import datetime, timedelta, date
from typing import Optional, List, Callable
from sqlalchemy import or_
from playwright.sync_api import sync_playwright
from core.database import SessionLocal, Empresa, Notificacion
from core.config import SESSION_DIR, DEBUG_DIR, init_dirs
from automation.utils import goto_menu, check_session, buscar_y_clickear, get_buzon_frame, print_frames, get_smart_download_path
from automation.auth import intentar_login_automatico, handle_post_login_popups
from automation.buzon import seleccionar_mensaje_por_checkbox, descargar_constancia_de_mensaje, extract_message_metadata

# Debug Reload
print("🔄 [DEBUG] Módulo main_auto.py recargado/importado. Verificando actualizaciones...")

# --- STATE CONTROL ---
STOP_REQUESTED = False

def request_stop():
    global STOP_REQUESTED
    STOP_REQUESTED = True
    print("🛑 Solicitud de detención recibida. El robot se detendrá al terminar la empresa actual.")

def run_automation_process(
    retry_mode: bool = False,
    days_back: int = 90,
    headless: bool = False,
    rucs: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    stop_checker: Optional[Callable[[], bool]] = None,
):
    """
    Función principal de automatización invocable desde API o CLI.
    retry_mode=True: "Modo Continuar/Completar Hoy".
        - Procesa lo que falló hoy.
        - Procesa lo que está pendiente.
        - Procesa lo que se completó AYER (o antes), porque hoy es un nuevo día.
        - SOLO SALTA lo que ya se completó HOY EXITOSAMENTE.
    days_back: Días para el filtro de fecha.
    headless: True para ocultar navegador, False para verlo.
    """
    # Inicializar directorios
    init_dirs()
    
    # Conexión BD
    db = SessionLocal()
    
    # Reset flag
    global STOP_REQUESTED
    STOP_REQUESTED = False

    print(f"📋 Iniciando automatización [Modo Reintento: {retry_mode}, Días: {days_back}, Headless: {headless}]")
    
    query = db.query(Empresa).filter(Empresa.activo == True)
    if rucs:
        query = query.filter(Empresa.ruc.in_(rucs))
    
    if retry_mode:
        # Lógica Inteligente:
        # Incluir si:
        # 1. Status NO es (COMPLETADO o SIN_NOVEDADES)  -> Falló o está pendiente
        # 2. O LastRun es NULL -> Nunca corrió
        # 3. O LastRun < Inicio de Hoy -> Corrió hace días, hoy toca de nuevo
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = query.filter(
            or_(
                Empresa.last_run_status.notin_(['COMPLETADO', 'SIN_NOVEDADES']),
                Empresa.last_run_at == None,
                Empresa.last_run_at < today_start
            )
        )
    
    empresas = query.all()
    
    if not empresas:
        print("✅ No hay empresas para procesar (según filtros).")
        db.close()
        return

    print(f"🚀 Iniciando procesamiento de {len(empresas)} empresas...\n")

    run_stats = []
    stop_requested = False

    with sync_playwright() as p:
        # Lanzar navegador con argumentos anti-bot
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--start-maximized", 
                "--disable-features=TranslateUI", 
                "--disable-translate",
                "--disable-blink-features=AutomationControlled" # Esconder flag de automatizacion
            ]
        )
        
        # UA común de Windows
        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        for emp in empresas:
            # Check Stop
            if STOP_REQUESTED or (stop_checker and stop_checker()):
                stop_requested = True
                print("\n🛑 DETENIENDO AUTOMATIZACIÓN POR SOLICITUD DE USUARIO.")
                break

            print(f"\n🤖 PROCESANDO: {emp.razon_social} ({emp.ruc}) [Estado anterior: {emp.last_run_status}]")
            session_path = os.path.join(SESSION_DIR, f"{emp.ruc}.json")
            
            # Inicializar estado de esta corrida
            emp.last_run_at = datetime.now()
            emp.last_run_status = 'PROCESANDO' # Temporal
            db.commit()

            # Crear Contexto (con o sin sesión guardada)
            # Pasamos user_agent explicitamente para que no diga 'HeadlessChrome'
            if os.path.exists(session_path):
                context = browser.new_context(
                    storage_state=session_path, 
                    viewport={"width": 1280, "height": 720},
                    user_agent=USER_AGENT
                )
            else:
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=USER_AGENT
                )

            page = context.new_page()

            try:
                # 1. Login / Verificación de Sesión
                if not goto_menu(page):
                    print("❌ No se pudo cargar el menú inicial.")
                    emp.last_run_status = 'ERROR'
                    db.commit()
                    continue
                
                if not check_session(page):
                    if intentar_login_automatico(page, emp):
                        # Guardar sesión si el login fue exitoso
                        context.storage_state(path=session_path)
                        emp.estado_sesion = 'OK'
                        db.commit()
                    else:
                        print(f"❌ Saltando empresa {emp.ruc} por fallo de login.")
                        emp.last_run_status = 'ERROR'
                        db.commit()
                        continue

                # 1.5 Asegurar que no hay modales molestando (incluso si ya estabamos logueados)
                handle_post_login_popups(page)

                # 2. Navegar al Buzón
                print("🔎 Buscando botón de Buzón...")
                found = False
                if buscar_y_clickear(page, "Buzón Electrónico"): found = True
                elif buscar_y_clickear(page, "Buzón de Mensajes"): found = True
                
                if not found:
                    print("❌ No se encontró el botón del buzón.")
                    emp.last_run_status = 'ERROR'
                    db.commit()
                    continue

                # 3. Obtener Frame del Buzón
                print("⏳ Esperando UI del buzón (Buscando iframeApplication)...")
                buzon = get_buzon_frame(page)
                
                if not buzon:
                    print("❌ No apareció el iframeApplication.")
                    # page.screenshot(...)
                    emp.last_run_status = 'ERROR'
                    db.commit()
                    continue
                
                print("✅ iframeApplication cargado. Buzón listo.")

                # 4. Procesar Mensajes (Lógica de bucle)
                print("⏳ Estabilizando vista del buzón...")
                page.wait_for_timeout(3000)

                # Detección de mensajes (Checkboxes)
                mensajes = buzon.locator("input[type='checkbox']").all()
                print(f"📨 Mensajes visibles (checkboxes): {len(mensajes)}")

                if len(mensajes) == 0:
                    print("⚠️ No encontré mensajes en la lista.")
                    emp.last_run_status = 'SIN_NOVEDADES'
                    db.commit()
                    run_stats.append({
                        "ruc": emp.ruc,
                        "descargas_ok": 0,
                        "skipped": 0,
                        "errors": 0,
                        "analizados": 0,
                        "sin_novedades": True,
                    })
                else:
                    # Parametros de Filtro usando el argumento days_back
                    if date_from:
                        fecha_limite = datetime.combine(date_from, datetime.min.time())
                    else:
                        DIAS_ATRAS = days_back
                        fecha_limite = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=DIAS_ATRAS)
                    print(f"📅 Filtro activo: Mensajes posteriores a {fecha_limite.strftime('%d/%m/%Y')}")

                    download_dir = get_smart_download_path(emp.razon_social)
                    print(f"📂 Guardando PDFs en: {download_dir}")

                    # Aumentamos el rango de escaneo para buscar por fecha
                    # Escaneamos hasta 50 ultimos mensajes para encontrar los de la fecha
                    max_scan = min(50, len(mensajes))
                    
                    descargas_ok = 0
                    skipped = 0
                    errors = 0
                    last_link_fingerprint = None
                    mensajes_nuevos_encontrados = False
                    
                    print(f"⬇️ Analizando hasta {max_scan} mensajes recientes...")

                    for i in range(max_scan):
                        if STOP_REQUESTED or (stop_checker and stop_checker()):
                            stop_requested = True
                            print("🛑 Detención solicitada. Cortando procesamiento de mensajes.")
                            break
                        try:
                            # 1. Extraer Metadata
                            metadata = extract_message_metadata(buzon, i)
                            if not metadata:
                                print(f"   ⚠️ No pude leer metadata de msg {i+1}. Saltando...")
                                continue
                                
                            # 2. Verificar Fecha vs Filtro
                            fecha_str = metadata.get('fecha', 'HOY')
                            fecha_msg = None
                            
                            if fecha_str == "HOY":
                                fecha_msg = datetime.now()
                            else:
                                try:
                                    fecha_msg = datetime.strptime(fecha_str, "%d/%m/%Y")
                                except:
                                    # Intentar formato 2 digitos año
                                    try:
                                        fecha_msg = datetime.strptime(fecha_str, "%d/%m/%y")
                                    except:
                                        print(f"   ⚠️ Fecha no parseable: {fecha_str}. Asumiendo 'viejo' para seguridad.")
                                        fecha_msg = datetime(2000, 1, 1) # Muy viejo

                            fecha_msg_date = fecha_msg.date()
                            if date_to and fecha_msg_date > date_to:
                                continue

                            # Comparación
                            if fecha_msg < fecha_limite:
                                print(f"   🛑 Mensaje {i+1} es de {fecha_str} (Limit: {fecha_limite.strftime('%d/%m/%Y')}). Deteniendo búsqueda.")
                                break
                                
                            mensajes_nuevos_encontrados = True
                            
                            raw_text = metadata['raw_text']
                            msg_id = metadata.get('msg_id', '0') # ID único del checkbox
                            
                            # Firma robusta: RUC + ID_MENSAJE (Si existe) + TEXTO
                            if msg_id and msg_id != '0':
                                raw_signature = f"{emp.ruc}|{msg_id}|{raw_text}"
                            else:
                                raw_signature = f"{emp.ruc}|{raw_text}"
                                
                            hash_id = hashlib.md5(raw_signature.encode()).hexdigest()
                            
                            existe = db.query(Notificacion).filter(Notificacion.codigo_notificacion == hash_id).first()
                            if existe:
                                print(f"   ⏭️  Saltando mensaje {i+1} (Ya existe en BD: {hash_id[:8]}...)")
                                skipped += 1
                                continue

                            # Intentos de click y descarga (Retry Loop)
                            max_retries = 3
                            for attempt in range(max_retries):
                                print(f"   👆 Seleccionando mensaje {i+1} (Intento {attempt+1}/{max_retries})...")
                                ok_click = seleccionar_mensaje_por_checkbox(buzon, i)
                                if not ok_click:
                                    print("      ⚠️ Click reportó falso. Reintentando...")
                                    buzon.wait_for_timeout(1000)
                                    continue
                                
                                # Descargar
                                saved_path, current_fingerprint = descargar_constancia_de_mensaje(
                                    page, buzon, emp.ruc, i, download_dir, 
                                    expected_metadata=metadata,
                                    prev_fingerprint=last_link_fingerprint
                                )
                                
                                if saved_path:
                                    # Éxito
                                    descargas_ok += 1
                                    if current_fingerprint:
                                        last_link_fingerprint = current_fingerprint
                                        
                                    # Guardar en BD
                                    try:
                                        notif = Notificacion(
                                            ruc_empresa=emp.ruc,
                                            codigo_notificacion=hash_id, 
                                            asunto=metadata.get('asunto', 'Desconocido') if metadata else "Desconocido",
                                            fecha_emision=datetime.now(), # Fecha de creación del registro
                                            fecha_recibido_sunat=fecha_msg, # Fecha real del documento
                                            fecha_leido=datetime.now(),
                                            estado_sunat="LEIDO",
                                            ruta_pdf_local=saved_path,
                                            procesado=False
                                        )
                                        db.add(notif)
                                        db.commit()
                                        print("   💾 Guardado registro en BD.")
                                    except Exception as e:
                                        db.rollback()
                                        print(f"   ⚠️ Error guardando en DB: {e}")
                                    
                                    # Salimos del retry loop
                                    break
                                else:
                                    print(f"   ⚠️ Falló validación/descarga. Reintentando click en 2s...")
                                    page.wait_for_timeout(2000)

                            if not saved_path:
                                print(f"   ❌ No se pudo descargar mensaje {i+1} tras {max_retries} intentos.")
                                errors += 1

                            page.wait_for_timeout(800)
                        except Exception as e:
                            print(f"   ⚠️ Error procesando mensaje {i+1}: {e}")
                            errors += 1

                    print(f"🏁 Resultado: {descargas_ok}/{max_scan} items analizados.")
                    
                    # Actualizar Estado Final
                    if stop_requested:
                        emp.last_run_status = 'INCOMPLETO'
                    elif descargas_ok > 0:
                        emp.last_run_status = 'COMPLETADO'
                    else:
                        # Si no descargamos nada, pudo ser porque todos ya existían (skip) o porque falló todo.
                        # Si max_descargas > 0 y descargas_ok == 0, verificar si hubo skips?
                        # Simplificación: Si no hubo errores fatales y llegamos aquí, marcamos SIN_NOVEDADES
                        # si es que realmente no había nada nuevo.
                        # Para ser más precisos: Si hubieron skips, técnicamente "ya está al día" -> COMPLETADO?
                        # O 'SIN_NOVEDADES' (no baje nada nuevo).
                        emp.last_run_status = 'SIN_NOVEDADES'
                    
                    db.commit()
                    run_stats.append({
                        "ruc": emp.ruc,
                        "descargas_ok": descargas_ok,
                        "skipped": skipped,
                        "errors": errors,
                        "analizados": max_scan,
                        "sin_novedades": descargas_ok == 0 and not stop_requested,
                    })

            except Exception as e:
                print(f"🔥 Error Crítico en empresa {emp.ruc}: {e}")
                emp.last_run_status = 'ERROR'
                emp.last_run_error = str(e) # Guardar log de error
                db.commit()
                try:
                    page.screenshot(path=os.path.join(DEBUG_DIR, f"error_{emp.ruc}.png"))
                except:
                    pass

            finally:
                context.close()
                time.sleep(1)

        browser.close()
    
    db.close()
    return {"stopped": stop_requested, "items": run_stats}

if __name__ == "__main__":
    run_automation_process(retry_mode=False, days_back=3000)
