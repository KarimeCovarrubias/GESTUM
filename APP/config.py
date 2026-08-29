"""
Configuración de rutas y parámetros del proyecto.

"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_DATOS_MODELO = os.path.join(BASE_DIR, "modelo", "datos")
RUTA_DATASET = os.path.join(CARPETA_DATOS_MODELO, "dataset_landmarks.csv")
RUTA_MODELO = os.path.join(BASE_DIR, "modelo", "modelo_entrenado.pkl")

# Carpeta opcional con una imagen de referencia por letra (ej. "A.png"),
# por si más adelante se quiere mostrarlas en la pantalla de práctica.
CARPETA_IMAGENES_LETRAS = os.path.join(BASE_DIR, "frontend", "imagenes", "letras")

# --- Parámetros de recolectar_datos.py ---
MUESTRAS_POR_RAFAGA = 60        # cuántos frames se guardan por cada ráfaga de una letra
RETARDO_ENTRE_MUESTRAS = 0.05   # segundos de espera entre cada muestra dentro de la ráfaga