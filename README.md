# GESTUM

Aplicación web para aprender el alfabeto de la **Lengua de Señas Mexicana (LSM)** con ayuda de un modelo de inteligencia artificial que reconoce tu seña con la cámara.

## Descripción

GESTUM guía a la persona por lecciones cortas: primero ve la teoría de cada letra (imagen y video de referencia), después practica frente a la cámara y finalmente presenta una prueba. El modelo detecta la mano en tiempo real y le dice si la seña es correcta, sin necesidad de un tutor.

## Objetivo

Ayudar a las personas a aprender LSM de una manera más fácil y didáctica con IA, permitiendo que sean autodidactas y sin tutores.

## Características

- **Alfabeto completo de LSM (28 letras):** 21 estáticas y 7 con movimiento (J, K, LL, Ñ, Q, X, Z).
- **Lecciones en tres pasos:** teoría, práctica con cámara y prueba. Aprobar la prueba desbloquea la siguiente lección.
- **Reconocimiento en tiempo real** con MediaPipe y scikit-learn. Funciona con mano derecha o izquierda.
- **Progreso y motivación:** XP, racha diaria y logros.
- **Cuentas de usuario:** registro con correo, inicio de sesión y perfil.
- **Configuración:** editar datos personales, cambiar contraseña, elegir cámara, tema claro, oscuro o automático, reiniciar progreso y eliminar la cuenta.
- **Recuperar contraseña por correo** con enlace de un solo uso que vence a los 10 minutos.
- Diseño adaptable a celular y computadora (Responsivo).

## Tecnologías

| Área | Herramientas |
|---|---|
| Backend | Python, Flask |
| Base de datos | SQLite |
| Seguridad | bcrypt, sesiones de Flask |
| Visión e IA | MediaPipe (landmarks de la mano), scikit-learn (Random Forest), OpenCV, NumPy |
| Frontend | HTML, CSS y JavaScript (sin frameworks) |

## Estructura del proyecto

```
APP/
├── app.py                  # Servidor Flask y rutas
├── config.py               # Rutas y configuración general
├── requirements.txt
├── backend/
│   ├── correo.py           # Envío de correos (recuperar contraseña)
│   ├── correo_config.py    # Credenciales del correo (NO se sube a Git, está en .gitignore)
│   ├── database/           # Usuarios, progreso, logros, cuenta.
│   ├── datos/              # Base de datos local (usuarios.db está en el .gitignore)
│   └── vision/             # Evaluación de señas
├── frontend/
│   ├── css/  html/  js/    # Interfaz del sistema y comportamiento de cada página dinámica
│   ├── imagenes/abecedario/   # Imagen de referencia por letra (A.png, B.png...)
│   └── videos/abecedario/     # Video explicativo por letra (A.mp4, B.mp4...)
└── modelo/
    ├── landmarks.py                    # Extracción y normalización de landmarks
    ├── capturar_estaticas.py           # Captura de letras estáticas
    ├── capturar_mov.py                 # Captura de letras con movimiento
    ├── entrenar_modelo.py              # Entrena el modelo estático
    ├── entrenar_modelo_dinamico.py     # Entrena el modelo de movimiento
    ├── letrasest/                      # Dataset estático (A/A01.npy, ...)
    └── letrasmov/                      # Dataset de movimiento
```

## Instalación

Requisitos: **Python 3.10 o superior**, una cámara web y un navegador moderno.
En este caso usamos la **Versión 3.10.12**

```bash
git clone <https://github.com/KarimeCovarrubias/GESTUM.git>
cd <GESTUM>/APP

# Entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
```

## Configurar el correo (recuperar contraseña)

Sin esta configuración la app funciona normal, pero los enlaces de recuperación se imprimen en la consola en vez de enviarse (modo desarrollo).

1. En la cuenta de Gmail que enviará los correos, activa la **verificación en 2 pasos**.
2. Crea una **contraseña de aplicación** en <https://myaccount.google.com/apppasswords>.
3. Copia `backend/correo_config_ejemplo.txt` como `backend/correo_config.py` y escribe tus datos:

   ```python
   USUARIO = "tu_correo@gmail.com"
   CLAVE = "abcd efgh ijkl mnop"   # contraseña de aplicación, no la de tu cuenta
   ```

También puedes usar variables de entorno: `GESTUM_SMTP_USUARIO`, `GESTUM_SMTP_CLAVE`, y opcionalmente `GESTUM_SMTP_HOST` y `GESTUM_SMTP_PUERTO`.

> **Importante:** `correo_config.py` y la base de datos están en `.gitignore`. Nunca subas contraseñas al repositorio.

## Ejecutar

```bash
python app.py
```

Abre <http://127.0.0.1:5000> en el navegador y permite el acceso a la cámara. La primera vez, crea una cuenta con un correo.

> La cámara solo funciona en `localhost` o en sitios con HTTPS.

## Entrenar o reentrenar el modelo

Los modelos entrenados se guardan en `modelo/` como archivos `.pkl`. Si cambias el dataset, bórralos y vuelve a entrenar.

**Letras estáticas**
```bash
python modelo/capturar_estaticas.py A        # captura la letra A (ESPACIO inicia, Q guarda y sale)
python modelo/entrenar_modelo.py
```
Cada toma se guarda sola al llegar a 150 frames (`META_FRAMES`). Se recomiendan al menos 5 tomas por letra, con variedad de distancia, ángulo y luz, y de varias personas.

**Letras con movimiento**
```bash
python modelo/capturar_mov.py
python modelo/entrenar_modelo_dinamico.py
```

El entrenamiento incluye una versión espejada de los datos para que el modelo reconozca también la mano izquierda, y muestra la precisión por tomas completas para evitar resultados inflados.

## Contenido de las lecciones

Cada letra usa una imagen y un video de referencia, nombrados con la letra en mayúscula:

- `frontend/imagenes/abecedario/A.png`
- `frontend/videos/abecedario/A.mp4`

 - Las lecciones de teoría muestran las imágenes y videos de las letras a estudiar.
 - Las lecciones de práctica muestran las imágenes de las letras a interpretar después de ver la teoría. Además, utilizan la cámara de tu dispositivo.
 - Las Pruebas muestran las imágenes de las letras a interpretar después de haber completado las lecciones de prueba. Además, utilizan la cámara de tu dispositivo.

Si falta alguno, la pantalla de teoría muestra un ícono en su lugar. Los videos se recomiendan en formato vertical (9:16) y comprimidos.

## Metodología de desarrollo
GESTUM se desarrolló con un modelo **Iterativo e Incremental** con un prototipado evolutivo
 - **Incremental**: El sistema creció por módulos funcionales (cuentas y lecciones, práctica con cámara, pruebas, perfil y logros, configuración, tema oscuro,
 recuperación de contraseña), cada uno integrado a una versión que ya funcionaba.
 - **Iterativo**: Cada módulo pasó por ciclos cortos de diseño, implementación, prueba y corrección a partir de la retroalimentación obtenida en las pruebas con usuarios
 creados por el equipo de trabajo.
- **Prototipado evolutivo**: Los requisitos se fueron precisando con cada versión (por ejemplo, la regla de la racha o el correo obligatorio) y el modelo de IA se mejoró capturando datos, entrenando y evaluando en varias rondas.

## Estado del proyecto

En desarrollo. Pendiente probar el modelo con más personas, con distintas condiciones de luz y con personas zurdas. Además, pendiente de añadir más lecciones y logros.
En un futuro probablemente implementemos el Rankin.

## Licencia

Por definir.

## Mostrar/verificar Actualizaciones del repositorio de GitHub
```bash
git log --oneline --reverse
```

## Para clonar el repositorio
```bash
robocopy C:\Users\TU-USUARIO\GESTUM D:\Respaldo\GESTUM /E /XD venv __pycache__ /R:1 /W:1
```