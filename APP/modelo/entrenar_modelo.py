"""
Entrena el modelo de letras ESTÁTICAS.

De dónde toma los datos:
  1. modelo/letrasest/<LETRA>/<LETRA>NN.npy  <- lo que graba capturar_estaticas.py
     (cada archivo es una "toma" con muchos frames).
  2. Opcional: modelo/datos/letras*.csv (sin encabezado: persona, letra, 63
     números), el formato anterior de tus compañeros. Si vas a rehacer el
     dataset desde cero, saca esos CSV de la carpeta para no mezclarlos.

Ignora las letras con movimiento (esas van en entrenar_modelo_dinamico.py).

Cómo mide la calidad: deja TOMAS completas fuera (entrena con unas tomas y
prueba con otras que el modelo no vio). Mezclar frames al azar daría ~99 % y
engaña, porque los frames de una misma toma son casi idénticos. Sigue siendo
optimista si todas las tomas son de la misma mano: pruébalo con otra persona.
"""

import glob
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GroupKFold

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import config
from modelo.landmarks import espejar_frames

ESPEJAR = True           # entrenar también con la imagen en espejo (sirve para zurdos y diestros)
BLOQUE_CSV = 60          # para los CSV viejos: 60 filas seguidas de una letra = una "toma"
TOMAS_MINIMAS = 5        # tomas por letra recomendadas
FRAMES_MINIMOS = 150     # frames por letra recomendados


def cargar_tomas():
    """Lee las tomas .npy. Devuelve un DataFrame: letra, persona, toma, 63 columnas."""
    filas = []
    for carpeta in sorted(glob.glob(os.path.join(config.CARPETA_LETRAS_ESTATICAS, "*"))):
        if not os.path.isdir(carpeta):
            continue
        letra = os.path.basename(carpeta).upper()
        for ruta in sorted(glob.glob(os.path.join(carpeta, "*.npy"))):
            datos = np.load(ruta)
            if datos.ndim != 2 or datos.shape[1] != 63:
                print(f"  (se omite {os.path.basename(ruta)}: forma {datos.shape}, se esperaba (N, 63))")
                continue
            nombre = os.path.basename(ruta)[:-4]
            persona = nombre.rsplit("_", 1)[0] if "_" in nombre else "sin_persona"
            df = pd.DataFrame(datos, columns=[f"p{i}" for i in range(63)])
            df.insert(0, "toma", f"{letra}/{nombre}")
            df.insert(0, "persona", persona)
            df.insert(0, "letra", letra)
            filas.append(df)
    return filas


def cargar_csv_viejos():
    """Lee los letras*.csv del formato anterior (si los hay)."""
    filas = []
    archivos = sorted(glob.glob(os.path.join(config.CARPETA_LETRAS_CSV, config.PATRON_LETRAS_CSV)))
    for a in archivos:
        d = pd.read_csv(a, header=None).rename(columns={0: "persona", 1: "letra"})
        d["letra"] = d["letra"].astype(str).str.upper()
        pos = d.groupby("letra").cumcount()
        d.insert(0, "toma", [f"csv:{os.path.basename(a)}:{l}:{p // BLOQUE_CSV}" for l, p in zip(d["letra"], pos)])
        d.columns = ["toma", "persona", "letra"] + [f"p{i}" for i in range(63)]
        filas.append(d[["letra", "persona", "toma"] + [f"p{i}" for i in range(63)]])
    if archivos:
        print("CSV usados:", ", ".join(os.path.basename(a) for a in archivos))
    return filas


def con_espejo(X, y):
    """Dataset original + su imagen en espejo (misma letra)."""
    if not ESPEJAR:
        return X, y
    return np.vstack([X, espejar_frames(X)]), np.concatenate([y, y])


def evaluar_por_tomas(X, y, grupos):
    """
    Validación cruzada dejando tomas completas fuera. Se entrena con tomas (y su
    espejo) y se prueba con tomas que el modelo no vio, de dos formas:
      - como las grabaste (tu mano)
      - en espejo (simula a alguien que usa la otra mano)
    """
    n_tomas = len(set(grupos))
    if n_tomas < 5:
        print("  Muy pocas tomas para evaluar (menos de 5). Graba más tomas por letra.")
        return
    Xe = espejar_frames(X)
    ok_normal = np.zeros(len(y), dtype=bool)
    ok_espejo = np.zeros(len(y), dtype=bool)
    for entrena, prueba in GroupKFold(n_splits=min(5, n_tomas)).split(X, y, grupos):
        if len(set(y[entrena])) < 2:
            continue
        Xa, ya = con_espejo(X[entrena], y[entrena])
        m = RandomForestClassifier(n_estimators=150, random_state=42, n_jobs=-1, class_weight="balanced")
        m.fit(Xa, ya)
        ok_normal[prueba] = m.predict(X[prueba]) == y[prueba]
        ok_espejo[prueba] = m.predict(Xe[prueba]) == y[prueba]
    print(f"  Precisión dejando tomas fuera (la mano con que grabaste): {ok_normal.mean() * 100:.1f} %")
    print(f"  Precisión con la mano contraria (espejo simulado):        {ok_espejo.mean() * 100:.1f} %")
    por_letra = pd.Series(ok_normal).groupby(y).mean().sort_values()
    flojas = por_letra[por_letra < 0.9]
    if len(flojas):
        print("  Letras que más se confunden: " +
              ", ".join(f"{l} ({a * 100:.0f} %)" for l, a in flojas.items()))
    else:
        print("  Todas las letras superan el 90 %.")


def main():
    partes = cargar_tomas() + cargar_csv_viejos()
    if not partes:
        print(f"No encontré datos. Graba con: python modelo/capturar_estaticas.py A\n"
              f"(se guardan en {config.CARPETA_LETRAS_ESTATICAS})")
        return
    datos = pd.concat(partes, ignore_index=True)

    dinamicas = datos["letra"].isin(config.LETRAS_DINAMICAS)
    if dinamicas.any():
        print(f"Ignorando {int(dinamicas.sum())} filas de letras con movimiento "
              f"({sorted(datos.loc[dinamicas, 'letra'].unique())}).")
    datos = datos[~dinamicas].dropna()

    columnas = [f"p{i}" for i in range(63)]
    X = datos[columnas].to_numpy(dtype=float)
    y = datos["letra"].to_numpy()
    grupos = datos["toma"].to_numpy()
    personas = datos["persona"].to_numpy()

    resumen = datos.groupby("letra").agg(frames=("toma", "size"), tomas=("toma", "nunique"))
    print(f"\nFrames: {len(X)} | Letras: {len(resumen)} | Tomas: {len(set(grupos))}")
    print(resumen.T.to_string())

    pocas = resumen[(resumen["tomas"] < TOMAS_MINIMAS) | (resumen["frames"] < FRAMES_MINIMOS)]
    if len(pocas):
        print(f"\n⚠ Letras con pocos datos (menos de {TOMAS_MINIMAS} tomas o {FRAMES_MINIMOS} frames): "
              f"{', '.join(pocas.index)}.")
        print("  Graba más tomas, moviendo un poco la mano y cambiando de lugar o de luz.")
    if len(set(personas)) <= 1:
        print("\nℹ Todo viene de la misma mano. Pídele a más personas que graben tomas: "
              "el modelo aprende mejor la letra y no solo tu mano.")

    print("\nEvaluación (tomas completas que el modelo no vio):")
    evaluar_por_tomas(X, y, grupos)

    Xf, yf = con_espejo(X, y)
    if ESPEJAR:
        print(f"\nEntrenando con {len(Xf)} ejemplos ({len(X)} grabados + {len(X)} en espejo para la otra mano).")
    modelo = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight="balanced")
    modelo.fit(Xf, yf)
    os.makedirs(os.path.dirname(config.RUTA_MODELO), exist_ok=True)
    joblib.dump(modelo, config.RUTA_MODELO)
    print(f"\nModelo estático guardado en: {config.RUTA_MODELO}")


if __name__ == "__main__":
    main()