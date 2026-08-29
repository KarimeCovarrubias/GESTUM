"""
Evaluador de señas para la pantalla de práctica en Flask.

Reutiliza el mismo modelo entrenado y el mismo extractor de landmarks que
usaba camara.py (Streamlit), pero aquí recibe un frame ya decodificado
(enviado por el navegador como imagen base64) y regresa un resultado en
lugar de dibujar sobre un video en vivo.

Colocar este archivo en: backend/vision/evaluador.py
(crea la carpeta backend/vision/ y un __init__.py vacío si no existen)
"""

import os
import cv2
import joblib

from APP.modelo.landmarks import crear_detector, extraer_landmarks_de_frame
import config

# Se cargan una sola vez y se reutilizan entre peticiones (evita releer el
# modelo del disco en cada frame, que sería muy lento).
_detector = None
_modelo = None


def _cargar_recursos():
    global _detector, _modelo
    if _detector is None:
        _detector = crear_detector()
    if _modelo is None and os.path.exists(config.RUTA_MODELO):
        _modelo = joblib.load(config.RUTA_MODELO)
    return _detector, _modelo


def evaluar_frame(imagen_bgr, letra_objetivo):
    """
    Recibe un frame (numpy array BGR, como lo da cv2) y la letra objetivo.

    Devuelve un dict:
        mano_detectada: bool
        modelo_listo:    bool
        prediccion:      str | None
        correcto:        bool | None  (None si no se pudo evaluar)
    """
    detector, modelo = _cargar_recursos()

    img_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
    valores, _landmarks_crudos = extraer_landmarks_de_frame(detector, img_rgb)

    if valores is None:
        return {
            "mano_detectada": False,
            "modelo_listo": modelo is not None,
            "prediccion": None,
            "correcto": None,
        }

    if modelo is None:
        return {
            "mano_detectada": True,
            "modelo_listo": False,
            "prediccion": None,
            "correcto": None,
        }

    prediccion = modelo.predict([valores])[0]
    correcto = (prediccion == letra_objetivo)

    return {
        "mano_detectada": True,
        "modelo_listo": True,
        "prediccion": prediccion,
        "correcto": correcto,
    }