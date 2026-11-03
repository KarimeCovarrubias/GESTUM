"""
Funciones relacionadas al usuario: crear cuenta, iniciar sesión,
actualizar racha y sumar puntos de experiencia (XP).
"""

import bcrypt
from datetime import date, timedelta
from backend.database.conexion import obtener_conexion
from backend.database.tiempo import hoy, ahora_texto


def crear_usuario(nombre, apellidoP, apellidoM, nombreUsuario, edad, contrasena):
    """
    Registra un nuevo usuario en la base de datos.
    La contraseña se guarda hasheada, nunca en texto plano.
    """
    contrasena_hash = bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt())
    # Hora oficial de GESTUM (UTC-7), guardada explícitamente: no depende de la
    # zona horaria de la computadora ni del datetime('now') de SQLite (que es UTC).
    fecha_registro = ahora_texto()

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuario (nombre, apellidoP, apellidoM, nombreUsuario, edad, contrasena_hash, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre, apellidoP, apellidoM, nombreUsuario, edad, contrasena_hash.decode("utf-8"), fecha_registro))

        conexion.commit()
        return True, "Cuenta creada correctamente."

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return False, "Ese nombre de usuario ya está en uso."
        return False, f"Ocurrió un error al crear la cuenta: {error}"

    finally:
        conexion.close()


def verificar_login(nombreUsuario, contrasena):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM usuario WHERE nombreUsuario = ?", (nombreUsuario,))
    usuario = cursor.fetchone()
    conexion.close()

    if usuario is None:
        return None

    # Asegurar conversión a bytes antes de verificar con bcrypt
    hash_almacenado = usuario["contrasena_hash"]
    if isinstance(hash_almacenado, str):
        hash_almacenado = hash_almacenado.encode("utf-8")

    contrasena_correcta = bcrypt.checkpw(
        contrasena.encode("utf-8"),
        hash_almacenado
    )

    return usuario if contrasena_correcta else None


def actualizar_nombre_usuario(usuario_id, nuevo_nombreUsuario):
    """
    Permite cambiar el nombre de usuario (sigue siendo único).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "UPDATE usuario SET nombreUsuario = ? WHERE id = ?",
            (nuevo_nombreUsuario, usuario_id)
        )
        conexion.commit()
        return True, "Nombre de usuario actualizado."

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return False, "Ese nombre de usuario ya está en uso."
        return False, f"Ocurrió un error: {error}"

    finally:
        conexion.close()


def reiniciar_racha_si_vencida(usuario_id):
    """
    Regla de la racha (como Duolingo), con días completos en UTC-7
    (de 00:00 a 23:59):
      - Practicó HOY o AYER  -> la racha sigue viva (si fue ayer, todavía
        puede sumarla hoy).
      - Su última práctica fue antes de ayer (pasó un día completo sin
        hacer ninguna lección) -> la racha regresa a 0.

    Se llama cada vez que se consulta el usuario, para que la racha se vea
    en 0 aunque todavía no haya vuelto a practicar. Devuelve la racha vigente.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT racha_actual, ultima_practica FROM usuario WHERE id = ?", (usuario_id,)
    )
    fila = cursor.fetchone()
    if fila is None:
        conexion.close()
        return 0

    racha = fila["racha_actual"]
    ultima = date.fromisoformat(fila["ultima_practica"]) if fila["ultima_practica"] else None

    if racha > 0 and (ultima is None or ultima < hoy() - timedelta(days=1)):
        cursor.execute("UPDATE usuario SET racha_actual = 0 WHERE id = ?", (usuario_id,))
        conexion.commit()
        racha = 0

    conexion.close()
    return racha


def actualizar_racha_y_xp(usuario_id, xp_ganado=10):
    """
    Registra actividad de HOY (UTC-7): suma la racha si es el primer día de
    práctica después de ayer, la mantiene si ya practicó hoy, o la reinicia
    en 1 si se saltó uno o más días. Suma también el XP.

    Para avisar "hizo una lección" sin dar XP (por ejemplo al terminar una
    teoría) se llama con xp_ganado=0.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT racha_actual, racha_maxima, ultima_practica FROM usuario WHERE id = ?",
        (usuario_id,)
    )
    fila = cursor.fetchone()

    if fila is None:
        conexion.close()
        return

    fecha_hoy = hoy()
    ultima_practica = (
        date.fromisoformat(fila["ultima_practica"]) if fila["ultima_practica"] else None
    )

    if ultima_practica == fecha_hoy:
        nueva_racha = max(fila["racha_actual"], 1)
    elif ultima_practica == fecha_hoy - timedelta(days=1):
        nueva_racha = fila["racha_actual"] + 1
    else:
        nueva_racha = 1

    nueva_racha_maxima = max(nueva_racha, fila["racha_maxima"])

    cursor.execute("""
        UPDATE usuario
        SET racha_actual = ?, racha_maxima = ?, ultima_practica = ?, puntos_xp = puntos_xp + ?
        WHERE id = ?
    """, (nueva_racha, nueva_racha_maxima, fecha_hoy.isoformat(), xp_ganado, usuario_id))

    conexion.commit()
    conexion.close()