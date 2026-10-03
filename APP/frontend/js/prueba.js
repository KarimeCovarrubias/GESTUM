// Igual que practica.js (misma cámara, misma tolerancia a fallos, misma
// barra inferior), pero en vez de una lista plana de letras, recorre
// PALABRAS completas letra por letra. Al terminar la última letra de la
// última palabra, marca la prueba como aprobada en el backend.

const INTERVALO_MS = 900;
const VIDAS_INICIALES = 5;
const FALLOS_CONSECUTIVOS_PARA_RESTAR_VIDA = 4;

let indicePalabra = 0;
let indiceLetraEnPalabra = 0;
let vidas = VIDAS_INICIALES;
let fallosConsecutivos = 0;
let evaluando = false;
let pausado = false;
let intervaloId = null;

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const camaraOverlay = document.getElementById('camara-overlay');
const letraObjetivoEl = document.getElementById('letra-objetivo');
const palabraLetrasEl = document.getElementById('palabra-letras');
const palabraContadorEl = document.getElementById('palabra-contador');
const progresoFill = document.getElementById('progreso-fill');
const vidasValEl = document.getElementById('vidas-val');
const referenciaPlaceholder = document.getElementById('referencia-placeholder');
const referenciaImg = document.getElementById('referencia-img');

const feedbackBar = document.getElementById('feedback-bar');
const feedbackIcon = document.getElementById('feedback-icon');
const feedbackTitulo = document.getElementById('feedback-titulo');
const feedbackSub = document.getElementById('feedback-sub');
const btnContinuar = document.getElementById('btn-continuar');

function palabraActual() {
    return window.LECCION.palabras[indicePalabra];
}

function letraActual() {
    const palabra = palabraActual();
    return palabra ? palabra[indiceLetraEnPalabra] : null;
}

function esUltimaLetraDeTodo() {
    const esUltimaPalabra = indicePalabra === window.LECCION.palabras.length - 1;
    const esUltimaLetra = indiceLetraEnPalabra === palabraActual().length - 1;
    return esUltimaPalabra && esUltimaLetra;
}

function actualizarProgresoUI() {
    const totalPalabras = window.LECCION.palabras.length;
    progresoFill.style.width = totalPalabras ? `${(indicePalabra / totalPalabras) * 100}%` : '0%';

    const palabra = palabraActual();
    palabraContadorEl.textContent = `Palabra ${indicePalabra + 1} de ${totalPalabras}`;

    if (palabra) {
        palabraLetrasEl.innerHTML = palabra
            .split('')
            .map((letra, i) => {
                if (i < indiceLetraEnPalabra) return `<span style="opacity:.4">${letra}</span>`;
                if (i === indiceLetraEnPalabra) return `<strong>${letra}</strong>`;
                return letra;
            })
            .join('');
    }

    letraObjetivoEl.textContent = letraActual() || '';
    vidasValEl.textContent = vidas;
    restablecerBarraInferior();
    actualizarReferencia();
}

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
        camaraOverlay.textContent = 'Sin acceso a la cámara. Permite los permisos en el navegador.';
    }
}

function capturarFrameBase64() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.7);
}

async function capturarYEvaluar() {
    if (evaluando || pausado || !window.LECCION.palabras.length) return;
    if (!video.videoWidth) return;

    evaluando = true;
    const imagen = capturarFrameBase64();
    const letra = letraActual();

    try {
        // Se reutiliza el mismo endpoint de práctica: evalúa una letra a la
        // vez contra un frame, sin importar si viene de una lección normal
        // o de una prueba -- la lógica de evaluación es idéntica.
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
        camaraOverlay.textContent = 'Error al evaluar la seña.';
        return;
    }

    if (!data.mano_detectada) {
        camaraOverlay.textContent = 'No se detecta tu mano';
        return;
    }

    if (!data.modelo_listo) {
        camaraOverlay.textContent = 'Modelo no disponible';
        return;
    }

    if (data.correcto) {
        camaraOverlay.textContent = '¡Correcto! ✓';
        fallosConsecutivos = 0;
        mostrarBarraExito();
    } else {
        camaraOverlay.textContent = `Detecté: ${data.prediccion}`;
        registrarFallo();
    }
}

function registrarFallo() {
    // Tolera reacomodar la mano: solo resta vida tras varios fallos seguidos.
    fallosConsecutivos += 1;
    if (fallosConsecutivos >= FALLOS_CONSECUTIVOS_PARA_RESTAR_VIDA) {
        fallosConsecutivos = 0;
        vidas = Math.max(0, vidas - 1);
        vidasValEl.textContent = vidas;
    }
}

function mostrarBarraExito() {
    pausado = true;
    feedbackBar.className = 'feedback-bar feedback-bar--ok';
    feedbackIcon.textContent = '✓';
    feedbackTitulo.textContent = '¡Bien hecho!';
    feedbackSub.textContent = `Lograste la letra ${letraActual()}`;
    btnContinuar.textContent = esUltimaLetraDeTodo() ? 'Finalizar prueba' : 'Siguiente Letra';
}

function restablecerBarraInferior() {
    feedbackBar.className = 'feedback-bar';
    feedbackIcon.textContent = '➔';

    const letra = letraActual();
    if (letra) {
        feedbackTitulo.textContent = `Letra ${letra}`;
        feedbackSub.textContent = `Palabra: ${palabraActual()}`;
        btnContinuar.textContent = esUltimaLetraDeTodo() ? 'Finalizar prueba' : 'Siguiente Letra';
    }
}

function avanzarSiguienteLetra() {
    fallosConsecutivos = 0;

    const palabra = palabraActual();
    if (indiceLetraEnPalabra < palabra.length - 1) {
        indiceLetraEnPalabra += 1;
    } else {
        // Terminó la palabra actual, pasa a la siguiente
        indicePalabra += 1;
        indiceLetraEnPalabra = 0;

        if (indicePalabra >= window.LECCION.palabras.length) {
            finalizarPrueba();
            return;
        }
    }

    pausado = false;
    actualizarProgresoUI();
    camaraOverlay.textContent = 'Buscando tu mano…';
}

async function finalizarPrueba() {
    if (intervaloId) clearInterval(intervaloId);

    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }

    try {
        await fetch('/api/prueba/aprobar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ leccion_id: window.LECCION.id })
        });
    } catch (error) {
        console.error('No se pudo registrar la prueba aprobada:', error);
    }

    const pantallaCompleta = document.getElementById('pantalla-completa');
    if (pantallaCompleta) pantallaCompleta.removeAttribute('hidden');
}

btnContinuar.addEventListener('click', avanzarSiguienteLetra);

const btnComenzar = document.getElementById('btn-comenzar');
const pantallaInicio = document.getElementById('pantalla-inicio');
const practicaContenido = document.getElementById('practica-contenido');

function iniciarPrueba() {
    if (!window.LECCION.palabras || !window.LECCION.palabras.length) {
        camaraOverlay.textContent = 'Esta prueba todavía no tiene palabras configuradas.';
        return;
    }
    actualizarProgresoUI();
    iniciarCamara();
}

document.addEventListener('DOMContentLoaded', () => {
    if (btnComenzar && pantallaInicio && practicaContenido) {
        btnComenzar.addEventListener('click', () => {
            pantallaInicio.hidden = true;
            practicaContenido.hidden = false;
            iniciarPrueba();
        });
    } else {
        iniciarPrueba();
    }
});