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
        "intro_teoria": (
            "La dactilología es el alfabeto manual de la Lengua de Señas Mexicana: "
            "cada letra del español tiene una forma de mano que la representa. Se usa "
            "sobre todo para deletrear nombres propios o palabras que todavía no tienen "
            "una seña propia asignada. "
            "\nRepasa cada letra con calma antes de practicar frente a la cámara."
        ),
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


def obtener_leccion(leccion_id):
    """
    Busca una lección por su id en cualquier bloque. Le anexa el texto
    introductorio del bloque (intro_bloque) SOLO si es la primera lección
    de ese bloque, para que no se repita en cada lección. None si no existe.
    """
    for bloque in BLOQUES:
        for indice, leccion in enumerate(bloque["lecciones"]):
            if leccion["id"] == leccion_id:
                leccion_con_intro = dict(leccion)
                es_primera_leccion = indice == 0
                leccion_con_intro["intro_bloque"] = (
                    bloque.get("intro_teoria", "") if es_primera_leccion else ""
                )
                return leccion_con_intro
    return None


def obtener_siguiente_leccion_id(leccion_id):
    """
    Devuelve el id de la siguiente lección implementada en la secuencia
    (recorriendo todos los bloques implementados en orden), o None si
    'leccion_id' es la última o no se encontró.
    """
    secuencia = []
    for bloque in BLOQUES:
        if not bloque["implementado"]:
            continue
        for leccion in bloque["lecciones"]:
            secuencia.append(leccion["id"])

    try:
        indice = secuencia.index(leccion_id)
    except ValueError:
        return None

    if indice + 1 < len(secuencia):
        return secuencia[indice + 1]
    return None


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
                "id": f"{leccion['id']}-teoria",
                "titulo": leccion["titulo"],
                "tipo": "teoria",
                "estado": estado,
            })
            lecciones_resultado.append({
                "id": f"{leccion['id']}-practica",
                "titulo": leccion["titulo"],
                "tipo": "practica",
                "estado": estado,
            })

        resultado.append({
            "id": bloque["id"],
            "titulo": bloque["titulo"],
            "totalLecciones": len(lecciones_resultado),
            "desbloqueado": desbloqueado,
            "lecciones": lecciones_resultado,
        })

        bloque_anterior_completo = bloque_completo and bloque["implementado"]

    return resultado