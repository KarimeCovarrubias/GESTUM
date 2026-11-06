"""
Gestión de la cuenta: editar datos, cambiar contraseña, recuperarla por correo,
reiniciar el progreso y eliminar la cuenta.

"""

import hashlib
import re
import secrets
from datetime import timedelta

import bcrypt

from backend.database.conexion import obtener_conexion
from backend.database.tiempo import ahora

MINUTOS_VALIDEZ_TOKEN = 45
CORREO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def correo_valido(correo):
    return bool(correo) and len(correo) <= 120 and bool(CORREO_RE.match(correo))


def _hash(contrasena):
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _coincide(contrasena, hash_guardado):
    if isinstance(hash_guardado, str):
        hash_guardado = hash_guardado.encode("utf-8")
    return bcrypt.checkpw(contrasena.encode("utf-8"), hash_guardado)


# ---------- Datos de la cuenta ----------

def obtener_datos(usuario_id):
    conexion = obtener_conexion()
    u = conexion.execute("""
        SELECT nombre, apellidoP, apellidoM, nombreUsuario, edad, correo, racha_actual, puntos_xp
        FROM usuario WHERE id = ?
    """, (usuario_id,)).fetchone()
    conexion.close()
    return dict(u) if u else None


def nombre_usuario_disponible(nombre, excepto_id=None):
    conexion = obtener_conexion()
    fila = conexion.execute(
        "SELECT id FROM usuario WHERE lower(nombreUsuario) = lower(?)", (nombre,)
    ).fetchone()
    conexion.close()
    return fila is None or fila["id"] == excepto_id


def actualizar_datos(usuario_id, nombre, apellidoP, apellidoM, edad, nombreUsuario, correo):
    """Valida y guarda nombre, apellidos, edad, usuario (único) y correo (único)."""
    nombre, apellidoP = (nombre or "").strip(), (apellidoP or "").strip()
    apellidoM = (apellidoM or "").strip()
    nombreUsuario, correo = (nombreUsuario or "").strip(), (correo or "").strip()

    if not nombre or not apellidoP:
        return False, "El nombre y el apellido paterno son obligatorios."
    try:
        edad = int(edad)
    except (TypeError, ValueError):
        return False, "La edad debe ser un número válido."
    if edad < 5 or edad > 120:
        return False, "La edad debe estar entre 5 y 120 años."
    if ' ' in nombreUsuario or len(nombreUsuario) < 3:
        return False, "El usuario debe tener al menos 3 caracteres y no contener espacios."
    if not correo_valido(correo):
        return False, "Escribe un correo válido."
    if not nombre_usuario_disponible(nombreUsuario, excepto_id=usuario_id):
        return False, "Ese nombre de usuario ya está en uso."

    conexion = obtener_conexion()
    try:
        conexion.execute("""
            UPDATE usuario
            SET nombre = ?, apellidoP = ?, apellidoM = ?, edad = ?, nombreUsuario = ?, correo = ?
            WHERE id = ?
        """, (nombre, apellidoP, apellidoM, edad, nombreUsuario, correo, usuario_id))
        conexion.commit()
        return True, "Cambios guardados."
    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            if "correo" in str(error):
                return False, "Ese correo ya está registrado en otra cuenta."
            return False, "Ese nombre de usuario ya está en uso."
        return False, f"Ocurrió un error: {error}"
    finally:
        conexion.close()


# ---------- Contraseña ----------

def verificar_contrasena(usuario_id, contrasena):
    conexion = obtener_conexion()
    u = conexion.execute("SELECT contrasena_hash FROM usuario WHERE id = ?", (usuario_id,)).fetchone()
    conexion.close()
    return bool(u) and _coincide(contrasena or "", u["contrasena_hash"])


def cambiar_contrasena(usuario_id, actual, nueva):
    if not verificar_contrasena(usuario_id, actual):
        return False, "La contraseña actual no es correcta."
    if len(nueva or "") < 8:
        return False, "La contraseña nueva debe tener al menos 8 caracteres."
    conexion = obtener_conexion()
    conexion.execute("UPDATE usuario SET contrasena_hash = ? WHERE id = ?", (_hash(nueva), usuario_id))
    conexion.commit()
    conexion.close()
    return True, "Contraseña actualizada."


# ---------- Recuperar contraseña (enlace por correo) ----------

def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_token_recuperacion(correo):
    """Devuelve (token, nombre) si el correo existe; si no, None. Reemplaza tokens anteriores."""
    conexion = obtener_conexion()
    u = conexion.execute(
        "SELECT id, nombre FROM usuario WHERE lower(correo) = lower(?)", (correo,)
    ).fetchone()
    if not u:
        conexion.close()
        return None

    token = secrets.token_urlsafe(32)
    expira = (ahora() + timedelta(minutes=MINUTOS_VALIDEZ_TOKEN)).strftime("%Y-%m-%d %H:%M:%S")
    conexion.execute("DELETE FROM tokens_recuperacion WHERE usuario_id = ?", (u["id"],))
    conexion.execute(
        "INSERT INTO tokens_recuperacion (usuario_id, token_hash, expira) VALUES (?, ?, ?)",
        (u["id"], _hash_token(token), expira)
    )
    conexion.commit()
    conexion.close()
    return token, u["nombre"]


def _usuario_de_token(conexion, token):
    if not token:
        return None
    fila = conexion.execute(
        "SELECT usuario_id, expira FROM tokens_recuperacion WHERE token_hash = ?",
        (_hash_token(token),)
    ).fetchone()
    if not fila or fila["expira"] < ahora().strftime("%Y-%m-%d %H:%M:%S"):
        return None
    return fila["usuario_id"]


def token_valido(token):
    conexion = obtener_conexion()
    valido = _usuario_de_token(conexion, token) is not None
    conexion.close()
    return valido


def restablecer_contrasena(token, nueva):
    if len(nueva or "") < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    conexion = obtener_conexion()
    usuario_id = _usuario_de_token(conexion, token)
    if usuario_id is None:
        conexion.close()
        return False, "El enlace no es válido o ya venció. Pide uno nuevo."
    conexion.execute("UPDATE usuario SET contrasena_hash = ? WHERE id = ?", (_hash(nueva), usuario_id))
    conexion.execute("DELETE FROM tokens_recuperacion WHERE usuario_id = ?", (usuario_id,))  # un solo uso
    conexion.commit()
    conexion.close()
    return True, "Contraseña actualizada. Ya puedes iniciar sesión."


# ---------- Zona delicada ----------

def reiniciar_progreso(usuario_id):
    """Borra intentos, progreso, pruebas aprobadas, XP y racha. La cuenta se conserva."""
    conexion = obtener_conexion()
    for tabla in ("intentos", "progreso", "pruebas_aprobadas"):
        conexion.execute(f"DELETE FROM {tabla} WHERE usuario_id = ?", (usuario_id,))
    conexion.execute("""
        UPDATE usuario
        SET puntos_xp = 0, racha_actual = 0, racha_maxima = 0, ultima_practica = NULL
        WHERE id = ?
    """, (usuario_id,))
    conexion.commit()
    conexion.close()


def eliminar_cuenta(usuario_id):
    conexion = obtener_conexion()
    conexion.execute("DELETE FROM usuario WHERE id = ?", (usuario_id,))  # el resto se borra en cascada
    conexion.commit()
    conexion.close()