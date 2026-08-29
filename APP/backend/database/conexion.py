"""
Módulo de conexión a la base de datos.
Crea el archivo usuarios.db y todas las tablas si no existen todavía.
"""

import sqlite3
import os

# Ruta donde vivirá el archivo de la base de datos
RUTA_BD = os.path.join(os.path.dirname(__file__), "..", "datos", "usuarios.db")


def obtener_conexion():
    """
    Devuelve una conexión a la base de datos SQLite.
    Se asegura de que la carpeta 'datos' exista antes de conectar.
    """
    carpeta = os.path.dirname(RUTA_BD)
    os.makedirs(carpeta, exist_ok=True)

    conexion = sqlite3.connect(RUTA_BD)
    # Permite acceder a las columnas por nombre (fila["columna"]) en vez de solo por índice
    conexion.row_factory = sqlite3.Row
    # Activa las llaves foráneas (SQLite las trae desactivadas por defecto)
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_bd():
    """
    Crea todas las tablas del proyecto si todavía no existen.
    Se debe llamar una vez al arrancar la app (por ejemplo, desde app.py).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellidoP TEXT NOT NULL,
            apellidoM TEXT,
            nombreUsuario TEXT NOT NULL UNIQUE,
            edad INTEGER,
            contrasena_hash TEXT NOT NULL,
            fecha_registro TEXT NOT NULL DEFAULT (datetime('now')),
            racha_actual INTEGER NOT NULL DEFAULT 0,
            racha_maxima INTEGER NOT NULL DEFAULT 0,
            ultima_practica TEXT,
            puntos_xp INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Catálogo de letras (para no repetir texto libre y poder agregar más datos después)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS letras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letra TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL DEFAULT 'estatica',
            dificultad TEXT NOT NULL DEFAULT 'facil',
            imagen_referencia TEXT
        )
    """)

    # Historial detallado de cada intento del usuario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS intentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            letra_id INTEGER NOT NULL,
            resultado TEXT NOT NULL CHECK (resultado IN ('correcto', 'incorrecto')),
            fecha_hora TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
            FOREIGN KEY (letra_id) REFERENCES letras (id) ON DELETE CASCADE
        )
    """)

    # Tabla resumen de progreso por usuario y letra (se actualiza junto con cada intento)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progreso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            letra_id INTEGER NOT NULL,
            veces_practicadas INTEGER NOT NULL DEFAULT 0,
            veces_correctas INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
            FOREIGN KEY (letra_id) REFERENCES letras (id) ON DELETE CASCADE,
            UNIQUE (usuario_id, letra_id)
        )
    """)

    conexion.commit()
    conexion.close()


if __name__ == "__main__":
    # Permite correr este archivo directamente para crear la BD manualmente:
    # python database/conexion.py
    inicializar_bd()
    print(f"Base de datos inicializada correctamente en: {os.path.abspath(RUTA_BD)}")