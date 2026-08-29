const INTERVALO_MS = 900; // cada cuánto se manda un frame a evaluar mientras se busca la seña
const VIDAS_INICIALES = 5;

let indiceActual = 0;
let vidas = VIDAS_INICIALES;
let evaluando = false;   // evita mandar un frame mientras el anterior sigue en vuelo
let pausado = false;     // se pausa mientras se muestra la barra de "¡Correcto!"
let intervaloId = null;

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const camaraOverlay = document.getElementById('camara-overlay');
const letraObjetivoEl = document.getElementById('letra-objetivo');
const progresoFill = document.getElementById('progreso-fill');
const vidasValEl = document.getElementById('vidas-val');
const pantallaCompleta = document.getElementById('pantalla-completa');
const referenciaPlaceholder = document.getElementById('referencia-placeholder');
const referenciaImg = document.getElementById('referencia-img');

const feedbackBar = document.getElementById('feedback-bar');
const feedbackIcon = document.getElementById('feedback-icon');
const feedbackTitulo = document.getElementById('feedback-titulo');
const feedbackSub = document.getElementById('feedback-sub');
const btnContinuar = document.getElementById('btn-continuar');

function letraActual() {
    return window.LECCION.letras[indiceActual];
}

function actualizarProgresoUI() {
    const total = window.LECCION.letras.length;
    progresoFill.style.width = total ? `${(indiceActual / total) * 100}%` : '0%';
    letraObjetivoEl.textContent = letraActual() || '';
    vidasValEl.textContent = vidas;
    actualizarReferencia();
}

// Muestra la imagen de referencia de la letra si existe en /static/imagenes/abecedario/<LETRA>.png,
// o el placeholder si todavía no hay material para esa letra.
function actualizarReferencia() {
    const letra = letraActual();
    if (!letra) return;

    const ruta = `../frontend/imagenes/abecedario/${letra}.png`;
    const probeImg = new Image();
    probeImg.onload = () => {
        referenciaImg.src = ruta;
        referenciaImg.hidden = false;
        referenciaPlaceholder.hidden = true;
    };
    probeImg.onerror = () => {
        console.warn(`No se encontró la imagen para la letra: ${letra} en la ruta ${ruta}`)
        referenciaImg.hidden = true;
        referenciaPlaceholder.hidden = false;
    };
    probeImg.src = ruta;
}

async function iniciarCamara() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;
        camaraOverlay.textContent = 'Buscando tu mano…';
        intervaloId = setInterval(capturarYEvaluar, INTERVALO_MS);
    } catch (error) {
        console.error('No se pudo acceder a la cámara:', error);
        camaraOverlay.textContent = 'No se pudo acceder a la cámara. Revisa los permisos del navegador.';
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
        procesarResultado(data);
    } catch (error) {
        console.error('Error evaluando el frame:', error);
    } finally {
        evaluando = false;
    }
}

function procesarResultado(data) {
    if (!data.ok) {
        camaraOverlay.textContent = 'Ocurrió un error evaluando la seña.';
        return;
    }

    if (!data.mano_detectada) {
        camaraOverlay.textContent = 'No se detecta tu mano';
        return;
    }

    if (!data.modelo_listo) {
        camaraOverlay.textContent = 'El modelo todavía no está entrenado';
        return;
    }

    if (data.correcto) {
        camaraOverlay.textContent = '¡Correcto! ✓';
        mostrarBarraExito();
    } else {
        camaraOverlay.textContent = `Detecté: ${data.prediccion}`;
        registrarFallo();
    }
}

function registrarFallo() {
    // Cosmético por ahora: las vidas no se guardan en el backend todavía,
    // solo bajan visualmente durante la sesión de práctica actual.
    vidas = Math.max(0, vidas - 1);
    vidasValEl.textContent = vidas;
}

function mostrarBarraExito() {
    pausado = true;

    feedbackBar.className = 'feedback-bar feedback-bar--ok';
    feedbackIcon.textContent = '✓';
    feedbackTitulo.textContent = '¡Correcto!';
    feedbackSub.textContent = `Dominaste la letra ${letraActual()}`;
    feedbackBar.hidden = false;
}

function avanzarSiguienteLetra() {
    feedbackBar.hidden = true;
    indiceActual += 1;
    pausado = false;

    if (indiceActual >= window.LECCION.letras.length) {
        finalizarLeccion();
        return;
    }

    actualizarProgresoUI();
    camaraOverlay.textContent = 'Buscando tu mano…';
}

function finalizarLeccion() {
    if (intervaloId) clearInterval(intervaloId);
    actualizarProgresoUI();
    document.querySelector('.practica-grid').hidden = true;
    document.querySelector('.letra-actual').hidden = true;
    pantallaCompleta.hidden = false;
}

btnContinuar.addEventListener('click', avanzarSiguienteLetra);

document.addEventListener('DOMContentLoaded', () => {
    if (!window.LECCION.letras || !window.LECCION.letras.length) {
        camaraOverlay.textContent = 'Esta lección todavía no tiene letras configuradas.';
        return;
    }
    actualizarProgresoUI();
    iniciarCamara();
});