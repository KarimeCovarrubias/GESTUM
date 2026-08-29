// frontend/js/practica.js

const INTERVALO_MS = 900; // cada cuánto se manda un frame a evaluar
const ESPERA_TRAS_CORRECTO_MS = 1200;

let indiceActual = 0;
let evaluando = false;   // evita mandar un frame mientras el anterior sigue en vuelo
let pausado = false;     // se pausa brevemente tras acertar, antes de pasar a la siguiente letra
let intervaloId = null;

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const overlay = document.getElementById('feedback-overlay');
const letraObjetivoEl = document.getElementById('letra-objetivo');
const progresoTexto = document.getElementById('progreso-texto');
const progresoFill = document.getElementById('progreso-fill');
const pantallaCompleta = document.getElementById('pantalla-completa');

function letraActual() {
    return window.LECCION.letras[indiceActual];
}

function actualizarProgresoUI() {
    const total = window.LECCION.letras.length;
    progresoTexto.textContent = `${indiceActual} / ${total}`;
    progresoFill.style.width = total ? `${(indiceActual / total) * 100}%` : '0%';
    letraObjetivoEl.textContent = letraActual() || '';
}

async function iniciarCamara() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;
        overlay.textContent = 'Buscando tu mano…';
        intervaloId = setInterval(capturarYEvaluar, INTERVALO_MS);
    } catch (error) {
        console.error('No se pudo acceder a la cámara:', error);
        overlay.textContent = 'No se pudo acceder a la cámara. Revisa los permisos del navegador.';
    }
}

function capturarFrameBase64() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1); // efecto espejo, más natural para el usuario
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.7);
}

async function capturarYEvaluar() {
    if (evaluando || pausado || !window.LECCION.letras.length) return;
    if (!video.videoWidth) return; // la cámara todavía no tiene frames listos

    evaluando = true;
    const imagen = capturarFrameBase64();
    const letra = letraActual();

    try {
        const respuesta = await fetch('/api/practica/evaluar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ letra, imagen })
        });

        const data = await respuesta.json();
        mostrarResultado(data);
    } catch (error) {
        console.error('Error evaluando el frame:', error);
    } finally {
        evaluando = false;
    }
}

function mostrarResultado(data) {
    if (!data.ok) {
        overlay.textContent = 'Ocurrió un error evaluando la seña.';
        overlay.className = 'feedback feedback--info';
        return;
    }

    if (!data.mano_detectada) {
        overlay.textContent = 'No se detecta tu mano';
        overlay.className = 'feedback feedback--info';
        return;
    }

    if (!data.modelo_listo) {
        overlay.textContent = 'El modelo todavía no está entrenado';
        overlay.className = 'feedback feedback--info';
        return;
    }

    if (data.correcto) {
        overlay.textContent = '¡Correcto! ✓';
        overlay.className = 'feedback feedback--ok';
        avanzarSiguienteLetra();
    } else {
        overlay.textContent = `Detecté: ${data.prediccion}`;
        overlay.className = 'feedback feedback--error';
    }
}

function avanzarSiguienteLetra() {
    pausado = true;
    setTimeout(() => {
        indiceActual += 1;
        pausado = false;

        if (indiceActual >= window.LECCION.letras.length) {
            finalizarLeccion();
            return;
        }

        actualizarProgresoUI();
        overlay.textContent = 'Buscando tu mano…';
        overlay.className = 'feedback';
    }, ESPERA_TRAS_CORRECTO_MS);
}

function finalizarLeccion() {
    if (intervaloId) clearInterval(intervaloId);
    actualizarProgresoUI();
    document.querySelector('.camara-box').hidden = true;
    document.querySelector('.progreso-leccion').hidden = true;
    document.querySelector('.letra-actual').hidden = true;
    pantallaCompleta.hidden = false;
}

document.addEventListener('DOMContentLoaded', () => {
    if (!window.LECCION.letras || !window.LECCION.letras.length) {
        overlay.textContent = 'Esta lección todavía no tiene letras configuradas.';
        return;
    }
    actualizarProgresoUI();
    iniciarCamara();
});