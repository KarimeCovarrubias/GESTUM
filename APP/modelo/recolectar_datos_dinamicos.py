"""
Script de recolección de dataset para las letras CON MOVIMIENTO en LSM:
J, K, Ll, Ñ, Q, X, Z.

A diferencia de recolectar_datos.py (donde cada ejemplo es UN frame), aquí
cada ejemplo es una SECUENCIA completa del movimiento de la seña, resumida
en estadísticas con landmarks.extraer_estadisticas_secuencia().

Controles:
    - Escribe la letra que vas a grabar cuando se te pida (puedes escribir
      "LL" o "Ñ" sin problema, es texto normal).
    - Con la ventana de la cámara enfocada, presiona ESPACIO para iniciar
      UNA grabación: haz el movimiento completo de la seña mientras se
      llena la barra de progreso (se detiene sola al reunir los frames
      necesarios).
    - Repite ESPACIO varias veces por letra (meta: al menos 50 secuencias).
    - 'n' para cambiar de letra, 'q' para salir.
"""

import csv
import os
import sys
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from modelo.landmarks import (
    crear_detector, extraer_landmarks_de_frame,
    extraer_estadisticas_secuencia, mp_manos, mp_dibujo,
)


def _asegurar_dataset():
    os.makedirs(os.path.dirname(config.RUTA_DATASET_DINAMICO), exist_ok=True)
    if not os.path.exists(config.RUTA_DATASET_DINAMICO):
        encabezado = [f"f{i}" for i in range(63 * 6)] + ["letra"]
        with open(config.RUTA_DATASET_DINAMICO, "w", newline="") as f:
            csv.writer(f).writerow(encabezado)


def _guardar_secuencia(estadisticas, letra):
    with open(config.RUTA_DATASET_DINAMICO, "a", newline="") as f:
        csv.writer(f).writerow(estadisticas + [letra])


def main():
    _asegurar_dataset()
    detector = crear_detector()
    camara = cv2.VideoCapture(0)

    print("Letras con movimiento:", ", ".join(sorted(config.LETRAS_DINAMICAS)))
    letra_actual = input("¿Qué letra vas a grabar? ").strip().upper()

    grabando = False
    buffer_secuencia = []
    contador = 0

    print("\nESPACIO = grabar una secuencia | 'n' = cambiar de letra | 'q' = salir\n")

    while True:
        ok, frame = camara.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        valores, landmarks_crudos = extraer_landmarks_de_frame(detector, frame_rgb)

        if landmarks_crudos is not None:
            mp_dibujo.draw_landmarks(frame, landmarks_crudos, mp_manos.HAND_CONNECTIONS)

        if grabando:
            if valores is not None:
                buffer_secuencia.append(valores)

            if len(buffer_secuencia) >= config.LONGITUD_SECUENCIA_DINAMICA:
                estadisticas = extraer_estadisticas_secuencia(buffer_secuencia)
                _guardar_secuencia(estadisticas, letra_actual)
                contador += 1
                print(f"Secuencia #{contador} de '{letra_actual}' guardada.")
                grabando = False
                buffer_secuencia = []

        if grabando:
            texto = f"Grabando '{letra_actual}': {len(buffer_secuencia)}/{config.LONGITUD_SECUENCIA_DINAMICA}"
            color = (0, 0, 255)
        else:
            texto = f"Letra: {letra_actual}  |  Secuencias: {contador}  (ESPACIO para grabar)"
            color = (0, 200, 0)

        cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        cv2.imshow("Recoleccion letras con movimiento - Gestum", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord(' ') and not grabando:
            grabando = True
            buffer_secuencia = []
        elif tecla == ord('n'):
            letra_actual = input("¿Qué letra vas a grabar ahora? ").strip().upper()
            contador = 0
        elif tecla == ord('q'):
            break

    camara.release()
    cv2.destroyAllWindows()
    print(f"\nListo. Dataset dinámico guardado en: {config.RUTA_DATASET_DINAMICO}")


if __name__ == "__main__":
    main()