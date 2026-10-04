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

# --- Parámetros de recolectar_datos.py (letras estáticas) ---
MUESTRAS_POR_RAFAGA = 60        # cuántos frames se guardan por cada ráfaga de una letra
RETARDO_ENTRE_MUESTRAS = 0.05   # segundos de espera entre cada muestra dentro de la ráfaga

# --- Letras CON MOVIMIENTO en LSM: necesitan secuencia de frames, no un solo frame ---
LETRAS_DINAMICAS = {"J", "K", "LL", "Ñ", "Q", "X", "Z"}

# --- Parámetros de recolectar_datos_dinamicos.py / evaluador.py ---
LONGITUD_SECUENCIA_DINAMICA = 26  # cuántos frames forman UN ejemplo de letra con movimiento
RUTA_DATASET_DINAMICO = os.path.join(CARPETA_DATOS_MODELO, "dataset_dinamico.csv")
RUTA_MODELO_DINAMICO = os.path.join(BASE_DIR, "modelo", "modelo_dinamico_entrenado.pkl")