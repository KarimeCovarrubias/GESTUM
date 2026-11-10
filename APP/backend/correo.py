"""
Envío de correos (recuperación de contraseña).

Configura el correo de una de estas dos formas.

backend/correo_config.py y escribir ahí el correo y la contraseña de aplicación.
Ese archivo está en .gitignore para que NO se suba a GitHub.

Si no están configuradas, el enlace se imprime en la consola del servidor
(modo desarrollo) en vez de enviarse.

"""

import os
import smtplib
import threading
from email.message import EmailMessage


def _credenciales():
    """Variables de entorno primero; si no, el archivo local backend/correo_config.py."""
    usuario = os.environ.get("GESTUM_SMTP_USUARIO")
    clave = os.environ.get("GESTUM_SMTP_CLAVE")
    if usuario and clave:
        return usuario, clave
    try:
        from backend import correo_config   # archivo local, NO se sube a GitHub
        return getattr(correo_config, "USUARIO", None), getattr(correo_config, "CLAVE", None)
    except ImportError:
        return None, None


def _enviar(destino, asunto, cuerpo):
    usuario, clave = _credenciales()
    clave = (clave or "").replace(" ", "")   # Google la muestra con espacios

    if not usuario or not clave:
        print("\n[GESTUM · correo sin configurar: modo desarrollo]")
        print(f"Para: {destino}\nAsunto: {asunto}\n{cuerpo}\n")
        return

    mensaje = EmailMessage()
    mensaje["From"] = f"GESTUM <{usuario}>"
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    try:
        host = os.environ.get("GESTUM_SMTP_HOST", "smtp.gmail.com")
        puerto = int(os.environ.get("GESTUM_SMTP_PUERTO", "587"))
        with smtplib.SMTP(host, puerto, timeout=15) as servidor:
            servidor.starttls()
            servidor.login(usuario, clave)
            servidor.send_message(mensaje)
    except Exception as error:
        print(f"[GESTUM · no se pudo enviar el correo a {destino}]: {error}")


def enviar_recuperacion(destino, nombre, enlace):
    cuerpo = (
        f"Hola {nombre},\n\n"
        "Recibimos una solicitud para restablecer tu contraseña de GESTUM.\n"
        f"Entra a este enlace (vale 10 minutos y se usa una sola vez):\n\n{enlace}\n\n"
        "Si no fuiste tú, ignora este mensaje: tu contraseña no cambiará.\n"
    )
    # En un hilo aparte para que la respuesta al usuario no espere al servidor de correo
    threading.Thread(target=_enviar, args=(destino, "Restablece tu contraseña de GESTUM", cuerpo), daemon=True).start()