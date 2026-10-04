"""
Evaluador de señas para la pantalla de práctica en Flask.

Maneja DOS modelos:
  - Modelo ESTÁTICO (config.RUTA_MODELO): una letra = un solo frame.
  - Modelo DINÁMICO (config.RUTA_MODELO_DINAMICO): letras con movimiento
    (config.LETRAS_DINAMICAS) = una secuencia de varios frames, resumida
    con landmarks.extraer_estadisticas_secuencia().

Para una letra dinámica, evaluar_frame() va acumulando frames en un buffer
EN MEMORIA por sesión (clave_sesion) hasta reunir
config.LONGITUD_SECUENCIA_DINAMICA frames, y solo entonces evalúa -- antes
de eso regresa "recolectando": True, que el frontend debe mostrar como
"capturando movimiento...", NO como un error ni un fallo.
"""

import os
import cv2
import joblib

from modelo.landmarks import crear_detector, extraer_landmarks_de_frame, extraer_estadisticas_secuencia
import config

_detector = None
_modelo_estatico = None
_modelo_dinamico = None

# Un buffer de secuencia por sesión de usuario (no persiste en disco; se
# reinicia si cambia la letra objetivo o si se reinicia el servidor).
_buffers_dinamicos = {}


def _cargar_recursos():
    global _detector, _modelo_estatico, _modelo_dinamico

    if _detector is None:
        _detector = crear_detector()
    if _modelo_estatico is None and os.path.exists(config.RUTA_MODELO):
        _modelo_estatico = joblib.load(config.RUTA_MODELO)
    if _modelo_dinamico is None and os.path.exists(config.RUTA_MODELO_DINAMICO):
        _modelo_dinamico = joblib.load(config.RUTA_MODELO_DINAMICO)

    return _detector, _modelo_estatico, _modelo_dinamico


def evaluar_frame(imagen_bgr, letra_objetivo, clave_sesion="default"):
    """
    Recibe un frame (numpy array BGR), la letra objetivo, y una clave que
    identifica la sesión del usuario (para no mezclar el buffer de secuencia
    de un usuario con el de otro).

    Devuelve un dict:
        mano_detectada: bool
        modelo_listo:    bool
        prediccion:      str | None
        correcto:        bool | None
        recolectando:    bool  (solo relevante para letras dinámicas)
        progreso:        str, ej. "12/26"  (solo mientras recolectando=True)
    """
    detector, modelo_estatico, modelo_dinamico = _cargar_recursos()
    es_dinamica = letra_objetivo in config.LETRAS_DINAMICAS

    img_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
    valores, _landmarks_crudos = extraer_landmarks_de_frame(detector, img_rgb)

    if valores is None:
        modelo_que_aplica = modelo_dinamico if es_dinamica else modelo_estatico
        return {
            "mano_detectada": False,
            "modelo_listo": modelo_que_aplica is not None,
            "prediccion": None,
            "correcto": None,
        }

    # --- Letra estática: igual que siempre, un frame = una predicción ---
    if not es_dinamica:
        if modelo_estatico is None:
            return {"mano_detectada": True, "modelo_listo": False, "prediccion": None, "correcto": None}

        prediccion = modelo_estatico.predict([valores])[0]
        return {
            "mano_detectada": True,
            "modelo_listo": True,
            "prediccion": prediccion,
            "correcto": prediccion == letra_objetivo,
        }

    # --- Letra dinámica: acumula frames hasta reunir una secuencia completa ---
    if modelo_dinamico is None:
        return {"mano_detectada": True, "modelo_listo": False, "prediccion": None, "correcto": None}

    buffer = _buffers_dinamicos.setdefault(clave_sesion, {"letra": letra_objetivo, "frames": []})

    if buffer["letra"] != letra_objetivo:
        # Cambió la letra objetivo a medias (el usuario avanzó) -- reinicia
        buffer["letra"] = letra_objetivo
        buffer["frames"] = []

    buffer["frames"].append(valores)

    if len(buffer["frames"]) < config.LONGITUD_SECUENCIA_DINAMICA:
        return {
            "mano_detectada": True,
            "modelo_listo": True,
            "prediccion": None,
            "correcto": None,
            "recolectando": True,
            "progreso": f"{len(buffer['frames'])}/{config.LONGITUD_SECUENCIA_DINAMICA}",
        }

    estadisticas = extraer_estadisticas_secuencia(buffer["frames"])
    prediccion = modelo_dinamico.predict([estadisticas])[0]
    buffer["frames"] = []  # listo para el siguiente intento de esta misma letra

    return {
        "mano_detectada": True,
        "modelo_listo": True,
        "prediccion": prediccion,
        "correcto": prediccion == letra_objetivo,
        "recolectando": False,
    }