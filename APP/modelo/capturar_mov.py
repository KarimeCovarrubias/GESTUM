"""
Captura de letras CON MOVIMIENTO (J, K, LL, Ñ, Q, X, Z).
Basado en el capturar_mov.py de tus compañeros, con tres cambios:
  - Guarda en modelo/letrasmov/<LETRA>/ sin importar desde dónde lo ejecutes.
  - Usa landmarks.py (no necesita utils_mov.py).
  - La vista previa se ve en espejo (más natural); lo que se GUARDA va sin
    espejo, igual que el resto del dataset.

Los archivos quedan numerados por letra:
    modelo/letrasmov/K/K01.npy, K02.npy, K03.npy ...

Uso (desde la raíz del proyecto, con el entorno virtual activado):
    python modelo/capturar_mov.py J
    python modelo/capturar_mov.py LL
    python modelo/capturar_mov.py Ñ

Controles: ESPACIO = grabar (cuenta de 2 s y 2 s de grabación) | q = salir
"""

import glob
import os
import  
import time

import cv2
import numpy as np

CARPETA_MODELO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA_MODELO)
from landmarks import crear_detector, vector_frame  # noqa: E402

N_FRAMES = 60
MINIMO_CON_MANO = 20
LETRAS_VALIDAS = {"J", "K", "LL", "Ñ", "Q", "X", "Z"}


def siguiente_numero(carpeta, letra):
    """Primer número libre: si ya existen K01..K20, devuelve 21."""
    usados = 0
    for ruta in glob.glob(os.path.join(carpeta, f"{letra}*.npy")):
        resto = os.path.basename(ruta)[len(letra):-4]
        if resto.isdigit():
            usados = max(usados, int(resto))
    return usados + 1


def main():
    if len(sys.argv) < 2:
        print("Uso: python modelo/capturar_mov.py <letra>   (ej. K)")
        return

    letra = sys.argv[1].upper()
    if letra not in LETRAS_VALIDAS:
        print(f"'{letra}' no es una letra con movimiento. Opciones: {', '.join(sorted(LETRAS_VALIDAS))}")
        return

    carpeta = os.path.join(CARPETA_MODELO, "letrasmov", letra)
    os.makedirs(carpeta, exist_ok=True)
    n = siguiente_numero(carpeta, letra)
    print(f"Guardando en: {carpeta}  (siguiente archivo: {letra}{n:02d}.npy)")

    mano = crear_detector(min_detection_confidence=0.6)
    cap = cv2.VideoCapture(0)
    mensaje, hasta = "", 0.0

    def mostrar(frame, texto, color=(0, 255, 0), linea2=None):
        vista = cv2.flip(frame, 1)  # solo para mostrar
        cv2.putText(vista, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        if linea2:
            cv2.putText(vista, linea2, (10, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("captura movimiento", vista)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        extra = mensaje if time.time() < hasta else None
        mostrar(frame, f"Letra {letra} | guardadas: {n - 1} | ESPACIO=grabar  q=salir",
                linea2=extra)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        if k == 32:
            t0 = time.time()
            while time.time() - t0 < 2:
                ok, frame = cap.read()
                mostrar(frame, f"Preparate... {2 - int(time.time() - t0)}", (0, 200, 255))
                cv2.waitKey(1)

            secuencia, ref, detectados = [], None, 0
            for _ in range(N_FRAMES):
                ok, frame = cap.read()
                res = mano.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                vec, ref = vector_frame(res, ref)
                detectados += bool(res.multi_hand_landmarks)
                secuencia.append(vec)
                mostrar(frame, "GRABANDO - haz la seña", (0, 0, 255))
                cv2.waitKey(1)

            if detectados >= MINIMO_CON_MANO:
                np.save(os.path.join(carpeta, f"{letra}{n:02d}.npy"), np.array(secuencia))
                n += 1
                mensaje = f"Guardada ({detectados}/{N_FRAMES} frames con mano)"
            else:
                mensaje = "Se perdió la mano: NO se guardó. Repite."
            hasta = time.time() + 3
            print(mensaje)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()