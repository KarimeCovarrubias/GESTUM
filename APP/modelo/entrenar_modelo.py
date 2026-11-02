"""
Entrena el modelo de letras ESTÁTICAS con el dataset

Uso (desde la raíz del proyecto):
    python modelo/entrenar_modelo.py

Qué hace:
  1. Une todos los modelo/datos/letras*.csv (uno por compañero, sin encabezado:
     persona, letra, 63 números).
  2. Ignora las letras con movimiento (esas van en entrenar_modelo_dinamico.py).
  3. Mide qué tan bien funcionaría con UNA PERSONA NUEVA (deja una persona
     fuera, entrena con las demás y prueba con ella). Ese número es el
     realista; el de "mezclar al azar" sale casi siempre ~99 % y engaña,
     porque capturar.py guarda decenas de fotos casi idénticas por segundo.
  4. Entrena el modelo final con TODO y lo guarda en modelo/modelo_entrenado.pkl.
"""

import glob
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import config


def cargar_datos():
    archivos = sorted(glob.glob(os.path.join(config.CARPETA_LETRAS_CSV, config.PATRON_LETRAS_CSV)))
    if not archivos:
        print(f"No encontré ningún CSV en {config.CARPETA_LETRAS_CSV} "
              f"(busqué {config.PATRON_LETRAS_CSV}). Copia ahí el letras.csv de tus compañeros.")
        return None
    partes = [pd.read_csv(a, header=None) for a in archivos]
    print("Archivos usados:", ", ".join(os.path.basename(a) for a in archivos))
    datos = pd.concat(partes, ignore_index=True)
    datos = datos.rename(columns={0: "persona", 1: "letra"})
    datos["letra"] = datos["letra"].astype(str).str.upper()
    return datos


def main():
    datos = cargar_datos()
    if datos is None:
        return

    dinamicas = datos["letra"].isin(config.LETRAS_DINAMICAS)
    if dinamicas.any():
        print(f"Ignorando {dinamicas.sum()} filas de letras con movimiento "
              f"({sorted(datos.loc[dinamicas, 'letra'].unique())}).")
    datos = datos[~dinamicas].dropna()

    X = datos.drop(columns=["persona", "letra"]).to_numpy(dtype=float)
    y = datos["letra"].to_numpy()
    personas = datos["persona"].to_numpy()

    print(f"\nFilas: {len(X)} | Letras: {len(set(y))} | Personas: {len(set(personas))}")
    resumen = datos.groupby("letra")["persona"].agg(filas="size", personas="nunique")
    print(resumen.T.to_string())

    pocas = resumen[resumen["personas"] < 2]
    if len(pocas):
        print(f"\n⚠ {len(pocas)} letras tienen datos de UNA sola persona: {', '.join(pocas.index)}.")
        print("  El modelo aprende la mano de esa persona, no la letra. Pídele a más gente que las capture.")

    # --- Evaluación honesta: dejar una persona fuera ---
    print("\nEvaluación con una persona nueva (solo en letras con 2+ personas):")
    letras_multi = set(resumen[resumen["personas"] >= 2].index)
    for p in sorted(set(personas)):
        prueba = (personas == p) & np.isin(y, list(letras_multi))
        entrena = (personas != p) & np.isin(y, list(letras_multi))
        if prueba.sum() == 0 or len(set(y[entrena])) < 2:
            continue
        m = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        m.fit(X[entrena], y[entrena])
        acc = accuracy_score(y[prueba], m.predict(X[prueba]))
        print(f"  {p}: {acc * 100:.1f} %  ({prueba.sum()} fotos)")

    # --- Modelo final con todo ---
    modelo = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
    modelo.fit(X, y)
    os.makedirs(os.path.dirname(config.RUTA_MODELO), exist_ok=True)
    joblib.dump(modelo, config.RUTA_MODELO)
    print(f"\nModelo estático guardado en: {config.RUTA_MODELO}")


if __name__ == "__main__":
    main()