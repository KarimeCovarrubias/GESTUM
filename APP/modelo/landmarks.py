"""
Extracción de landmarks con MediaPipe y preparación de datos.

IMPORTANTE: las funciones `normalizar` y `vector_frame` hacen EXACTAMENTE lo
mismo que utils.py y utils_mov.py de tus compañeros (los scripts de captura).
Los datos de entrenamiento y los de la web tienen que prepararse igual; si
una de las dos partes cambia, el modelo deja de acertar.

Colocar en: modelo/landmarks.py
"""

import numpy as np
import mediapipe as mp

mp_manos = mp.solutions.hands
mp_dibujo = mp.solutions.drawing_utils

# Letras con movimiento: se leen como una secuencia de frames (ver config.py)
FRAMES_VALIDOS_MINIMOS = 10   # capturar_mov.py exige 20 de 60 (1/3); en la web el clip es más corto
PUNTOS_REMUESTREO = 10        # la secuencia se reduce siempre a 10 "fotos" en el tiempo


def _lista_de_puntos(landmarks):
    """Acepta el objeto de MediaPipe (con .landmark) o la lista de 21 puntos."""
    return landmarks.landmark if hasattr(landmarks, "landmark") else landmarks


def normalizar(landmarks):
    """
    Letras ESTÁTICAS. 21 puntos -> 63 números.
    Resta la muñeca (punto 0) y divide entre la distancia muñeca->nudillo del
    dedo medio (punto 9), así no importa dónde está la mano ni qué tan cerca.
    (Copia de utils.normalizar de tus compañeros.)
    """
    puntos = _lista_de_puntos(landmarks)
    pts = np.array([[p.x, p.y, p.z] for p in puntos])
    pts = pts - pts[0]
    escala = np.linalg.norm(pts[9]) or 1.0
    return (pts / escala).flatten()


def vector_frame(resultado, ref):
    """
    Letras CON MOVIMIENTO. Un frame -> 65 números (63 de forma + 2 de cuánto
    se movió la muñeca respecto al primer frame con mano).
    Sin mano devuelve ceros. (Copia de utils_mov.vector_frame.)
    """
    if not resultado.multi_hand_landmarks:
        return np.zeros(65), ref
    puntos = resultado.multi_hand_landmarks[0].landmark
    pts = np.array([[p.x, p.y, p.z] for p in puntos])
    muneca = pts[0].copy()
    if ref is None:
        ref = muneca[:2]
    forma = pts - muneca
    forma = forma / (np.linalg.norm(forma[9]) or 1.0)
    posicion = muneca[:2] - ref
    return np.concatenate([forma.flatten(), posicion]), ref


def resumir_secuencia(secuencia):
    """
    Convierte una secuencia (N, 65) en UN vector de tamaño fijo para el modelo.

    Pasos:
      1. Quita los frames sin mano (filas de ceros).
      2. Si quedan menos de FRAMES_VALIDOS_MINIMOS, devuelve None.
      3. Remuestrea a PUNTOS_REMUESTREO instantes equiespaciados. Así da igual
         si la seña se grabó a 15 o a 30 cuadros por segundo, o si la persona
         la hizo más rápido o más lento: siempre se compara "inicio -> final".
      4. Añade la desviación estándar de cada columna (cuánto se mueve).
    Resultado: 10*65 + 65 = 715 números.
    """
    mat = np.asarray(secuencia, dtype=float)
    if mat.ndim != 2 or mat.shape[1] != 65:
        return None
    mat = mat[np.abs(mat).sum(axis=1) > 0]
    if len(mat) < FRAMES_VALIDOS_MINIMOS:
        return None
    t_viejo = np.linspace(0.0, 1.0, len(mat))
    t_nuevo = np.linspace(0.0, 1.0, PUNTOS_REMUESTREO)
    remuestreada = np.stack(
        [np.interp(t_nuevo, t_viejo, mat[:, j]) for j in range(mat.shape[1])], axis=1
    )
    return np.concatenate([remuestreada.ravel(), mat.std(axis=0)])


def crear_detector(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.5,
                   static_image_mode=False):
    return mp_manos.Hands(
        static_image_mode=static_image_mode,
        max_num_hands=max_num_hands,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


def extraer_landmarks_de_frame(detector, frame_rgb):
    """
    Un frame RGB -> (63 números normalizados | None, landmarks crudos | None).
    Para letras estáticas.
    """
    resultado = detector.process(frame_rgb)
    if not resultado.multi_hand_landmarks:
        return None, None
    crudos = resultado.multi_hand_landmarks[0]
    return normalizar(crudos).tolist(), crudos


def secuencia_desde_frames(detector, frames_rgb):
    """
    Lista de frames RGB (un clip grabado) -> matriz (N, 65), igual que lo que
    guarda capturar_mov.py en los .npy.
    """
    ref = None
    filas = []
    for frame in frames_rgb:
        resultado = detector.process(frame)
        vector, ref = vector_frame(resultado, ref)
        filas.append(vector)
    return np.array(filas)