"""
Evaluador de señas para Flask. Dos modelos:

  - ESTÁTICO  (config.RUTA_MODELO): una letra = un frame. evaluar_frame().
  - DINÁMICO  (config.RUTA_MODELO_DINAMICO): letras con movimiento
    (config.LETRAS_DINAMICAS) = un clip de ~2 s. evaluar_secuencia().

Si evaluar_frame() recibe una letra con movimiento NO intenta adivinar con un
solo frame: responde requiere_clip=True y la página debe grabar un clip y
mandarlo a /api/practica/evaluar-secuencia.

Los frames deben llegar SIN espejo (igual que en capturar.py de tus
compañeros). El espejo es solo visual y lo hace el CSS del <video>.

Colocar en: backend/vision/evaluador.py
"""

import os
import threading

import cv2
import joblib

from modelo.landmarks import (
    crear_detector, extraer_landmarks_de_frame, secuencia_desde_frames, resumir_secuencia,
)
import config

_detector = None
_modelo_estatico = None
_modelo_dinamico = None
# MediaPipe no es seguro con varios hilos; Flask en modo debug sí los usa.
_candado = threading.Lock()


def _cargar_recursos():
    global _detector, _modelo_estatico, _modelo_dinamico
    if _detector is None:
        _detector = crear_detector()
    if _modelo_estatico is None and os.path.exists(config.RUTA_MODELO):
        _modelo_estatico = joblib.load(config.RUTA_MODELO)
    if _modelo_dinamico is None and os.path.exists(config.RUTA_MODELO_DINAMICO):
        _modelo_dinamico = joblib.load(config.RUTA_MODELO_DINAMICO)
    return _detector, _modelo_estatico, _modelo_dinamico


def _confianza(modelo, entrada, prediccion):
    try:
        clases = list(modelo.classes_)
        return float(modelo.predict_proba([entrada])[0][clases.index(prediccion)])
    except Exception:
        return None


def evaluar_frame(imagen_bgr, letra_objetivo, clave_sesion="default"):
    """Letras estáticas: un frame -> una predicción."""
    detector, modelo_estatico, modelo_dinamico = _cargar_recursos()

    if letra_objetivo in config.LETRAS_DINAMICAS:
        return {
            "mano_detectada": True, "modelo_listo": modelo_dinamico is not None,
            "prediccion": None, "correcto": None, "requiere_clip": True,
        }

    if modelo_estatico is None:
        return {"mano_detectada": True, "modelo_listo": False, "prediccion": None, "correcto": None}

    img_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
    with _candado:
        valores, _ = extraer_landmarks_de_frame(detector, img_rgb)

    if valores is None:
        return {"mano_detectada": False, "modelo_listo": True, "prediccion": None, "correcto": None}

    prediccion = str(modelo_estatico.predict([valores])[0])
    return {
        "mano_detectada": True,
        "modelo_listo": True,
        "prediccion": prediccion,
        "correcto": prediccion == letra_objetivo,
        "confianza": _confianza(modelo_estatico, valores, prediccion),
    }


def evaluar_secuencia(frames_bgr, letra_objetivo):
    """
    Letras con movimiento: recibe el clip completo (lista de frames BGR).

    Devuelve el mismo formato que evaluar_frame(), más:
        clip_valido: False si en el clip casi no se vio la mano
    """
    _, _, modelo_dinamico = _cargar_recursos()

    if modelo_dinamico is None:
        return {"mano_detectada": True, "modelo_listo": False, "prediccion": None, "correcto": None}

    frames_rgb = [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames_bgr]
    # Detector propio por clip: el seguimiento de MediaPipe arrastra estado
    # entre frames y no queremos que se mezcle con el de otro clip/usuario.
    detector = crear_detector()
    try:
        with _candado:
            secuencia = secuencia_desde_frames(detector, frames_rgb)
    finally:
        detector.close()

    entrada = resumir_secuencia(secuencia)
    if entrada is None:
        return {
            "mano_detectada": False, "modelo_listo": True, "prediccion": None,
            "correcto": None, "clip_valido": False,
        }

    entrada = entrada.tolist()
    prediccion = str(modelo_dinamico.predict([entrada])[0])
    return {
        "mano_detectada": True,
        "modelo_listo": True,
        "clip_valido": True,
        "prediccion": prediccion,
        "correcto": prediccion == letra_objetivo,
        "confianza": _confianza(modelo_dinamico, entrada, prediccion),
    }