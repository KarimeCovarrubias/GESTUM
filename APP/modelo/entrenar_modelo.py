"""
Script de entrenamiento del modelo de clasificación de letras LSM.

Cómo se usa:
    python modelo/entrenar_modelo.py

Lee el dataset generado por recolectar_datos.py (config.RUTA_DATASET),
entrena un RandomForestClassifier y guarda el modelo entrenado en
config.RUTA_MODELO, listo para usarse en la app (componentes/camara.py).
"""

import os
import sys

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def cargar_dataset():
    """Lee el CSV de landmarks y separa features (X) de etiquetas (y)."""
    if not os.path.exists(config.RUTA_DATASET):
        raise FileNotFoundError(
            f"No se encontró el dataset en {config.RUTA_DATASET}. "
            "Corre primero modelo/recolectar_datos.py para generarlo."
        )

    datos = pd.read_csv(config.RUTA_DATASET)

    if datos.empty:
        raise ValueError("El dataset está vacío. Graba al menos una ráfaga por letra.")

    X = datos.drop(columns=["letra"])
    y = datos["letra"]
    return X, y


def entrenar_y_evaluar(X, y):
    """
    Separa datos de entrenamiento/prueba, entrena el modelo y muestra
    métricas básicas para saber qué tan bien está funcionando.
    """
    X_entrena, X_prueba, y_entrena, y_prueba = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    modelo = RandomForestClassifier(n_estimators=200, random_state=42)
    modelo.fit(X_entrena, y_entrena)

    predicciones = modelo.predict(X_prueba)
    exactitud = accuracy_score(y_prueba, predicciones)

    print(f"Exactitud en datos de prueba: {exactitud * 100:.1f}%")
    print("\nReporte por letra:")
    print(classification_report(y_prueba, predicciones, zero_division=0))

    return modelo


def guardar_modelo(modelo):
    """Guarda el modelo entrenado en disco con joblib."""
    carpeta = os.path.dirname(config.RUTA_MODELO)
    os.makedirs(carpeta, exist_ok=True)
    joblib.dump(modelo, config.RUTA_MODELO)
    print(f"\nModelo guardado en: {config.RUTA_MODELO}")


def main():
    print("Cargando dataset...")
    X, y = cargar_dataset()

    print(f"Muestras totales: {len(X)}")
    print("Muestras por letra:")
    print(y.value_counts().sort_index())

    print("\nEntrenando modelo...")
    modelo = entrenar_y_evaluar(X, y)

    guardar_modelo(modelo)


if __name__ == "__main__":
    main()