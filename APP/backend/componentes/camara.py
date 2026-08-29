"""
Componente de cámara para la pantalla de lección.

Encapsula: acceso a la cámara vía streamlit-webrtc, extracción de landmarks
con MediaPipe, predicción con el modelo entrenado, y el dibujo del feedback
(correcto/incorrecto) directamente sobre el video.
"""

import os
import cv2
import av
import joblib
import streamlit as st
from streamlit_webrtc import webrtc_streamer

from APP.modelo.landmarks import crear_detector, extraer_landmarks_de_frame
from APP.modelo import landmarks as mod_landmarks
import config


@st.cache_resource
def cargar_modelo():
    """
    Carga el modelo entrenado desde disco una sola vez (cacheado por Streamlit,
    no se recarga en cada rerun de la app). Devuelve None si el archivo no existe
    todavía, para poder mostrar un aviso en vez de tronar la app.
    """
    if not os.path.exists(config.RUTA_MODELO):
        return None
    return joblib.load(config.RUTA_MODELO)


def _crear_callback(letra_objetivo, modelo):
    """
    Devuelve la función que streamlit-webrtc va a llamar por cada frame de video.
    Se genera dinámicamente para que el callback "sepa" cuál es la letra objetivo
    actual sin depender de variables globales.
    """
    detector = crear_detector()

    def procesar_frame(frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)  # efecto espejo, más natural para el usuario
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        valores, landmarks_crudos = extraer_landmarks_de_frame(detector, img_rgb)

        if valores is None:
            texto = "No se detecta mano"
            color = (0, 165, 255)  # naranja (BGR)
        elif modelo is None:
            texto = "Modelo no entrenado todavía"
            color = (0, 165, 255)
        else:
            mod_landmarks.mp_dibujo.draw_landmarks(
                img, landmarks_crudos, mod_landmarks.mp_manos.HAND_CONNECTIONS
            )
            prediccion = modelo.predict([valores])[0]

            if prediccion == letra_objetivo:
                texto = "Correcto"
                color = (0, 200, 0)  # verde (BGR)
                st.session_state["ultimo_resultado"] = "correcto"
            else:
                texto = f"Incorrecto (detecté: {prediccion})"
                color = (0, 0, 220)  # rojo (BGR)
                st.session_state["ultimo_resultado"] = "incorrecto"

        cv2.putText(img, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    return procesar_frame


def mostrar_camara(letra_objetivo):
    """
    Dibuja el bloque de cámara en la pantalla de lección, ya conectado
    al modelo entrenado y evaluando en tiempo real contra 'letra_objetivo'.
    """
    modelo = cargar_modelo()

    if modelo is None:
        st.warning(
            "Todavía no hay un modelo entrenado. Corre primero "
            "`modelo/entrenar_modelo.py` para generar `modelo_entrenado.pkl`."
        )

    webrtc_streamer(
        key=f"camara_{letra_objetivo}",
        video_frame_callback=_crear_callback(letra_objetivo, modelo),
        media_stream_constraints={"video": True, "audio": False},
    )