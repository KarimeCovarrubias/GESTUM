// Cuadro de confirmación al pulsar la ✕ de salir (teoría, práctica, prueba y
// repaso). "Sigue aprendiendo" cierra el cuadro; "Salir" va a inicio.
// Se activa solo en los enlaces con el atributo data-salir.
(function () {
    let fondo = null;
    let destino = '/user-home';
    let anteriorFoco = null;

    function construir() {
        fondo = document.createElement('div');
        fondo.className = 'salir-fondo';
        fondo.hidden = true;
        fondo.innerHTML = `
            <div class="salir-caja" role="dialog" aria-modal="true" aria-labelledby="salir-titulo">
                <div class="salir-icono">🥺</div>
                <h2 id="salir-titulo" class="salir-titulo">¡Espera, no te vayas!</h2>
                <p class="salir-texto">Si sales ahora, perderás el avance de esta lección y tendrás que empezarla de nuevo.</p>
                <button type="button" class="salir-btn-seguir">SIGUE APRENDIENDO</button>
                <button type="button" class="salir-btn-salir">SALIR</button>
            </div>`;
        document.body.appendChild(fondo);

        fondo.querySelector('.salir-btn-seguir').addEventListener('click', cerrar);
        fondo.querySelector('.salir-btn-salir').addEventListener('click', () => {
            window.location.href = destino;
        });
        fondo.addEventListener('click', (e) => { if (e.target === fondo) cerrar(); });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !fondo.hidden) cerrar();
        });
    }

    function abrir(url) {
        if (!fondo) construir();
        destino = url || '/user-home';
        anteriorFoco = document.activeElement;
        fondo.hidden = false;
        fondo.querySelector('.salir-btn-seguir').focus();
    }

    function cerrar() {
        fondo.hidden = true;
        if (anteriorFoco && anteriorFoco.focus) anteriorFoco.focus();
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-salir]').forEach((enlace) => {
            enlace.addEventListener('click', (e) => {
                e.preventDefault();
                abrir(enlace.getAttribute('href'));
            });
        });
    });
})();