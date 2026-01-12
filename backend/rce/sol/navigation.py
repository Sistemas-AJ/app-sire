# backend/rce/sol/navigation.py
import re

def navegar_menu_jerarquico(page, ruta_menus, timeout_ms=10000, pause_ms=1500):
    """
    Navega el menú jerárquico de SUNAT (niveles).
    Usa span.spanNivelDescripcion como en tu script original.
    """
    print(f"📂 Iniciando navegación de ruta: {' > '.join(ruta_menus)}")

    for i, menu_texto in enumerate(ruta_menus):
        selector_actual = (
            page.locator("span.spanNivelDescripcion")
            .get_by_text(menu_texto, exact=True)
            .filter(visible=True)
            .first
        )

        # Si el siguiente ya está visible, asumimos que el actual está expandido.
        if i + 1 < len(ruta_menus):
            siguiente_texto = ruta_menus[i + 1]
            siguiente_visible = (
                page.locator("span.spanNivelDescripcion")
                .get_by_text(siguiente_texto, exact=True)
                .filter(visible=True)
                .count()
            )
            if siguiente_visible > 0:
                print(f"  ⏭️ Saltando '{menu_texto}': Ya está expandido.")
                continue

        print(f"  👆 Click en '{menu_texto}'")
        selector_actual.wait_for(state="visible", timeout=timeout_ms)
        selector_actual.click()
        page.wait_for_timeout(pause_ms)
