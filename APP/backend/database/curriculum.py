"""
Definición del currículo (bloques y lecciones) y cálculo del progreso real
de cada usuario.

Por ahora solo el Bloque 1 (Abecedario) tiene contenido real, respaldado por
la tabla 'letras' + 'progreso'. El Bloque 2 se muestra bloqueado con un aviso
de "próximamente" hasta que se implemente su contenido (no hay todavía una
tabla que represente saludos/frases).

Colocar este archivo en: backend/database/curriculum.py
"""

from backend.database.conexion import obtener_conexion

ALFABETO = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Umbral: cuántas veces_correctas necesita una letra para considerarse "dominada"
UMBRAL_DOMINIO = 1

BLOQUES = [
    {
        "id": 1,
        "titulo": "Abecedario",
        "implementado": True,
        "lecciones": [
            {"id": "A-E", "titulo": "A – E", "letras": ["A", "B", "C", "D", "E"]},
            {"id": "F-J", "titulo": "F – J", "letras": ["F", "G", "H", "I", "J"]},
            {"id": "K-O", "titulo": "K – O", "letras": ["K", "L", "M", "N", "O"]},
            {"id": "P-T", "titulo": "P – T", "letras": ["P", "Q", "R", "S", "T"]},
            {"id": "U-Z", "titulo": "U – Z", "letras": ["U", "V", "W", "X", "Y", "Z"]},
            {"id": "Repaso-1", "titulo": "Repaso", "letras": ALFABETO},
        ],
    },
    {
        "id": 2,
        "titulo": "Saludos y presentación",
        "implementado": False,
        "lecciones": [
            {"id": "S1", "titulo": "Hola y adiós", "letras": []},
            {"id": "S2", "titulo": "Cortesía", "letras": []},
            {"id": "S3", "titulo": "Mi nombre", "letras": []},
            {"id": "S4", "titulo": "Repaso", "letras": []},
        ],
    },
]


def sembrar_letras():
    """
    Inserta el alfabeto en la tabla 'letras' si todavía no existe
    (INSERT OR IGNORE no duplica si ya están). Llamar una vez al arrancar
    la app, junto a inicializar_bd().
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    for letra in ALFABETO:
        cursor.execute(
            "INSERT OR IGNORE INTO letras (letra, tipo, dificultad) VALUES (?, 'estatica', 'facil')",
            (letra,),
        )
    conexion.commit()
    conexion.close()


def _letras_dominadas(usuario_id):
    """Devuelve el conjunto de letras (texto) que el usuario ya domina."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT l.letra
        FROM progreso p
        JOIN letras l ON l.id = p.letra_id
        WHERE p.usuario_id = ? AND p.veces_correctas >= ?
    """, (usuario_id, UMBRAL_DOMINIO))
    filas = cursor.fetchall()
    conexion.close()
    return {fila["letra"] for fila in filas}


def obtener_progreso_usuario(usuario_id):
    """
    Construye la estructura de bloques/lecciones con el estado real
    ('completada' | 'actual' | 'bloqueada') para el usuario dado.
    """
    dominadas = _letras_dominadas(usuario_id)

    resultado = []
    bloque_anterior_completo = True  # el primer bloque siempre inicia desbloqueado

    for bloque in BLOQUES:
        lecciones_resultado = []
        bloque_completo = True
        actual_asignado = False
        desbloqueado = bloque_anterior_completo and bloque["implementado"]

        for leccion in bloque["lecciones"]:
            if not bloque["implementado"] or not desbloqueado:
                estado = "bloqueada"
                bloque_completo = False
            else:
                completada = bool(leccion["letras"]) and all(
                    letra in dominadas for letra in leccion["letras"]
                )
                if completada:
                    estado = "completada"
                elif not actual_asignado:
                    estado = "actual"
                    actual_asignado = True
                    bloque_completo = False
                else:
                    estado = "bloqueada"
                    bloque_completo = False

            lecciones_resultado.append({
                "id": leccion["id"],
                "titulo": leccion["titulo"],
                "estado": estado,
            })

        resultado.append({
            "id": bloque["id"],
            "titulo": bloque["titulo"],
            "totalLecciones": len(bloque["lecciones"]),
            "desbloqueado": desbloqueado,
            "lecciones": lecciones_resultado,
        })

        bloque_anterior_completo = bloque_completo and bloque["implementado"]

    return resultado

def obtener_leccion(leccion_id):
    """Busca una lección por su id en cualquier bloque. None si no existe."""
    for bloque in BLOQUES:
        for leccion in bloque["lecciones"]:
            if leccion["id"] == leccion_id:
                return leccion
    return None