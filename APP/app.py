import base64
import numpy as np
import cv2

from backend.database.curriculum import (
    sembrar_letras, obtener_progreso_usuario, obtener_leccion, 
    obtener_siguiente_leccion_id, obtener_leccion_actual_usuario
)
from backend.database.progreso import registrar_intento
from backend.vision.evaluador import evaluar_frame

from flask import Flask, request, jsonify, url_for, render_template, session, redirect
from backend.database.conexion import inicializar_bd, obtener_conexion
from backend.database.usuarios import crear_usuario, verificar_login

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

    # --- Validaciones ---
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
        contrasena=contrasena
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
        # Extraer el ID base (remover '-teoria' o '-practica' para armar la URL)
        raw_id = leccion_actual["id"]
        if raw_id.endswith("-teoria"):
            base_id = raw_id[:-7]
            url_continuar = f"/teoria?leccion={base_id}"
        elif raw_id.endswith("-practica"):
            base_id = raw_id[:-9]
            url_continuar = f"/practica?leccion={base_id}"

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
    
    # Si obtener_siguiente_leccion_id retorna None o vacío, enviamos /user-home
    siguiente_id = obtener_siguiente_leccion_id(leccion_id)
    siguiente_url = f"/practica?leccion={siguiente_id}" if siguiente_id else "/user-home"

    return render_template('practica.html', leccion=leccion, siguiente_leccion=siguiente_url)


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

    resultado = evaluar_frame(imagen_bgr, letra_objetivo)

    if resultado['mano_detectada'] and resultado['modelo_listo']:
        resultado_texto = 'correcto' if resultado['correcto'] else 'incorrecto'
        registrar_intento(session['usuario_id'], letra_objetivo, resultado_texto)

    return jsonify({'ok': True, **resultado})

# --- INICIO DE LA APLICACIÓN ---
if __name__ == '__main__':
    app.run(debug=True)