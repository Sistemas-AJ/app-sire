import os

def seleccionar_mensaje_por_checkbox(buzon_frame, i: int):
    """
    Selecciona el mensaje i clickeando el ASUNTO o la fila.
    """
    try:
        cb = buzon_frame.locator("input[type='checkbox']").nth(i)
        cb.wait_for(state="attached", timeout=5000)

        # ESTRATEGIA 1: Click en el ASUNTO (Suele ser el anchor principal)
        # Buscamos el texto hermano siguiente
        # Checkbox -> (espacio) -> Asunto
        try:
            # Buscamos un hermano que tenga texto y sea visible
            siblings = cb.locator("xpath=following-sibling::*")
            count = siblings.count()
            for s_idx in range(min(3, count)):
                sib = siblings.nth(s_idx)
                if len(sib.inner_text().strip()) > 5: # Asumimos que es el asunto
                    sib.scroll_into_view_if_needed(timeout=2000)
                    sib.click(timeout=2000)
                    # print(f"      [Click] Click en Asunto (Sibling {s_idx})")
                    return True
        except:
            pass

        # ESTRATEGIA 2: Click en la fila (TR)
        # Esto a veces falla si el evento está en un TD específico
        for up in [1, 2]:
            try:
                fila = cb.locator(f"xpath=ancestor::tr[{up}]")
                if fila.count() > 0:
                    fila.scroll_into_view_if_needed(timeout=2000)
                    # Forzamos click en el centro de la fila
                    fila.click(position={"x": 50, "y": 10}, timeout=2000) 
                    return True
            except:
                continue

        # ESTRATEGIA 3: Fallback click en el checkbox (A veces abre, a veces solo marca)
        cb.click(timeout=3000)
        return True
        
    except Exception as e:
        print(f"      [Click] Error seleccionando msg {i}: {e}")
        return False


def descargar_constancia_de_mensaje(page, buzon_frame, emp_ruc, idx, target_dir, expected_metadata=None, prev_fingerprint=None):
    """
    Descarga con validación estricta del panel y protección contra links estancados (stale).
    prev_fingerprint: Texto del link del mensaje anterior para evitar re-descargarlo.
    """
    
    # --- 1. Validador de cambio de panel (Texto en Body) ---
    def panel_actualizado():
        if expected_metadata:
            # Obtenemos texto 
            content = buzon_frame.locator("body").inner_text()
            
            fecha_esp = expected_metadata.get("fecha", "HOY")
            asunto_esp = expected_metadata.get("asunto", "")

            # A. Validación de Fecha
            if fecha_esp != "HOY" and fecha_esp not in content:
                return False
            
            # B. Validación de Contenido (Asunto)
            if len(asunto_esp) > 5:
                # Match exacto o parcial 
                if asunto_esp in content or asunto_esp[:20] in content:
                    return True
                if fecha_esp != "HOY":
                    return False 
                return False 
            
            # Fallback: Match solo por fecha
            if fecha_esp != "HOY":
                return True

            return True 
        else:
            return buzon_frame.locator("a:visible:has-text('constancia')").count() > 0

    print(f"   ⏳ Esperando actualización del panel (Msg {idx+1})...")
    if expected_metadata:
         print(f"   🎯 Meta Esperada -> Fecha: {expected_metadata.get('fecha')} | Asunto: {expected_metadata.get('asunto')[:40]}...")

    found_content = False
    
    # Loop de espera (12 segundos)
    # FASE 1: Esperar Contenido (Texto/Fecha)
    for _ in range(24): 
        if panel_actualizado():
            found_content = True
            break
        page.wait_for_timeout(500)
    
    if not found_content:
        print(f"   ⚠️ TIMEOUT esperando contenido panel Msg {idx+1}. (Posiblemente click falló).")
        # ABORTAR: Si el panel no cambió, no intentamos descargar basura.
        return None, None
    
    # FASE 2: Esperar Link Fresco (Stale Link Check)
    # Solo si NO validamos por contenido (metadata), dependemos del fingerprint del link.
    # Si YA validamos que el contenido del body cambió (fecha/asunto correctos), confiamos en el link actual.
    
    valid_candidate = None
    bypass_stale_check = (expected_metadata is not None and found_content)

    if prev_fingerprint and not bypass_stale_check:
        print(f"   🛡️  Verificando frescura del link (Prev: '{prev_fingerprint[:20]}...')...")
    
        for _ in range(10): 
            candidates = buzon_frame.locator("a:visible:has-text('constancia')").all()
            if not candidates:
                candidates = buzon_frame.locator("a:visible[href$='.pdf']").all()
                
            current_best = None
            if candidates: current_best = candidates[0]
                
            if current_best:
                try:
                    curr_text = current_best.inner_text().strip()
                    if prev_fingerprint and curr_text == prev_fingerprint:
                         page.wait_for_timeout(500)
                         continue
                    else:
                        valid_candidate = current_best
                        break
                except:
                    pass
            else:
                page.wait_for_timeout(500)
    else:
        # Si bypass active, tomamos el primero inmediatamente
        candidates = buzon_frame.locator("a:visible:has-text('constancia')").all()
        if not candidates: candidates = buzon_frame.locator("a:visible[href$='.pdf']").all()
        if candidates: valid_candidate = candidates[0]

    # Si despues de esperar no cambió...
    if not valid_candidate and candidates:
        if bypass_stale_check:
             # Confiamos en el primero porque el body ya cambió
             valid_candidate = candidates[0]
        else:
             # Si no hay metadata para validar, y el link sigue igual -> Abort
             if prev_fingerprint:
                  # Chequear si sigue igual
                  try:
                      if candidates[0].inner_text().strip() == prev_fingerprint:
                           print(f"   ⚠️ Link sigue siendo el mismo anterior ({prev_fingerprint[:15]}...). Abortando.")
                           return None, None
                  except: pass
             valid_candidate = candidates[0]
        
    if not valid_candidate:
        print(f"   ⚠️ Msg {idx+1}: No encontré link válido.")
        return None, None 

    # --- 3. EXTRACCIÓN FINAl ---
    try:
        link_text = valid_candidate.inner_text(timeout=1000).strip()
        print(f"      [DEBUG_LINK] Final: '{link_text}'")
    except Exception:
        link_text = f"msg_{idx+1}"

    # Limpieza
    safe = "".join(c for c in link_text if c.isalnum() or c in ("_", "-", "."))
    safe = safe[:80] if safe else f"msg_{idx+1}"

    save_path = os.path.join(target_dir, f"{emp_ruc}_{idx+1}_{safe}.pdf")
    save_path = os.path.abspath(save_path)

    # --- 5. DESCARGA CONSTANCIA (PRIMARIA) ---
    primary_path = None
    try:
        with page.expect_download(timeout=30000) as d: 
            valid_candidate.click(timeout=5000)
        
        d.value.save_as(save_path)
        primary_path = save_path
        print(f"   ✅ Descargado Constancia: {save_path}")
        
    except Exception as e:
        print(f"   ⚠️ Falló download Constancia: {e}")
        return None, None

    # --- 6. DESCARGA ANEXOS (Orden de Pago, Resolución, etc) ---
    print("   🔍 Buscando anexos/documentos internos...")
    try:
        # Debug de frames
        print(f"      [DEBUG] Frames hijos en buzon_frame: {len(buzon_frame.child_frames)}")
        
        content_frame = None
        iframe_locator = buzon_frame.locator("#contenedorMensaje")
        
        if iframe_locator.count() > 0:
            print("      [DEBUG] Iframe '#contenedorMensaje' detectado en DOM.")
            content_frame = iframe_locator.content_frame
            if content_frame:
                print("      [DEBUG] Acceso exitoso a content_frame de #contenedorMensaje.")
                # Esperar a que cargue algo
                try:
                    content_frame.locator("body").wait_for(timeout=3000)
                except:
                    print("      [DEBUG] Timeout esperando body en #contenedorMensaje")
            else:
                print("      [DEBUG] content_frame es None (¿Cross-origin o no cargado?).")
        else:
            print("      [DEBUG] No se encontró iframe '#contenedorMensaje'. Buscando en root.")

        scope = content_frame if content_frame else buzon_frame
        
        # Debug: Listar TODOS los links para ver qué hay
        all_links = scope.locator("a").all()
        print(f"      [DEBUG] Total links encontrados en scope: {len(all_links)}")
        for lnk in all_links[:5]: # Mostrar primeros 5
            try:
                href = lnk.get_attribute("href")
                txt = lnk.inner_text().strip()
                print(f"         Link: Text='{txt}' | Href='{href}'")
            except: pass

        # Busqueda especifica
        anexos = scope.locator("a[href*='goArchivoDescarga'], a[href*='accion=genhtml']").all()
        
        if not anexos:
            print("      [DEBUG] No se encontraron links con 'goArchivoDescarga' o 'genhtml'. Proando 'descargaArchivo'...")
             # A veces es 'descargaArchivo' o similar
            anexos = scope.locator("a[href*='descargar'], a[href*='Download']").all()

        print(f"      [DEBUG] Candidatos a anexo encontrados: {len(anexos)}")
        
        for i, anexo in enumerate(anexos):
            try:
                anexo_text = anexo.inner_text().strip()
                if not anexo_text: continue
                
                # Evitar descargar lo mismo que la constancia
                if anexo_text == link_text: 
                    print(f"      [DEBUG] Saltando anexo '{anexo_text}' (Es la constancia)")
                    continue
                
                print(f"   📎 Intentando descargar Anexo: {anexo_text}")
                
                safe_anexo = "".join(c for c in anexo_text if c.isalnum() or c in ("_", "-", "."))[:50]
                anexo_path = os.path.join(target_dir, f"{emp_ruc}_{idx+1}_ANEXO_{safe_anexo}.pdf")
                
                try:
                    with page.expect_download(timeout=15000) as d_anexo:
                        # A veces requieren click JS si hay eventos raros, pero probemos click normal
                        anexo.click(timeout=3000)
                        
                    d_anexo.value.save_as(anexo_path)
                    print(f"      ⬇️ Descargado Anexo Exitosamente: {anexo_path}")
                    
                    # SI ENCONTRAMOS ANEXO, ESTE ES EL ARCHIVO QUE IMPORTA
                   # Actualizamos el path que retornaremos para que la BD apunte a este
                    primary_path = anexo_path 
                    
                except Exception as down_err:
                    print(f"      ⚠️ Falló la espera de descarga para anexo: {down_err}")
                
            except Exception as e:
                print(f"      ⚠️ Error procesando candidato anexo: {e}")

    except Exception as e:
        print(f"   ⚠️ Excepción general buscando anexos: {e}")

    # Retornamos primary_path (que ahora puede ser el anexo si se encontró)
    return primary_path, link_text



import re

def extract_message_metadata(buzon_frame, i: int):
    """
    Extrae Asunto y Fecha específicos usando Regex.
    """
    try:
        cb = buzon_frame.locator("input[type='checkbox']").nth(i)
        
        # Estrategia jerárquica
        row = cb.locator("xpath=ancestor::tr[1]")
        if row.count() == 0:
            padre = cb.locator("xpath=..") 
            if len(padre.inner_text()) < 5:
                padre = cb.locator("xpath=../..")
            row = padre

        if row.count() > 0:
            text_content = row.inner_text(timeout=1000)
            
            # Anti-colisión del header global
            if "Buzón Notificaciones" in text_content and len(text_content) > 500:
                sibling_text = cb.locator("xpath=following-sibling::*[1]").inner_text()
                if sibling_text:
                    text_content = sibling_text
                else: 
                     return None

            clean_text = " ".join(text_content.split())
            
            # 1. Extraer FECHA (dd/mm/yyyy)
            # Busca patrones como 19/07/2024 o 19/07/24
            date_match = re.search(r"(\d{2}/\d{2}/\d{2,4})", clean_text)
            fecha_str = date_match.group(1) if date_match else "HOY"
            
            # 2. Extraer Título (Texto sin Fecha y sin 'ASUNTO:')
            # Quitamos "ASUNTO:", "NOTIFICACIÓN DE", etc para tener keywords fuertes
            titulo_clean = clean_text.replace("ASUNTO:", "").replace(fecha_str, "")
            # Quitamos caracteres raros
            titulo_clean = re.sub(r'[^a-zA-Z0-9\sáéíóúÁÉÍÓÚñÑ]', ' ', titulo_clean)
            titulo_clean = " ".join(titulo_clean.split())
            
            # Tomamos un chunk significativo (start)
            # A veces el título empieza con espacio o basura, tomamos los primeros 30 chars alfanuméricos
            titulo_corto = titulo_clean[:40].strip()

            # 3. Extraer ID del Mensaje (Checkbox Value)
            msg_id = "0"
            try:
                val = cb.get_attribute("value")
                if val and len(val) > 2 and val.lower() != "on":
                    msg_id = val
            except:
                pass

            return {
                "raw_text": clean_text,
                "asunto": titulo_corto,
                "fecha": fecha_str,
                "msg_id": msg_id
            }
    except Exception as e:
        print(f"   ⚠️ Error extrayendo metadata msg {i}: {e}")
    
    return None


