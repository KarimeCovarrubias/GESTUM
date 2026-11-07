"""
Captura de letras ESTÁTICAS (A, B, C, D, E, F, G, H, I, L, M, N, O, P, R, S, T, U, V, W, Y).

Graba MUCHOS frames seguidos mientras mueves un poco la mano, hasta que pulses
'q'. Cada grabación ("toma") se guarda en un solo archivo, por letra:

    modelo/letrasest/A/A01.npy, A02.npy, A03.npy ...
    modelo/letrasest/B/B01.npy ...

(cada archivo tiene forma (N, 63): N frames, 63 números por frame, ya
normalizados igual que en la web). La numeración sigue sola: si ya existen A01
y A02, la próxima toma será A03.

Colocar en: modelo/capturar_estaticas.py

Uso (desde la raíz del proyecto, con el entorno virtual activado):
    python modelo/capturar_estaticas.py A
    python modelo/capturar_estaticas.py B 1        <- el "1" es el número de cámara (webcam USB)

Controles (con la ventana de la cámara enfocada):
    ESPACIO -> empezar a grabar / pausar y reanudar
    q       -> dejar de grabar, GUARDAR la toma y salir
    n       -> guardar la toma y pasar a OTRA letra (sin cerrar la ventana)
    r       -> descartar la toma actual y empezar de cero

Para que el modelo aprenda bien la letra, en cada toma:
  - Mantén la seña de la letra, pero MUEVE un poco la mano: acércala y aléjala,
    gírala suavemente, inclínala, cambia su altura.
  - Haz varias tomas por letra (idealmente 5 o más), cambiando de lugar, de
    luz o de fondo entre toma y toma.
  - Si la mano se queda quieta, el script deja de guardar frames repetidos
    (te avisa en pantalla): es normal, solo muévela un poco.
"""

import glob
import os
import sys
import time

import cv2
import numpy as np

CARPETA_MODELO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA_MODELO)
sys.path.insert(0, os.path.join(CARPETA_MODELO, ".."))
from landmarks import crear_detector, extraer_landmarks_de_frame  # noqa: E402
from landmarks import mp_dibujo, mp_manos  # noqa: E402

try:
    import config  # noqa: E402
    LETRAS_DINAMICAS = set(config.LETRAS_DINAMICAS)
except Exception:  # por si se ejecuta desde otro lugar
    LETRAS_DINAMICAS = {"J", "K", "LL", "Ñ", "Q", "X", "Z"}

ABECEDARIO = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LETRAS_ESTATICAS = [l for l in ABECEDARIO if l not in LETRAS_DINAMICAS]

CARPETA_BASE = os.path.join(CARPETA_MODELO, "letrasest")

INTERVALO_S = 0.12          # como máximo un frame guardado cada 0.12 s (~8 por segundo)
DIFERENCIA_MINIMA = 0.04    # un frame se guarda solo si es distinto al anterior guardado
CUENTA_REGRESIVA_S = 3
MINIMO_FRAMES = 20          # una toma con menos frames se descarta


def siguiente_numero(carpeta, letra):
    """Primer número libre: si ya existen A01..A07, devuelve 8."""
    usados = 0
    for ruta in glob.glob(os.path.join(carpeta, f"{letra}*.npy")):
        resto = os.path.basename(ruta)[len(letra):-4]
        if resto.isdigit():
            usados = max(usados, int(resto))
    return usados + 1


def es_distinto(vector, anterior, umbral=DIFERENCIA_MINIMA):
    """True si el frame cambió lo suficiente respecto al último guardado."""
    if anterior is None:
        return True
    return float(np.linalg.norm(np.asarray(vector) - np.asarray(anterior))) >= umbral


def guardar_toma(letra, frames):
    """Guarda la toma como modelo/letrasest/<LETRA>/<LETRA>NN.npy. Devuelve la ruta o None."""
    if len(frames) < MINIMO_FRAMES:
        return None
    carpeta = os.path.join(CARPETA_BASE, letra)
    os.makedirs(carpeta, exist_ok=True)
    n = siguiente_numero(carpeta, letra)
    ruta = os.path.join(carpeta, f"{letra}{n:02d}.npy")
    np.save(ruta, np.array(frames, dtype=np.float32))
    return ruta


def abrir_camara(indice=None):
    """Abre la cámara indicada, o la primera que entregue imagen."""
    candidatos = [indice] if indice is not None else [0, 1, 2, 3]
    for i in candidatos:
        # En Windows, CAP_DSHOW abre mucho mejor las webcams USB
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) if sys.platform.startswith("win") else cv2.VideoCapture(i)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                print(f"Usando la cámara número {i}")
                return cap
        cap.release()
    return None


def pedir_letra(texto="¿Qué letra vas a grabar? "):
    while True:
        letra = input(texto).strip().upper()
        if letra in LETRAS_ESTATICAS:
            return letra
        if letra in LETRAS_DINAMICAS:
            print(f"'{letra}' lleva movimiento: se captura con modelo/capturar_mov.py {letra}")
        else:
            print(f"'{letra}' no es válida. Opciones: {', '.join(LETRAS_ESTATICAS)}")


def texto(vista, linea, y, color=(0, 255, 0), escala=0.7):
    cv2.putText(vista, linea, (10, y), cv2.FONT_HERSHEY_SIMPLEX, escala, color, 2)


def main():
    if len(sys.argv) >= 2:
        letra = sys.argv[1].upper()
        if letra not in LETRAS_ESTATICAS:
            if letra in LETRAS_DINAMICAS:
                print(f"'{letra}' lleva movimiento. Usa: python modelo/capturar_mov.py {letra}")
            else:
                print(f"'{letra}' no es una letra estática. Opciones: {', '.join(LETRAS_ESTATICAS)}")
            return
    else:
        letra = pedir_letra()

    indice = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    cap = abrir_camara(indice)
    if cap is None:
        print("No pude abrir ninguna cámara. Revisa que la webcam esté conectada, que otra "
              "aplicación (Zoom, navegador, la app) no la esté usando, y prueba con otro "
              "número: python modelo/capturar_estaticas.py A 1")
        return

    detector = crear_detector(min_detection_confidence=0.6)

    frames = []            # frames guardados de la toma actual
    ultimo = None          # último vector guardado
    estado = "listo"       # listo | cuenta | grabando | pausa
    t_cuenta = 0.0
    t_ultimo_guardado = 0.0
    t_ultimo_nuevo = time.time()
    mensaje, hasta = "", 0.0
    guardadas_sesion = {}

    def avisar(txt, seg=3.0):
        nonlocal mensaje, hasta
        mensaje, hasta = txt, time.time() + seg
        print(txt)

    def cerrar_toma():
        """Guarda la toma actual si tiene suficientes frames."""
        nonlocal frames, ultimo, estado
        if frames:
            ruta = guardar_toma(letra, frames)
            if ruta:
                guardadas_sesion[letra] = guardadas_sesion.get(letra, 0) + 1
                avisar(f"Guardada: {os.path.relpath(ruta, CARPETA_MODELO)} ({len(frames)} frames)")
            else:
                avisar(f"Toma muy corta ({len(frames)} frames, mínimo {MINIMO_FRAMES}): no se guardó.")
        frames, ultimo, estado = [], None, "listo"

    print(f"\nLetra {letra}. Se guardará en: {os.path.join(CARPETA_BASE, letra)}")
    print("ESPACIO = grabar/pausar | q = guardar y salir | n = guardar y otra letra | r = descartar\n")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("La cámara dejó de entregar imagen.")
                break

            # Se procesa el frame SIN espejo (igual que lo que manda la web)
            valores, crudos = extraer_landmarks_de_frame(detector, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            vista = frame.copy()
            if crudos is not None:
                mp_dibujo.draw_landmarks(vista, crudos, mp_manos.HAND_CONNECTIONS)
            vista = cv2.flip(vista, 1)   # el espejo es solo para que te veas natural

            ahora = time.time()

            if estado == "cuenta":
                restante = CUENTA_REGRESIVA_S - int(ahora - t_cuenta)
                if ahora - t_cuenta >= CUENTA_REGRESIVA_S:
                    estado = "grabando"
                    t_ultimo_nuevo = ahora
                else:
                    texto(vista, f"Preparate... {restante}", 30, (0, 200, 255))
            if estado == "grabando":
                if valores is not None and ahora - t_ultimo_guardado >= INTERVALO_S:
                    if es_distinto(valores, ultimo):
                        frames.append(valores)
                        ultimo = valores
                        t_ultimo_guardado = ahora
                        t_ultimo_nuevo = ahora
                texto(vista, f"GRABANDO {letra}: {len(frames)} frames", 30, (0, 0, 255))
                if valores is None:
                    texto(vista, "No se detecta la mano", 62, (0, 165, 255))
                elif ahora - t_ultimo_nuevo > 1.5:
                    texto(vista, "Mueve o gira un poco la mano", 62, (0, 255, 255))
                else:
                    texto(vista, "Muevela despacio: cerca, lejos, inclinada...", 62, (200, 200, 200), 0.55)
            elif estado == "pausa":
                texto(vista, f"PAUSA {letra}: {len(frames)} frames  (ESPACIO = seguir)", 30, (0, 200, 255))
            elif estado == "listo":
                total = guardadas_sesion.get(letra, 0)
                texto(vista, f"Letra {letra} | tomas guardadas hoy: {total}", 30)
                texto(vista, "ESPACIO = grabar   q = salir", 62, (200, 200, 200), 0.6)

            if ahora < hasta:
                texto(vista, mensaje, vista.shape[0] - 15, (0, 255, 255), 0.6)

            cv2.imshow("Captura de letras estaticas - Gestum", vista)
            tecla = cv2.waitKey(1) & 0xFF

            if tecla in (ord("q"), ord("Q")):
                cerrar_toma()
                break
            elif tecla == 32:  # ESPACIO
                if estado == "listo":
                    estado, t_cuenta = "cuenta", time.time()
                elif estado == "grabando":
                    estado = "pausa"
                elif estado == "pausa":
                    estado, t_ultimo_nuevo = "grabando", time.time()
            elif tecla in (ord("r"), ord("R")):
                frames, ultimo, estado = [], None, "listo"
                avisar("Toma descartada.")
            elif tecla in (ord("n"), ord("N")):
                cerrar_toma()
                cv2.destroyAllWindows()
                letra = pedir_letra("¿Qué letra vas a grabar ahora? ")
                print(f"Letra {letra}. Se guardará en: {os.path.join(CARPETA_BASE, letra)}")
    except KeyboardInterrupt:
        cerrar_toma()
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if guardadas_sesion:
        print("\nResumen de esta sesión:")
        for l, n in sorted(guardadas_sesion.items()):
            print(f"  {l}: {n} toma(s)")
    print("Listo. Cuando termines de capturar, entrena con: python modelo/entrenar_modelo.py")


if __name__ == "__main__":
    main()