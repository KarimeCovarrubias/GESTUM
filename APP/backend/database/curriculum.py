"""
Definición del currículo (bloques, lecciones y pruebas) y cálculo del
progreso real de cada usuario.

Cada lección del Bloque 1 tiene ahora TRES pasos: Teoría, Práctica y Prueba.
La Prueba consiste en deletrear 2-3 palabras frente a la cámara usando
TODAS las letras vistas hasta ese punto (acumulado, no solo las del rango
actual) -- varios rangos de letras (F-J, P-T, U-Z) casi no tienen vocales
y no alcanzarían para formar palabras reales en español si se limitaran
solo a su propio rango.

Por ahora solo el Bloque 1 (Abecedario) tiene contenido real. El Bloque 2
se muestra bloqueado con un aviso de "próximamente" hasta que se
implemente su contenido.

Colocar este archivo en: backend/database/curriculum.py
"""

from backend.database.conexion import obtener_conexion
from backend.database.progreso import obtener_pruebas_aprobadas

ALFABETO = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Umbral: cuántas veces_correctas necesita una letra para considerarse "dominada"
UMBRAL_DOMINIO = 1

XP_POR_LETRA = 3

# --- MODO DE PRUEBAS ---
# En True: desbloquea TODAS las lecciones de los bloques implementados,
# sin importar el progreso real, para poder probarlas libremente.
# Ponlo en False cuando quieras que el desbloqueo real (secuencial) vuelva
# a aplicar -- antes de que usuarios reales usen la app.
FORZAR_DESBLOQUEO_TOTAL = True

BLOQUES = [
    {
        "id": 1,
        "titulo": "Abecedario",
        "implementado": True,
        "intro_teoria": (
            "La dactilología es el alfabeto manual de la Lengua de Señas Mexicana: "
            "cada letra del español tiene una forma de mano que la representa. Se usa "
            "sobre todo para deletrear nombres propios o palabras que todavía no tienen "
            "una seña propia asignada. Repasa cada letra con calma antes de practicar "
            "frente a la cámara."
        ),
        "lecciones": [
            {
                "id": "A-E", "titulo": "A – E",
                "letras": ["A", "B", "C", "D", "E"],
                "palabras_prueba": ["CADA", "DEBE", "BEBA"],
            },
            {
                "id": "F-J", "titulo": "F – J",
                "letras": ["F", "G", "H", "I", "J"],
                "palabras_prueba": ["HIJA", "FIJA", "EDAD"],
            },
            {
                "id": "K-O", "titulo": "K – O",
                "letras": ["K", "L", "M", "N", "O"],
                "palabras_prueba": ["MANO", "LIMON", "CAJA"],
            },
            {
                "id": "P-T", "titulo": "P – T",
                "letras": ["P", "Q", "R", "S", "T"],
                "palabras_prueba": ["CASA", "PATO", "LIBRO"],
            },
            {
                "id": "U-Z", "titulo": "U – Z",
                "letras": ["U", "V", "W", "X", "Y", "Z"],
                "palabras_prueba": ["AZUL", "VUELO", "ZAPATO"],
            },
            {
                "id": "Repaso-1", "titulo": "Repaso",
                "letras": ALFABETO,
                "palabras_prueba": ["SOL", "LUNA", "GATO"],
            },
        ],
    },
    {
        "id": 2,
        "titulo": "Saludos y presentación",
        "implementado": False,
        "lecciones": [
            {"id": "S1", "titulo": "Hola y adiós", "letras": [], "palabras_prueba": []},
            {"id": "S2", "titulo": "Cortesía", "letras": [], "palabras_prueba": []},
            {"id": "S3", "titulo": "Mi nombre", "letras": [], "palabras_prueba": []},
            {"id": "S4", "titulo": "Repaso", "letras": [], "palabras_prueba": []},
        ],
    },
]


def obtener_leccion(leccion_id):
    """
    Busca una lección por su id en cualquier bloque. Le anexa el texto
    introductorio del bloque (intro_bloque) SOLO si es la primera lección
    de ese bloque, y el XP total que se gana al completarla (xp_total).
    None si no existe.
    """
    for bloque in BLOQUES:
        for indice, leccion in enumerate(bloque["lecciones"]):
            if leccion["id"] == leccion_id:
                leccion_con_intro = dict(leccion)
                es_primera_leccion = indice == 0
                leccion_con_intro["intro_bloque"] = (
                    bloque.get("intro_teoria", "") if es_primera_leccion else ""
                )
                leccion_con_intro["xp_total"] = len(leccion["letras"]) * XP_POR_LETRA
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

    Cada lección produce TRES tiles: teoría, práctica y prueba.
    Teoría y práctica comparten estado (se desbloquean juntas, como antes).
    La prueba se desbloquea solo cuando las letras de la lección ya están
    dominadas, y el SIGUIENTE rango de letras solo se desbloquea cuando la
    prueba de la lección actual ya fue aprobada (no solo con dominar las
    letras) -- así la prueba es el verdadero "examen final" de cada rango.
    """
    dominadas = _letras_dominadas(usuario_id)
    pruebas_aprobadas = obtener_pruebas_aprobadas(usuario_id)

    resultado = []
    bloque_anterior_completo = True  # el primer bloque siempre inicia desbloqueado

    for bloque in BLOQUES:
        lecciones_resultado = []
        bloque_completo = True
        actual_asignado = False
        desbloqueado = FORZAR_DESBLOQUEO_TOTAL or (bloque_anterior_completo and bloque["implementado"])

        for leccion in bloque["lecciones"]:
            if not bloque["implementado"] or not desbloqueado:
                estado_tp = "bloqueada"
                estado_prueba = "bloqueada"
                bloque_completo = False

            elif FORZAR_DESBLOQUEO_TOTAL:
                # Modo pruebas: todo disponible, sin calcular progreso real
                estado_tp = "actual"
                estado_prueba = "actual"

            else:
                letras_completas = bool(leccion["letras"]) and all(
                    letra in dominadas for letra in leccion["letras"]
                )
                prueba_pasada = leccion["id"] in pruebas_aprobadas
                leccion_completa = letras_completas and prueba_pasada

                if leccion_completa:
                    estado_tp = "completada"
                    estado_prueba = "completada"
                elif letras_completas:
                    # Ya domina las letras: teoría/práctica quedan como
                    # completadas y la prueba es lo que falta (el "actual").
                    estado_tp = "completada"
                    if not actual_asignado:
                        estado_prueba = "actual"
                        actual_asignado = True
                    else:
                        estado_prueba = "bloqueada"
                elif not actual_asignado:
                    estado_tp = "actual"
                    estado_prueba = "bloqueada"
                    actual_asignado = True
                else:
                    estado_tp = "bloqueada"
                    estado_prueba = "bloqueada"

                if not leccion_completa:
                    bloque_completo = False

            lecciones_resultado.append({
                "id": f"{leccion['id']}-teoria",
                "titulo": leccion["titulo"],
                "tipo": "teoria",
                "estado": estado_tp,
            })
            lecciones_resultado.append({
                "id": f"{leccion['id']}-practica",
                "titulo": leccion["titulo"],
                "tipo": "practica",
                "estado": estado_tp,
            })
            lecciones_resultado.append({
                "id": f"{leccion['id']}-prueba",
                "titulo": leccion["titulo"],
                "tipo": "prueba",
                "estado": estado_prueba,
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


def obtener_leccion_actual_usuario(usuario_id):
    """
    Devuelve el tile (teoría, práctica o prueba) que el usuario debería
    continuar ahora mismo: el primero en estado 'actual' recorriendo los
    bloques en orden. None si no hay ninguno (por ejemplo, todo completado).

    NOTA: esta es mi reconstrucción de la función que mencionaste haber
    agregado en tu propio curriculum.py -- no tengo el código original que
    escribiste. Si tu versión hacía algo distinto, dime y la ajusto.
    """
    bloques = obtener_progreso_usuario(usuario_id)
    for bloque in bloques:
        if not bloque["desbloqueado"]:
            continue
        for leccion in bloque["lecciones"]:
            if leccion["estado"] == "actual":
                return leccion
    return None