"""
Componente reusable: la tarjetita de cada letra que se muestra en el home,
con su estado (bloqueada / disponible / completada) y su porcentaje de acierto.
"""

import os
import streamlit as st
import config


def mostrar_tarjeta_letra(letra, estado="disponible", porcentaje_acierto=None, on_click=None):
    """
    Dibuja una tarjeta individual para una letra dentro de un st.container.

    Parámetros:
        letra: texto de la letra, ej. "A"
        estado: "bloqueada" | "disponible" | "completada"
        porcentaje_acierto: número 0-100 si ya se practicó esta letra, o None
        on_click: función a ejecutar si el usuario presiona la tarjeta
                  (normalmente: ir a la pantalla de lección con esta letra)
    """
    with st.container(border=True):
        ruta_imagen = os.path.join(config.CARPETA_IMAGENES_LETRAS, f"{letra}.png")

        if estado == "bloqueada":
            if os.path.exists(ruta_imagen):
                st.image(ruta_imagen, width=64)
            else:
                st.markdown("🔒")
            st.caption("Bloqueada")
            st.button(letra, key=f"tarjeta_{letra}", disabled=True, width="stretch")
            return

        if os.path.exists(ruta_imagen):
            st.image(ruta_imagen, width=64)

        if estado == "completada":
            emoji_estado = "✅"
        else:
            emoji_estado = "🔓"

        if porcentaje_acierto is not None:
            st.caption(f"{emoji_estado} {porcentaje_acierto:.0f}% de acierto")
        else:
            st.caption(f"{emoji_estado} Sin practicar")

        if st.button(letra, key=f"tarjeta_{letra}", width="stretch"):
            if on_click is not None:
                on_click(letra)