"""
Funciones relacionadas al usuario: crear cuenta, iniciar sesión,
actualizar racha y sumar puntos de experiencia (XP).
"""

import bcrypt
from datetime import date, timedelta
from backend.database.conexion import obtener_conexion


def crear_usuario(nombre, apellidoP, apellidoM, nombreUsuario, edad, contrasena):
    """
    Registra un nuevo usuario en la base de datos.
    La contraseña se guarda hasheada, nunca en texto plano.
    """
    contrasena_hash = bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt())

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuario (nombre, apellidoP, apellidoM, nombreUsuario, edad, contrasena_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, apellidoP, apellidoM, nombreUsuario, edad, contrasena_hash.decode("utf-8")))

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


def actualizar_racha_y_xp(usuario_id, xp_ganado=10):
    """
    Actualiza la racha de práctica y suma XP al usuario.
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

    hoy = date.today()
    ultima_practica = (
        date.fromisoformat(fila["ultima_practica"]) if fila["ultima_practica"] else None
    )

    if ultima_practica == hoy:
        nueva_racha = fila["racha_actual"]
    elif ultima_practica == hoy - timedelta(days=1):
        nueva_racha = fila["racha_actual"] + 1
    else:
        nueva_racha = 1

    nueva_racha_maxima = max(nueva_racha, fila["racha_maxima"])

    cursor.execute("""
        UPDATE usuario
        SET racha_actual = ?, racha_maxima = ?, ultima_practica = ?, puntos_xp = puntos_xp + ?
        WHERE id = ?
    """, (nueva_racha, nueva_racha_maxima, hoy.isoformat(), xp_ganado, usuario_id))

    conexion.commit()
    conexion.close()