// Compartido por practica.js y prueba.js.
//
// Las letras con movimiento (J, K, LL, Ñ, Q, X, Z) no se pueden evaluar con
// una sola foto. Aquí se graba un clip corto (cuenta regresiva + ~2 s) y se
// manda ENTERO al servidor, igual que hace capturar_mov.py con el dataset.
//
// Los frames se mandan SIN espejo (el espejo del video es solo visual, por
// CSS): así coinciden con los datos con los que se entrenó el modelo.
//
// Si cambias estos valores, cámbialos también en config.py.
(function () {
    const LETRAS_DINAMICAS = ['J', 'K', 'LL', 'Ñ', 'Q', 'X', 'Z'];
    const DURACION_MS = 2000;
    const INTERVALO_MS = 70;
    const CUENTA_REGRESIVA_S = 2;
    const ANCHO_PX = 480;

    let boton = null;
    let aviso = null;

    const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

    function frameBase64(video, canvas) {
        const ancho = ANCHO_PX;
        const alto = Math.round(ancho * video.videoHeight / video.videoWidth);
        canvas.width = ancho;
        canvas.height = alto;
        canvas.getContext('2d').drawImage(video, 0, 0, ancho, alto);
        return canvas.toDataURL('image/jpeg', 0.7);
    }

    function asegurarElementos() {
        if (boton) return;
        const caja = document.querySelector('.camara-box');
        if (!caja) return;
        boton = document.createElement('button');
        boton.type = 'button';
        boton.className = 'btn-grabar-mov';
        boton.textContent = '● Grabar movimiento';
        boton.hidden = true;
        aviso = document.createElement('div');
        aviso.className = 'aviso-grabacion';
        aviso.hidden = true;
        caja.appendChild(boton);
        caja.appendChild(aviso);
    }

    function esDinamica(letra) {
        return LETRAS_DINAMICAS.includes(letra);
    }

    function mostrarBoton(alClic) {
        asegurarElementos();
        if (!boton) return;
        boton.hidden = false;
        boton.disabled = false;
        boton.onclick = alClic;
    }

    function ocultarBoton() {
        if (boton) boton.hidden = true;
        if (aviso) aviso.hidden = true;
    }

    function deshabilitarBoton(valor) {
        if (boton) boton.disabled = valor;
    }

    function mostrarAviso(texto) {
        if (!aviso) return;
        aviso.textContent = texto || '';
        aviso.hidden = !texto;
    }

    // Cuenta regresiva, graba y manda al servidor. Devuelve la respuesta JSON.
    async function grabarYEvaluar(letra, video, canvas, estado) {
        for (let s = CUENTA_REGRESIVA_S; s > 0; s--) {
            mostrarAviso(String(s));
            estado(`Prepárate… ${s}`);
            await esperar(1000);
        }

        mostrarAviso('GRABANDO');
        estado('Grabando: haz la seña');
        const frames = [];
        const inicio = performance.now();
        while (performance.now() - inicio < DURACION_MS) {
            frames.push(frameBase64(video, canvas));
            await esperar(INTERVALO_MS);
        }
        mostrarAviso('');
        estado('Analizando…');

        const respuesta = await fetch('/api/practica/evaluar-secuencia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ letra, frames })
        });
        return respuesta.json();
    }

    window.ClipMovimiento = {
        esDinamica, mostrarBoton, ocultarBoton, deshabilitarBoton, grabarYEvaluar
    };
})();