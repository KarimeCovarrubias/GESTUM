"""
Configuración de rutas y parámetros del proyecto.

Colocar este archivo en la raíz: config.py (mismo nivel que app.py)
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_DATOS_MODELO = os.path.join(BASE_DIR, "modelo", "datos")
RUTA_DATASET = os.path.join(CARPETA_DATOS_MODELO, "dataset_landmarks.csv")
RUTA_MODELO = os.path.join(BASE_DIR, "modelo", "modelo_entrenado.pkl")

# Carpeta opcional con una imagen de referencia por letra (ej. "A.png"),
# por si más adelante quieres mostrarlas en la pantalla de práctica.
CARPETA_IMAGENES_LETRAS = os.path.join(BASE_DIR, "frontend", "imagenes", "letras")

# --- Dataset del equipo ---
# Letras estáticas: cada compañero genera un letras.csv con capturar.py.
# Pon todos los CSV (letras.csv, letras_ana.csv, ...) en modelo/datos/ -- el
# entrenador los une solo. Formato: persona, letra, 63 números (sin encabezado).
CARPETA_LETRAS_CSV = CARPETA_DATOS_MODELO
PATRON_LETRAS_CSV = "letras*.csv"

# Letras con movimiento: capturar_mov.py guarda modelo/letrasmov/<LETRA>/<persona>_0000.npy
# (cada una de forma (60, 65)). Copia/une las carpetas de todos aquí:
CARPETA_SECUENCIAS = os.path.join(BASE_DIR, "modelo", "letrasmov")

# --- Letras CON MOVIMIENTO en LSM: necesitan secuencia de frames, no un solo frame ---
LETRAS_DINAMICAS = {"J", "K", "LL", "Ñ", "Q", "X", "Z"}

RUTA_MODELO_DINAMICO = os.path.join(BASE_DIR, "modelo", "modelo_dinamico_entrenado.pkl")

# --- Grabación de movimiento en la web ---
CLIP_DURACION_MS = 2000   # cuánto dura la grabación (capturar_mov.py: 60 frames ≈ 2 s)
CLIP_INTERVALO_MS = 70    # un frame cada 70 ms -> ~28 frames por clip
CLIP_CUENTA_REGRESIVA_S = 2
CLIP_ANCHO_PX = 480       # se reduce el frame para que el envío sea ligero