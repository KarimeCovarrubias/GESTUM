"""
Logros y resumen de actividad del perfil. Todo se calcula con datos que ya
existen (racha máxima, XP, pruebas aprobadas y letras dominadas), así que no
hace falta ninguna tabla nueva.

Colocar este archivo en: backend/database/logros.py
"""

from backend.database.conexion import obtener_conexion
from backend.database.curriculum import BLOQUES, ALFABETO, _letras_dominadas
from backend.database.progreso import obtener_pruebas_aprobadas

# (id, icono, título, descripción, meta, clave de la métrica)
DEFINICION_LOGROS = [
    ("primeros_pasos", "🎯", "Primeros pasos",       "Completa tu primera lección",          1,  "lecciones"),
    ("racha_3",        "🔥", "Calentando motores",   "Alcanza una racha de 3 días",          3,  "racha"),
    ("racha_7",        "🔥", "Constancia de fuego",  "Alcanza una racha de 7 días",          7,  "racha"),
    ("xp_100",         "⭐", "Estrella naciente",    "Reúne 100 XP",                         100, "xp"),
    ("xp_500",         "🌟", "Estrella brillante",   "Reúne 500 XP",                         500, "xp"),
    ("primera_prueba", "📝", "Prueba superada",      "Aprueba tu primera prueba",            1,  "pruebas"),
    ("letras_10",      "🤟", "Manos a la obra",      "Domina 10 letras",                     10, "letras"),
    ("alfabeto",       "🏅", "Alfabeto completo",    "Domina las 28 letras del abecedario",  len(ALFABETO), "letras"),
]


def obtener_perfil_extra(usuario_id):
    """Devuelve {'logros': [...], 'resumen': {...}} para la pantalla de perfil."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT racha_maxima, puntos_xp, ultima_practica FROM usuario WHERE id = ?",
        (usuario_id,)
    )
    u = cursor.fetchone()

    cursor.execute(
        "SELECT COALESCE(SUM(veces_practicadas),0) AS p, COALESCE(SUM(veces_correctas),0) AS c "
        "FROM progreso WHERE usuario_id = ?", (usuario_id,)
    )
    suma = cursor.fetchone()
    conexion.close()

    pruebas = len(obtener_pruebas_aprobadas(usuario_id))
    letras = len(_letras_dominadas(usuario_id))

    metricas = {
        "lecciones": 1 if (u and u["ultima_practica"]) else 0,
        "racha": u["racha_maxima"] if u else 0,
        "xp": u["puntos_xp"] if u else 0,
        "pruebas": pruebas,
        "letras": letras,
    }

    logros = []
    for id_, icono, titulo, descripcion, meta, clave in DEFINICION_LOGROS:
        valor = metricas[clave]
        logros.append({
            "id": id_, "icono": icono, "titulo": titulo, "descripcion": descripcion,
            "meta": meta, "progreso": min(valor, meta), "desbloqueado": valor >= meta,
        })

    total_lecciones = sum(len(b["lecciones"]) for b in BLOQUES if b["implementado"])
    precision = round(suma["c"] / suma["p"] * 100) if suma["p"] else None

    resumen = {
        "pruebasAprobadas": pruebas,
        "totalLecciones": total_lecciones,
        "letrasDominadas": letras,
        "totalLetras": len(ALFABETO),
        "precision": precision,
    }
    return {"logros": logros, "resumen": resumen}