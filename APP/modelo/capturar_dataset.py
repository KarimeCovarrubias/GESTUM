"""
Herramienta para grabar tu propio dataset de landmarks, letra por letra,
usando la cámara de tu computadora.

Uso:
    python modelo/capturar_dataset.py

Controles (con la ventana de la cámara enfocada):
    ESPACIO -> guarda el frame actual como ejemplo de la letra en curso
    'n'     -> cambia a otra letra
    'q'     -> salir

Recomendación: graba entre 100 y 200 ejemplos por letra, moviendo un poco
la mano de posición/ángulo entre cada captura para que el modelo generalice
mejor (no solo memorice una sola pose exacta).
"""

import csv
import os
import cv2

from modelo.landmarks import crear_detector, extraer_landmarks_de_frame, mp_dibujo, mp_manos
import config


def _asegurar_dataset():
    os.makedirs(os.path.dirname(config.RUTA_DATASET), exist_ok=True)
    if not os.path.exists(config.RUTA_DATASET):
        with open(config.RUTA_DATASET, "w", newline="") as f:
            escritor = csv.writer(f)
            encabezado = ["letra"] + [f"p{i}" for i in range(63)]
            escritor.writerow(encabezado)


def _guardar_ejemplo(letra, valores):
    with open(config.RUTA_DATASET, "a", newline="") as f:
        csv.writer(f).writerow([letra] + valores)


def main():
    _asegurar_dataset()
    detector = crear_detector()
    camara = cv2.VideoCapture(0)

    letra_actual = input("¿Qué letra vas a grabar? ").strip().upper()
    contador = 0

    print("\nESPACIO = guardar ejemplo | 'n' = cambiar de letra | 'q' = salir\n")

    while True:
        ok, frame = camara.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        valores, landmarks_crudos = extraer_landmarks_de_frame(detector, img_rgb)

        if landmarks_crudos is not None:
            mp_dibujo.draw_landmarks(frame, landmarks_crudos, mp_manos.HAND_CONNECTIONS)

        color = (0, 200, 0) if valores is not None else (0, 165, 255)
        cv2.putText(frame, f"Letra: {letra_actual}  |  Ejemplos: {contador}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.imshow("Captura de dataset - Gestum", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord(' ') and valores is not None:
            _guardar_ejemplo(letra_actual, valores)
            contador += 1
        elif tecla == ord('n'):
            letra_actual = input("¿Qué letra vas a grabar ahora? ").strip().upper()
            contador = 0
        elif tecla == ord('q'):
            break

    camara.release()
    cv2.destroyAllWindows()
    print(f"\nListo. Dataset guardado en: {config.RUTA_DATASET}")


if __name__ == "__main__":
    main()