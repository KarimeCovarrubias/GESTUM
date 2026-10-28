"""
Entrena el modelo de letras CON MOVIMIENTO (J, K, LL, Ñ, Q, X, Z) con las
secuencias que graba capturar_mov.py.

Uso (desde la raíz del proyecto):
    python modelo/entrenar_modelo_dinamico.py

Espera: modelo/letrasmov/<LETRA>/K01.npy, K02.npy ... (también sirve persona01_0000.npy)   (cada uno de forma (60, 65))
Cada secuencia se resume con landmarks.resumir_secuencia() (10 instantes
equiespaciados + variación), así no depende de la velocidad a la que se hizo
la seña ni de los cuadros por segundo de la cámara.
"""

import glob
import os
import sys

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import config
from modelo.landmarks import resumir_secuencia

MINIMO_RECOMENDADO = 50  # secuencias por letra


def cargar():
    X, y, personas = [], [], []
    descartadas = 0
    for carpeta in sorted(glob.glob(os.path.join(config.CARPETA_SECUENCIAS, "*"))):
        letra = os.path.basename(carpeta).upper()
        for ruta in sorted(glob.glob(os.path.join(carpeta, "*.npy"))):
            secuencia = np.load(ruta)
            vector = resumir_secuencia(secuencia)
            if vector is None:
                descartadas += 1
                continue
            X.append(vector)
            y.append(letra)
            nombre = os.path.basename(ruta)[:-4]
            # "persona01_0003" -> persona01 ; "K01" (sin persona) -> "sin_persona"
            personas.append(nombre.rsplit("_", 1)[0] if "_" in nombre else "sin_persona")
    return np.array(X), np.array(y), np.array(personas), descartadas


def main():
    X, y, personas, descartadas = cargar()
    if len(X) == 0:
        print(f"No encontré secuencias en {config.CARPETA_SECUENCIAS}. "
              "Copia ahí las carpetas que genera capturar_mov.py (una por letra).")
        return

    print(f"Secuencias: {len(X)} (descartadas por pocos frames con mano: {descartadas})")
    for letra in sorted(set(y)):
        n = int((y == letra).sum())
        quien = sorted(set(personas[y == letra]))
        aviso = "" if n >= MINIMO_RECOMENDADO else f"   ⚠ faltan (ideal ≥ {MINIMO_RECOMENDADO})"
        print(f"  {letra}: {n} secuencias, personas: {', '.join(quien)}{aviso}")

    faltan = sorted(config.LETRAS_DINAMICAS - set(y))
    if faltan:
        print(f"\n⚠ Sin ninguna secuencia todavía: {', '.join(faltan)}")

    if len(set(y)) < 2:
        print("\nHacen falta al menos 2 letras con movimiento para poder entrenar. "
              "No se guardó ningún modelo.")
        return

    # --- Evaluación ---
    if len(set(personas)) >= 2:
        print("\nEvaluación con una persona nueva (dejando una fuera):")
        for p in sorted(set(personas)):
            prueba, entrena = personas == p, personas != p
            comunes = set(y[entrena])
            prueba &= np.isin(y, list(comunes))
            if prueba.sum() == 0 or len(comunes) < 2:
                continue
            m = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
            m.fit(X[entrena], y[entrena])
            print(f"  {p}: {accuracy_score(y[prueba], m.predict(X[prueba])) * 100:.1f} % ({prueba.sum()} secuencias)")
    else:
        minimo = min(int((y == l).sum()) for l in set(y))
        folds = max(2, min(5, minimo))
        aciertos = []
        for a, b in StratifiedKFold(folds, shuffle=True, random_state=42).split(X, y):
            m = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1).fit(X[a], y[a])
            aciertos.append(accuracy_score(y[b], m.predict(X[b])))
        print(f"\nValidación cruzada ({folds} partes): {np.mean(aciertos) * 100:.1f} %")
        print("⚠ No se sabe de cuántas personas son las secuencias: este número es optimista (muestras parecidas entre sí).")

    modelo = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
    modelo.fit(X, y)
    os.makedirs(os.path.dirname(config.RUTA_MODELO_DINAMICO), exist_ok=True)
    joblib.dump(modelo, config.RUTA_MODELO_DINAMICO)
    print(f"\nModelo dinámico guardado en: {config.RUTA_MODELO_DINAMICO}")


if __name__ == "__main__":
    main()