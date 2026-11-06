import base64
import numpy as np
import cv2

from backend.database.curriculum import (
    sembrar_letras, obtener_progreso_usuario, obtener_leccion,
    obtener_siguiente_leccion_id, obtener_leccion_actual_usuario, XP_POR_LETRA, XP_BONO_PRUEBA
)
from backend.database.progreso import registrar_intento, registrar_prueba_aprobada
from backend.database.logros import obtener_perfil_extra
from backend.database import cuenta
from backend.correo import enviar_recuperacion
from backend.vision.evaluador import evaluar_frame, evaluar_secuencia

import time
from datetime import datetime
from flask import Flask, request, jsonify, url_for, render_template, session, redirect
from backend.database.conexion import inicializar_bd, obtener_conexion
from backend.database.usuarios import (
    crear_usuario, verificar_login, actualizar_racha_y_xp, reiniciar_racha_si_vencida
)

app = Flask(
    __name__,
    template_folder='frontend/html',
    static_folder='frontend'
)
app.secret_key = '1234'

# Inicializar las tablas de la BD al arrancar
inicializar_bd()
sembrar_letras()

# --- RUTAS DE AUTENTICACIÓN (API) ---

@app.route('/api/registro', methods=['POST'])
def api_registro():
    data = request.get_json() if request.is_json else request.form

    nombre = (data.get('nombre') or '').strip()
    apellidoP = (data.get('apellidoP') or '').strip()
    apellidoM = (data.get('apellidoM') or '').strip()
    nombreUsuario = (data.get('nombreUsuario') or '').strip()
    edad_raw = (data.get('edad') or '').strip() if isinstance(data.get('edad'), str) else data.get('edad')
    contrasena = data.get('contrasena') or ''
    correo = (data.get('correo') or '').strip()

    # --- Validaciones ---
    if not cuenta.correo_valido(correo):
        return jsonify({'ok': False, 'mensaje': 'Escribe un correo válido (lo usaremos para recuperar tu contraseña).'}), 400

    if not nombre or not apellidoP or not nombreUsuario or not contrasena:
        return jsonify({'ok': False, 'mensaje': 'Todos los campos obligatorios deben estar completos.'}), 400

    # La edad debe ser un número entero válido, no cualquier texto
    try:
        edad = int(edad_raw)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'mensaje': 'La edad debe ser un número válido.'}), 400

    if edad < 5 or edad > 120:
        return jsonify({'ok': False, 'mensaje': 'La edad debe estar entre 5 y 120 años.'}), 400

    # El nombre de usuario no debe contener espacios ni quedar vacío tras limpiar
    if ' ' in nombreUsuario or len(nombreUsuario) < 3:
        return jsonify({'ok': False, 'mensaje': 'El nombre de usuario debe tener al menos 3 caracteres y no contener espacios.'}), 400

    if len(contrasena) < 8:
        return jsonify({'ok': False, 'mensaje': 'La contraseña debe tener al menos 8 caracteres.'}), 400

    exito, mensaje = crear_usuario(
        nombre=nombre,
        apellidoP=apellidoP,
        apellidoM=apellidoM,
        nombreUsuario=nombreUsuario,
        edad=edad,
        contrasena=contrasena,
        correo=correo
    )

    if exito:
        return jsonify({'ok': True, 'mensaje': mensaje, 'redirect': '/login'})

    return jsonify({'ok': False, 'mensaje': mensaje}), 400

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() if request.is_json else request.form

    nombre_usuario = (data.get('nombreUsuario') or '').strip()
    contrasena = data.get('contrasena') or ''

    usuario = verificar_login(nombre_usuario, contrasena)

    if usuario:
        # sqlite3.Row permite acceder a las columnas por clave
        session['usuario_id'] = usuario['id']
        session['nombre'] = usuario['nombre']
        session['nombreUsuario'] = usuario['nombreUsuario']
        return jsonify({'ok': True, 'redirect': '/user-home'})

    return jsonify({'ok': False, 'mensaje': 'Usuario o contraseña incorrectos'}), 401


@app.route('/api/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/api/usuario-actual')
def usuario_actual():
    if 'usuario_id' not in session:
        return jsonify({'logged_in': False}), 401

    # Si pasó un día completo sin practicar, la racha regresa a 0 antes de mostrarla
    reiniciar_racha_si_vencida(session['usuario_id'])

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id, nombre, nombreUsuario, racha_actual, puntos_xp 
        FROM usuario WHERE id = ?
    """, (session['usuario_id'],))
    u = cursor.fetchone()
    conexion.close()

    if not u:
        return jsonify({'logged_in': False}), 401

    return jsonify({
        'logged_in': True,
        'nombre': u['nombre'],
        'nombreUsuario': u['nombreUsuario'],
        'racha': u['racha_actual'],
        'xp': u['puntos_xp']
    })


# --- RUTAS DE VISTAS (HTML) ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def vista_login():
    return render_template('login.html')

@app.route('/registro')
def vista_registro():
    return render_template('registro.html')

@app.route('/user-home')
def vista_user_home():
    if 'usuario_id' not in session:
        return redirect('/login')
    return render_template('user-home.html')

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_larga(texto):
    """'2026-11-04 16:16:05' -> '4 de noviembre de 2026' (si no se puede, devuelve el texto tal cual)."""
    try:
        fecha = datetime.strptime((texto or '')[:10], '%Y-%m-%d')
        return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"
    except (ValueError, TypeError):
        return texto or ''


@app.route('/perfil')
def vista_perfil():
    if 'usuario_id' not in session:
        return redirect('/login')
    return render_template('perfil.html')


@app.route('/api/perfil')
def api_perfil():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401

    # Si pasó un día completo sin practicar, la racha se muestra en 0
    reiniciar_racha_si_vencida(session['usuario_id'])

    conexion = obtener_conexion()
    u = conexion.execute("""
        SELECT nombre, apellidoP, apellidoM, nombreUsuario, fecha_registro,
               racha_actual, racha_maxima, puntos_xp
        FROM usuario WHERE id = ?
    """, (session['usuario_id'],)).fetchone()
    conexion.close()

    if not u:
        return jsonify({'ok': False}), 401

    nombre_completo = ' '.join(p for p in (u['nombre'], u['apellidoP'], u['apellidoM']) if p)

    return jsonify({
        'ok': True,
        'nombreCompleto': nombre_completo,
        'nombre': u['nombre'],
        'nombreUsuario': u['nombreUsuario'],
        'miembroDesde': _fecha_larga(u['fecha_registro']),
        'racha': u['racha_actual'],
        'rachaMaxima': u['racha_maxima'],
        'xp': u['puntos_xp'],
        **obtener_perfil_extra(session['usuario_id']),
    })


# --- CONFIGURACIÓN DE LA CUENTA ---

@app.route('/configuracion')
def vista_configuracion():
    if 'usuario_id' not in session:
        return redirect('/login')
    return render_template('configuracion.html')


@app.route('/api/configuracion')
def api_configuracion():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401
    reiniciar_racha_si_vencida(session['usuario_id'])
    datos = cuenta.obtener_datos(session['usuario_id'])
    if not datos:
        return jsonify({'ok': False}), 401
    return jsonify({'ok': True, **datos})


@app.route('/api/usuario/disponible')
def api_usuario_disponible():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401
    nombre = (request.args.get('nombre') or '').strip()
    if len(nombre) < 3 or ' ' in nombre:
        return jsonify({'ok': True, 'disponible': False, 'mensaje': 'Mínimo 3 caracteres y sin espacios.'})
    libre = cuenta.nombre_usuario_disponible(nombre, excepto_id=session['usuario_id'])
    return jsonify({'ok': True, 'disponible': libre,
                    'mensaje': 'Disponible' if libre else 'Ese usuario ya está en uso.'})


@app.route('/api/configuracion/perfil', methods=['POST'])
def api_configuracion_perfil():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401
    d = request.get_json(silent=True) or {}
    exito, mensaje = cuenta.actualizar_datos(
        session['usuario_id'], d.get('nombre'), d.get('apellidoP'), d.get('apellidoM'),
        d.get('edad'), d.get('nombreUsuario'), d.get('correo')
    )
    if not exito:
        return jsonify({'ok': False, 'mensaje': mensaje}), 400
    datos = cuenta.obtener_datos(session['usuario_id'])
    session['nombre'] = datos['nombre']
    session['nombreUsuario'] = datos['nombreUsuario']
    return jsonify({'ok': True, 'mensaje': mensaje, **datos})


@app.route('/api/configuracion/contrasena', methods=['POST'])
def api_configuracion_contrasena():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401
    d = request.get_json(silent=True) or {}
    exito, mensaje = cuenta.cambiar_contrasena(session['usuario_id'], d.get('actual'), d.get('nueva'))
    return jsonify({'ok': exito, 'mensaje': mensaje}), (200 if exito else 400)


@app.route('/api/configuracion/reiniciar-progreso', methods=['POST'])
def api_reiniciar_progreso():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401
    d = request.get_json(silent=True) or {}
    if not cuenta.verificar_contrasena(session['usuario_id'], d.get('contrasena')):
        return jsonify({'ok': False, 'mensaje': 'La contraseña no es correcta.'}), 400
    cuenta.reiniciar_progreso(session['usuario_id'])
    return jsonify({'ok': True, 'mensaje': 'Tu progreso se reinició.'})


@app.route('/api/configuracion/eliminar-cuenta', methods=['POST'])
def api_eliminar_cuenta():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401
    d = request.get_json(silent=True) or {}
    if not cuenta.verificar_contrasena(session['usuario_id'], d.get('contrasena')):
        return jsonify({'ok': False, 'mensaje': 'La contraseña no es correcta.'}), 400
    cuenta.eliminar_cuenta(session['usuario_id'])
    session.clear()
    return jsonify({'ok': True, 'redirect': '/login'})


# --- RECUPERAR CONTRASEÑA ---

_SOLICITUDES_RECUPERAR = {}


def _limitar(clave, maximo=5, ventana=900):
    """Máximo 'maximo' solicitudes por 'ventana' segundos para la misma IP."""
    ahora_ts = time.time()
    recientes = [t for t in _SOLICITUDES_RECUPERAR.get(clave, []) if ahora_ts - t < ventana]
    if len(recientes) >= maximo:
        _SOLICITUDES_RECUPERAR[clave] = recientes
        return False
    recientes.append(ahora_ts)
    _SOLICITUDES_RECUPERAR[clave] = recientes
    return True


@app.route('/olvide')
def vista_olvide():
    return render_template('olvide.html')


@app.route('/api/recuperar', methods=['POST'])
def api_recuperar():
    d = request.get_json(silent=True) or {}
    correo = (d.get('correo') or '').strip()
    if not cuenta.correo_valido(correo):
        return jsonify({'ok': False, 'mensaje': 'Escribe un correo válido.'}), 400
    if not _limitar(request.remote_addr or 'desconocida'):
        return jsonify({'ok': False, 'mensaje': 'Demasiados intentos. Espera unos minutos.'}), 429

    resultado = cuenta.crear_token_recuperacion(correo)
    if resultado:
        token, nombre = resultado
        enlace = url_for('vista_restablecer', _external=True) + '?token=' + token
        enviar_recuperacion(correo, nombre, enlace)

    # Misma respuesta exista o no el correo, para no revelar quién tiene cuenta
    return jsonify({'ok': True, 'mensaje': 'Si ese correo está registrado, te enviamos un enlace para restablecer tu contraseña. Revisa también el spam.'})


@app.route('/restablecer')
def vista_restablecer():
    token = request.args.get('token', '')
    return render_template('restablecer.html', token=token, valido=cuenta.token_valido(token))


@app.route('/api/restablecer', methods=['POST'])
def api_restablecer():
    d = request.get_json(silent=True) or {}
    exito, mensaje = cuenta.restablecer_contrasena(d.get('token', ''), d.get('contrasena', ''))
    return jsonify({'ok': exito, 'mensaje': mensaje}), (200 if exito else 400)


@app.route('/nosotros')
def vista_nosotros():
    return render_template('Nosotros.html')

@app.route('/privacidad')
def vista_privacidad():
    return render_template('privacidad.html')

@app.route('/terminos')
def vista_terminos():
    return render_template('terminos.html')

@app.route('/api/progreso')
def api_progreso():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401

    usuario_id = session['usuario_id']
    bloques = obtener_progreso_usuario(usuario_id)
    leccion_actual = obtener_leccion_actual_usuario(usuario_id)

    url_continuar = "/user-home"
    if leccion_actual:
        # Extraer el ID base (remover '-teoria', '-practica' o '-prueba' para armar la URL)
        raw_id = leccion_actual["id"]
        if raw_id.endswith("-teoria"):
            base_id = raw_id[:-7]
            url_continuar = f"/teoria?leccion={base_id}"
        elif raw_id.endswith("-practica"):
            base_id = raw_id[:-9]
            url_continuar = f"/practica?leccion={base_id}"
        elif raw_id.endswith("-prueba"):
            base_id = raw_id[:-7]
            url_continuar = f"/prueba?leccion={base_id}"

    return jsonify({
        'ok': True,
        'bloques': bloques,
        'url_continuar': url_continuar
    })

@app.route('/teoria')
def vista_teoria():
    if 'usuario_id' not in session:
        return redirect('/login')
    leccion_id = request.args.get('leccion', '')
    leccion = obtener_leccion(leccion_id)
    if leccion is None:
        return redirect('/user-home')
    return render_template('teoria.html', leccion=leccion)

@app.route('/practica')
def vista_practica():
    if 'usuario_id' not in session:
        return redirect('/login')

    leccion_id = request.args.get('leccion', '')
    leccion = obtener_leccion(leccion_id)
    if leccion is None:
        return redirect('/user-home')

    # Al terminar la Práctica, lo siguiente es la Prueba de ESTA MISMA lección
    # (no la siguiente lección todavía -- eso solo pasa al aprobar la prueba).
    siguiente_url = f"/prueba?leccion={leccion_id}"

    return render_template('practica.html', leccion=leccion, siguiente_leccion=siguiente_url)


@app.route('/prueba')
def vista_prueba():
    if 'usuario_id' not in session:
        return redirect('/login')
    leccion_id = request.args.get('leccion', '')
    leccion = obtener_leccion(leccion_id, session['usuario_id'])   # palabras propias de este usuario
    if leccion is None:
        return redirect('/user-home')

    siguiente_id = obtener_siguiente_leccion_id(leccion_id)
    siguiente_url = f"/teoria?leccion={siguiente_id}" if siguiente_id else "/user-home"

    return render_template('prueba.html', leccion=leccion, siguiente_leccion=siguiente_url)


@app.route('/api/prueba/aprobar', methods=['POST'])
def api_prueba_aprobar():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401

    data = request.get_json()
    leccion_id = (data.get('leccion_id') or '').strip()

    if not leccion_id:
        return jsonify({'ok': False, 'mensaje': 'Falta leccion_id.'}), 400

    registrar_prueba_aprobada(session['usuario_id'], leccion_id)
    actualizar_racha_y_xp(session['usuario_id'], xp_ganado=XP_BONO_PRUEBA)
    return jsonify({'ok': True})


@app.route('/api/teoria/completar', methods=['POST'])
def api_teoria_completar():
    """Terminar la teoría de una lección cuenta como actividad del día (racha), sin XP."""
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401
    actualizar_racha_y_xp(session['usuario_id'], xp_ganado=0)
    return jsonify({'ok': True})


@app.route('/api/practica/evaluar', methods=['POST'])
def api_practica_evaluar():
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401

    data = request.get_json()
    letra_objetivo = (data.get('letra') or '').strip().upper()
    imagen_b64 = data.get('imagen', '')

    if not letra_objetivo or not imagen_b64:
        return jsonify({'ok': False, 'mensaje': 'Faltan datos.'}), 400

    try:
        if ',' in imagen_b64:
            imagen_b64 = imagen_b64.split(',', 1)[1]
        binario = base64.b64decode(imagen_b64)
        arreglo = np.frombuffer(binario, dtype=np.uint8)
        imagen_bgr = cv2.imdecode(arreglo, cv2.IMREAD_COLOR)
    except Exception:
        return jsonify({'ok': False, 'mensaje': 'No se pudo leer la imagen.'}), 400

    if imagen_bgr is None:
        return jsonify({'ok': False, 'mensaje': 'Imagen inválida.'}), 400

    resultado = evaluar_frame(imagen_bgr, letra_objetivo, clave_sesion=str(session['usuario_id']))
    _registrar_resultado(resultado, letra_objetivo)
    return jsonify({'ok': True, **resultado})


def _registrar_resultado(resultado, letra_objetivo):
    """Guarda el intento (y da XP si acertó) cuando hubo una predicción real."""
    hay_prediccion = (
        resultado['mano_detectada']
        and resultado['modelo_listo']
        and resultado.get('prediccion') is not None
    )
    if not hay_prediccion:
        return

    resultado_texto = 'correcto' if resultado['correcto'] else 'incorrecto'
    registrar_intento(session['usuario_id'], letra_objetivo, resultado_texto)
    if resultado_texto == 'correcto':
        actualizar_racha_y_xp(session['usuario_id'], xp_ganado=XP_POR_LETRA)


MAX_FRAMES_CLIP = 80


@app.route('/api/practica/evaluar-secuencia', methods=['POST'])
def api_practica_evaluar_secuencia():
    """Letras con movimiento: el navegador graba ~2 s y manda todos los frames juntos."""
    if 'usuario_id' not in session:
        return jsonify({'ok': False}), 401

    data = request.get_json(silent=True) or {}
    letra_objetivo = (data.get('letra') or '').strip().upper()
    frames_b64 = data.get('frames') or []

    if not letra_objetivo or not isinstance(frames_b64, list) or not frames_b64:
        return jsonify({'ok': False, 'mensaje': 'Faltan datos.'}), 400
    if len(frames_b64) > MAX_FRAMES_CLIP:
        return jsonify({'ok': False, 'mensaje': 'Clip demasiado largo.'}), 400

    frames_bgr = []
    try:
        for imagen_b64 in frames_b64:
            if ',' in imagen_b64:
                imagen_b64 = imagen_b64.split(',', 1)[1]
            arreglo = np.frombuffer(base64.b64decode(imagen_b64), dtype=np.uint8)
            frame = cv2.imdecode(arreglo, cv2.IMREAD_COLOR)
            if frame is not None:
                frames_bgr.append(frame)
    except Exception:
        return jsonify({'ok': False, 'mensaje': 'No se pudo leer el clip.'}), 400

    if not frames_bgr:
        return jsonify({'ok': False, 'mensaje': 'Clip inválido.'}), 400

    resultado = evaluar_secuencia(frames_bgr, letra_objetivo)
    _registrar_resultado(resultado, letra_objetivo)
    return jsonify({'ok': True, **resultado})

# --- INICIO DE LA APLICACIÓN ---
if __name__ == '__main__':
    app.run(debug=True)