"""
Funciones relacionadas al progreso del usuario: registrar cada intento
de una seña y consultar el avance (para pantallas de práctica y perfil).
"""

from backend.database.conexion import obtener_conexion


def obtener_o_crear_letra(letra, tipo="estatica", dificultad="facil", imagen_referencia=None):
    """
    Busca una letra en el catálogo por su texto (ej. "A") y devuelve su id.
    Si no existe todavía, la crea. Así nunca trabajamos con texto libre
    directamente en INTENTOS o PROGRESO, solo con el id.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT id FROM letras WHERE letra = ?", (letra,))
    fila = cursor.fetchone()

    if fila is not None:
        conexion.close()
        return fila["id"]

    cursor.execute("""
        INSERT INTO letras (letra, tipo, dificultad, imagen_referencia)
        VALUES (?, ?, ?, ?)
    """, (letra, tipo, dificultad, imagen_referencia))

    conexion.commit()
    letra_id = cursor.lastrowid
    conexion.close()
    return letra_id


def registrar_intento(usuario_id, letra, resultado):
    """
    Registra un intento individual (correcto/incorrecto) para una letra,
    y actualiza la tabla resumen PROGRESO al mismo tiempo.

    resultado debe ser el texto 'correcto' o 'incorrecto'.
    """
    if resultado not in ("correcto", "incorrecto"):
        raise ValueError("resultado debe ser 'correcto' o 'incorrecto'")

    letra_id = obtener_o_crear_letra(letra)

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # 1. Insertar el intento en el historial detallado
    cursor.execute("""
        INSERT INTO intentos (usuario_id, letra_id, resultado)
        VALUES (?, ?, ?)
    """, (usuario_id, letra_id, resultado))

    # 2. Actualizar (o crear) la fila resumen en PROGRESO para esa letra
    es_correcto = 1 if resultado == "correcto" else 0

    cursor.execute("""
        INSERT INTO progreso (usuario_id, letra_id, veces_practicadas, veces_correctas)
        VALUES (?, ?, 1, ?)
        ON CONFLICT (usuario_id, letra_id) DO UPDATE SET
            veces_practicadas = veces_practicadas + 1,
            veces_correctas = veces_correctas + excluded.veces_correctas
    """, (usuario_id, letra_id, es_correcto))

    conexion.commit()
    conexion.close()


def obtener_detalle_progreso_usuario(usuario_id):
    """
    Devuelve el progreso resumido del usuario, una fila por letra practicada:
    letra, veces_practicadas, veces_correctas y porcentaje de acierto.

    Útil para la pantalla de perfil (ej. graficar aciertos por letra).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            l.letra AS letra,
            p.veces_practicadas AS veces_practicadas,
            p.veces_correctas AS veces_correctas
        FROM progreso p
        JOIN letras l ON l.id = p.letra_id
        WHERE p.usuario_id = ?
        ORDER BY l.letra
    """, (usuario_id,))

    filas = cursor.fetchall()
    conexion.close()

    resultado = []
    for fila in filas:
        porcentaje = (
            round(fila["veces_correctas"] / fila["veces_practicadas"] * 100, 1)
            if fila["veces_practicadas"] > 0 else 0.0
        )
        resultado.append({
            "letra": fila["letra"],
            "veces_practicadas": fila["veces_practicadas"],
            "veces_correctas": fila["veces_correctas"],
            "porcentaje_acierto": porcentaje
        })

    return resultado


def obtener_historial_intentos(usuario_id, letra=None, limite=50):
    """
    Devuelve el historial de intentos más recientes del usuario,
    opcionalmente filtrado por una letra específica.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if letra:
        cursor.execute("""
            SELECT l.letra AS letra, i.resultado AS resultado, i.fecha_hora AS fecha_hora
            FROM intentos i
            JOIN letras l ON l.id = i.letra_id
            WHERE i.usuario_id = ? AND l.letra = ?
            ORDER BY i.fecha_hora DESC
            LIMIT ?
        """, (usuario_id, letra, limite))
    else:
        cursor.execute("""
            SELECT l.letra AS letra, i.resultado AS resultado, i.fecha_hora AS fecha_hora
            FROM intentos i
            JOIN letras l ON l.id = i.letra_id
            WHERE i.usuario_id = ?
            ORDER BY i.fecha_hora DESC
            LIMIT ?
        """, (usuario_id, limite))

    filas = cursor.fetchall()
    conexion.close()
    return [dict(fila) for fila in filas]