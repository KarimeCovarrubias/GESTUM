// Función para alternar la visibilidad de las contraseñas
function toggleVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    const isPassword = input.type === "password";
    
    input.type = isPassword ? "text" : "password";

    const eyeOpen = `
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
        </svg>
    `;

    const eyeOff = `
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
    `;

    btn.innerHTML = isPassword ? eyeOff : eyeOpen;
}

// Modal dinámico al centro para mensajes y errores
function mostrarModal({ titulo, mensaje, textoBoton, alAceptar }) {
    const modalExistente = document.getElementById('custom-modal-overlay');
    if (modalExistente) modalExistente.remove();

    const modalHTML = `
        <div id="custom-modal-overlay" style="
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.6); display: flex; align-items: center;
            justify-content: center; z-index: 1000; backdrop-filter: blur(4px);
        ">
            <div style="
                background: #1e293b; color: #fff; padding: 25px 30px; border-radius: 12px;
                text-align: center; max-width: 350px; width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.1);
            ">
                <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.25rem;">${titulo}</h3>
                <p style="margin-bottom: 20px; color: #cbd5e1; font-size: 0.95rem;">${mensaje}</p>
                <button id="btn-modal-aceptar" style="
                    background: #2563eb; color: white; border: none; padding: 10px 20px;
                    border-radius: 6px; cursor: pointer; font-weight: 600; width: 100%;
                    font-size: 0.95rem;
                ">${textoBoton}</button>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    document.getElementById('btn-modal-aceptar').addEventListener('click', () => {
        const modal = document.getElementById('custom-modal-overlay');
        if (modal) modal.remove();
        if (typeof alAceptar === 'function') {
            alAceptar();
        }
    });
}

// Manejo del envío del formulario (distingue entre Login y Registro)
document.addEventListener('DOMContentLoaded', () => {
    const authForm = document.querySelector('.auth-form');

    if (!authForm) return;

    authForm.addEventListener('submit', async (e) => {
        const esRegistro = document.getElementById('confirmarContrasena') !== null;

        if (esRegistro) {
            e.preventDefault();

            const contrasena = document.getElementById('contrasena').value;
            const confirmarContrasena = document.getElementById('confirmarContrasena').value;

            if (contrasena !== confirmarContrasena) {
                mostrarModal({
                    titulo: 'Error en contraseñas',
                    mensaje: 'Las contraseñas no coinciden.',
                    textoBoton: 'Intentar de nuevo'
                });
                return;
            }

            const datosUsuario = {
                nombre: document.getElementById('nombre').value,
                apellidoP: document.getElementById('apellidoP').value,
                apellidoM: document.getElementById('apellidoM').value,
                edad: document.getElementById('edad').value,
                nombreUsuario: document.getElementById('nombreUsuario').value,
                contrasena: contrasena
            };

            try {
                // Ruta corregida a /api/registro
                const respuesta = await fetch('/api/registro', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datosUsuario)
                });

                const data = await respuesta.json();

                if (respuesta.ok && data.ok) {
                    mostrarModal({
                        titulo: '¡Registro exitoso!',
                        mensaje: 'Tu cuenta ha sido creada con éxito.',
                        textoBoton: 'Regrese a iniciar sesión',
                        alAceptar: () => {
                            window.location.href = data.redirect || '/login';
                        }
                    });
                } else {
                    mostrarModal({
                        titulo: 'Error de registro',
                        mensaje: data.mensaje || 'Ocurrió un error en el registro.',
                        textoBoton: 'Aceptar'
                    });
                }
            } catch (error) {
                console.error('Error en la petición de registro:', error);
            }

        } else {
            // Sección de Login
            e.preventDefault();

            const nombreUsuario = document.getElementById('nombreUsuario').value;
            const contrasena = document.getElementById('contrasena').value;

            try {
                const respuesta = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nombreUsuario, contrasena })
                });

                const data = await respuesta.json();

                if (data.ok) {
                    window.location.href = data.redirect;
                } else {
                    mostrarModal({
                        titulo: 'Error de autenticación',
                        mensaje: data.mensaje || 'Usuario y/o contraseña incorrectos',
                        textoBoton: 'Aceptar'
                    });
                }
            } catch (error) {
                console.error('Error al iniciar sesión:', error);
            }
        }
    });
});