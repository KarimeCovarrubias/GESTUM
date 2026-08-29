"""
Funciones de extracción de landmarks con MediaPipe, reutilizables tanto
por el script de recolección de datos como por la app en tiempo real.
"""

import mediapipe as mp

mp_manos = mp.solutions.hands
mp_dibujo = mp.solutions.drawing_utils


def normalizar_landmarks(landmarks):
    """
    Convierte los 21 puntos de MediaPipe en una lista plana de 63 números,
    normalizados respecto a la muñeca (punto 0), para que no importe en qué
    parte del cuadro esté la mano ni qué tan lejos de la cámara.
    """
    base_x = landmarks[0].x
    base_y = landmarks[0].y
    base_z = landmarks[0].z

    valores = []
    for punto in landmarks:
        valores.extend([
            punto.x - base_x,
            punto.y - base_y,
            punto.z - base_z,
        ])
    return valores


def crear_detector(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7):
    """
    Crea y devuelve una instancia del detector de manos de MediaPipe,
    lista para usarse con 'with' o guardarse en session_state de Streamlit.
    """
    return mp_manos.Hands(
        max_num_hands=max_num_hands,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


def extraer_landmarks_de_frame(detector, frame_rgb):
    """
    Corre el detector sobre un frame ya convertido a RGB.

    Devuelve una tupla (valores_normalizados, landmarks_crudos):
    - valores_normalizados: lista de 63 números, o None si no se detectó mano
    - landmarks_crudos: el objeto de MediaPipe (útil para dibujar el esqueleto
      de la mano sobre el frame), o None si no se detectó mano
    """
    resultado = detector.process(frame_rgb)

    if not resultado.multi_hand_landmarks:
        return None, None

    landmarks_crudos = resultado.multi_hand_landmarks[0]
    valores_normalizados = normalizar_landmarks(landmarks_crudos.landmark)
    return valores_normalizados, landmarks_crudos