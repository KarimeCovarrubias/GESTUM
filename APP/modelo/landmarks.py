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

def extraer_estadisticas_secuencia(secuencia):
    """
    Resume una secuencia de N frames (letras CON MOVIMIENTO: J, K, Ll, Ñ, Q,
    X, Z) en UN solo vector de tamaño fijo, para poder clasificarla con un
    RandomForestClassifier normal en vez de necesitar una red neuronal
    recurrente.

    Por cada una de las 63 columnas (21 puntos x,y,z) calcula: media,
    desviación estándar, mínimo, máximo, rango y pendiente lineal a lo
    largo del tiempo -- la pendiente es justo lo que captura "hacia dónde
    se movió" cada punto durante la seña.

    secuencia: lista de listas, cada una con 63 valores (un frame).
    Devuelve: lista de 63 * 6 = 378 valores.
    """
    import numpy as np

    matriz = np.array(secuencia)  # forma: (n_frames, 63)

    media = matriz.mean(axis=0)
    desviacion = matriz.std(axis=0)
    minimo = matriz.min(axis=0)
    maximo = matriz.max(axis=0)
    rango = maximo - minimo

    tiempos = np.arange(matriz.shape[0])
    pendiente = np.array([
        np.polyfit(tiempos, matriz[:, columna], 1)[0]
        for columna in range(matriz.shape[1])
    ])

    estadisticas = np.concatenate([media, desviacion, minimo, maximo, rango, pendiente])
    return estadisticas.tolist()