"""
Entrena el clasificador de letras CON MOVIMIENTO (J, K, Ll, Ñ, Q, X, Z),
usando el dataset de secuencias resumidas en estadísticas que genera
recolectar_datos_dinamicos.py.

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


def main():
    if not os.path.exists(config.RUTA_DATASET_DINAMICO):
        print(
            f"No se encontró el dataset dinámico en {config.RUTA_DATASET_DINAMICO}. "
            "Corre primero modelo/recolectar_datos_dinamicos.py"
        )
        return

    datos = pd.read_csv(config.RUTA_DATASET_DINAMICO)
    if datos.empty:
        print("El dataset dinámico está vacío. Graba al menos una secuencia por letra.")
        return

    X = datos.drop(columns=["letra"])
    y = datos["letra"]

    print(f"Secuencias totales: {len(X)}")
    print("Secuencias por letra:")
    print(y.value_counts().sort_index())

    X_entrena, X_prueba, y_entrena, y_prueba = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    modelo = RandomForestClassifier(n_estimators=200, random_state=42)
    modelo.fit(X_entrena, y_entrena)

    predicciones = modelo.predict(X_prueba)
    exactitud = accuracy_score(y_prueba, predicciones)
    print(f"\nExactitud en datos de prueba: {exactitud * 100:.1f}%")
    print("\nReporte por letra:")
    print(classification_report(y_prueba, predicciones, zero_division=0))

    os.makedirs(os.path.dirname(config.RUTA_MODELO_DINAMICO), exist_ok=True)
    joblib.dump(modelo, config.RUTA_MODELO_DINAMICO)
    print(f"\nModelo dinámico guardado en: {config.RUTA_MODELO_DINAMICO}")


if __name__ == "__main__":
    main()