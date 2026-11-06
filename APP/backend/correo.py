"""
Envío de correos (recuperación de contraseña).

Configura estas variables de entorno antes de iniciar la app. Con Gmail hace
falta una "contraseña de aplicación" (Cuenta de Google > Seguridad > Verificación
en dos pasos > Contraseñas de aplicaciones), NO tu contraseña normal:

    GESTUM_SMTP_USUARIO   tu_correo@gmail.com
    GESTUM_SMTP_CLAVE     la contraseña de aplicación de 16 letras
    GESTUM_SMTP_HOST      (opcional) por defecto smtp.gmail.com
    GESTUM_SMTP_PUERTO    (opcional) por defecto 587

Si no están configuradas, el enlace se imprime en la consola del servidor
(modo desarrollo) en vez de enviarse.

"""

import os
import smtplib
import threading
from email.message import EmailMessage


def _enviar(destino, asunto, cuerpo):
    usuario = os.environ.get("GESTUM_SMTP_USUARIO")
    clave = os.environ.get("GESTUM_SMTP_CLAVE")

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
        f"Entra a este enlace (vale 45 minutos y se usa una sola vez):\n\n{enlace}\n\n"
        "Si no fuiste tú, ignora este mensaje: tu contraseña no cambiará.\n"
    )
    # En un hilo aparte para que la respuesta al usuario no espere al servidor de correo
    threading.Thread(target=_enviar, args=(destino, "Restablece tu contraseña de GESTUM", cuerpo), daemon=True).start()