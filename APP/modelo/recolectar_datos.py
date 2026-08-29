"""
Script de recolección de dataset para LSM (letras estáticas).

Cómo se usa:
    python modelo/recolectar_datos.py

Controles:
    - Presiona una letra (a-z) para iniciar una ráfaga de grabación de esa letra.
      El script capturará automáticamente MUESTRAS_POR_RAFAGA frames mientras
      mantienes la seña fija frente a la cámara.
    - Presiona ESC para salir.

Cada muestra capturada se agrega como una fila al CSV de salida, con los
63 valores de landmarks (21 puntos x,y,z) normalizados + la letra.
"""

import cv2
import csv
import os
import time
import sys

# Permite correr este script directamente (python modelo/recolectar_datos.py)
# sin depender de cómo se invoque, agregando la carpeta App/ al path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
from APP.modelo.landmarks import crear_detector, extraer_landmarks_de_frame, mp_manos, mp_dibujo


def crear_csv_si_no_existe():
    """Crea el CSV con encabezado si todavía no existe."""
    carpeta = os.path.dirname(config.RUTA_DATASET)
    os.makedirs(carpeta, exist_ok=True)

    if not os.path.exists(config.RUTA_DATASET):
        encabezado = []
        for i in range(21):
            encabezado.extend([f"x{i}", f"y{i}", f"z{i}"])
        encabezado.append("letra")

        with open(config.RUTA_DATASET, mode="w", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(encabezado)


def guardar_muestra(valores, letra):
    """Agrega una fila (landmarks + letra) al CSV."""
    with open(config.RUTA_DATASET, mode="a", newline="") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(valores + [letra])


def main():
    crear_csv_si_no_existe()

    camara = cv2.VideoCapture(0)
    if not camara.isOpened():
        print("No se pudo abrir la cámara.")
        return

    # Estado de la ráfaga de grabación en curso
    grabando = False
    letra_actual = None
    muestras_capturadas = 0
    ultima_captura = 0.0

    detector = crear_detector()

    while True:
        ok, frame = camara.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)  # efecto espejo, más natural para el usuario
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        valores, landmarks_crudos = extraer_landmarks_de_frame(detector, frame_rgb)
        mano_detectada = valores is not None

        if mano_detectada:
            mp_dibujo.draw_landmarks(frame, landmarks_crudos, mp_manos.HAND_CONNECTIONS)

            if grabando:
                ahora = time.time()
                if ahora - ultima_captura >= config.RETARDO_ENTRE_MUESTRAS:
                    guardar_muestra(valores, letra_actual)
                    muestras_capturadas += 1
                    ultima_captura = ahora

                    if muestras_capturadas >= config.MUESTRAS_POR_RAFAGA:
                        grabando = False
                        print(f"Ráfaga completa: {muestras_capturadas} muestras de '{letra_actual}' guardadas.")
                        muestras_capturadas = 0
                        letra_actual = None

        # ------------------------- Interfaz en pantalla -------------------------

        if grabando:
            texto_estado = f"Grabando '{letra_actual}': {muestras_capturadas}/{config.MUESTRAS_POR_RAFAGA}"
            color_estado = (0, 0, 255)  # rojo mientras graba
        elif not mano_detectada:
            texto_estado = "No se detecta mano"
            color_estado = (0, 165, 255)  # naranja
        else:
            texto_estado = "Presiona una letra (a-z) para grabar"
            color_estado = (0, 255, 0)  # verde, listo

        cv2.putText(frame, texto_estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, color_estado, 2)
        cv2.putText(frame, "ESC para salir", (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Recoleccion de dataset LSM", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == 27:  # ESC
            break

        se_presiono_tecla = tecla != 255
        if not grabando and se_presiono_tecla and chr(tecla).isalpha():
            letra_actual = chr(tecla).upper()
            grabando = True
            muestras_capturadas = 0
            ultima_captura = 0.0
            print(f"Iniciando ráfaga para la letra '{letra_actual}'...")

    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()