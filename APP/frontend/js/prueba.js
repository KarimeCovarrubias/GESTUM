// Igual que practica.js (misma cámara, misma tolerancia a fallos, misma
// barra inferior), pero en vez de una lista plana de letras, recorre
// PALABRAS completas letra por letra. Al terminar la última letra de la
// última palabra, marca la prueba como aprobada en el backend.

const INTERVALO_MS = 900;

let indicePalabra = 0;
let indiceLetraEnPalabra = 0;
let evaluando = false;
let pausado = false;
let intervaloId = null;
let grabandoClip = false;

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const camaraOverlay = document.getElementById('camara-overlay');
const letraObjetivoEl = document.getElementById('letra-objetivo');
const palabraLetrasEl = document.getElementById('palabra-letras');
const palabraContadorEl = document.getElementById('palabra-contador');
const palabraPasosEl = document.getElementById('palabra-pasos');
const avisoMovEl = document.getElementById('aviso-mov');
const camaraBox = document.getElementById('camara-box');
const toastPalabra = document.getElementById('toast-palabra');
const progresoFill = document.getElementById('progreso-fill');
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

// Letras ya hechas en toda la prueba (para la barra de arriba)
function letrasHechas() {
    let hechas = 0;
    for (let i = 0; i < indicePalabra; i++) hechas += window.LECCION.palabras[i].length;
    return hechas + indiceLetraEnPalabra;
}

function totalLetras() {
    return window.LECCION.palabras.reduce((suma, palabra) => suma + palabra.length, 0);
}

// Dibuja los círculos de palabras y las fichas de la palabra actual.
// Si 'exito' es true, la letra actual se marca como lograda (verde).
function renderPalabra(exito = false) {
    const palabras = window.LECCION.palabras;

    palabraPasosEl.innerHTML = palabras
        .map((_, i) => {
            if (i < indicePalabra) return '<span class="paso done">✓</span>';
            if (i === indicePalabra) return `<span class="paso actual">${i + 1}</span>`;
            return `<span class="paso">${i + 1}</span>`;
        })
        .join('');

    const palabra = palabraActual();
    palabraContadorEl.textContent = `Palabra ${indicePalabra + 1} de ${palabras.length}`;

    if (palabra) {
        palabraLetrasEl.innerHTML = palabra
            .split('')
            .map((letra, i) => {
                if (i < indiceLetraEnPalabra) return `<span class="tile-letra done">${letra}</span>`;
                if (i === indiceLetraEnPalabra) {
                    return `<span class="tile-letra current${exito ? ' exito' : ''}">${exito ? '✓' : letra}</span>`;
                }
                return `<span class="tile-letra">${letra}</span>`;
            })
            .join('');
    }
}

function actualizarProgresoUI() {
    const total = totalLetras();
    progresoFill.style.width = total ? `${(letrasHechas() / total) * 100}%` : '0%';

    renderPalabra(false);

    // Cámara y marco vuelven al estado "buscando" con cada letra nueva
    camaraBox.classList.remove('camara-ok');
    camaraOverlay.className = 'camara-overlay estado-buscando';

    letraObjetivoEl.textContent = letraActual() || '';
    if (avisoMovEl) avisoMovEl.hidden = !ClipMovimiento.esDinamica(letraActual());
    restablecerBarraInferior();
    actualizarReferencia();
    prepararLetraConMovimiento();
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

async function abrirCamara() {
    // Usa la cámara elegida en Configuración; si ya no existe, la predeterminada
    let id = '';
    try { id = localStorage.getItem('gestum_camara') || ''; } catch (e) { /* sin almacenamiento */ }
    if (id) {
        try {
            return await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: id } }, audio: false });
        } catch (e) { /* cae a la predeterminada */ }
    }
    return navigator.mediaDevices.getUserMedia({ video: true, audio: false });
}

async function iniciarCamara() {
    try {
        const stream = await abrirCamara();
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
    // Sin espejo: igual que los datos de entrenamiento (el espejo visual lo hace el CSS)
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.7);
}

async function capturarYEvaluar() {
    if (evaluando || pausado || !window.LECCION.palabras.length) return;
    if (!video.videoWidth) return;
    if (grabandoClip || ClipMovimiento.esDinamica(letraActual())) return;

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

function prepararLetraConMovimiento() {
    if (ClipMovimiento.esDinamica(letraActual())) {
        ClipMovimiento.mostrarBoton(grabarMovimiento);
        camaraOverlay.textContent = 'Esta letra lleva movimiento: pulsa "Grabar movimiento"';
    } else {
        ClipMovimiento.ocultarBoton();
    }
}

async function grabarMovimiento() {
    if (grabandoClip || pausado || !video.videoWidth) return;
    grabandoClip = true;
    ClipMovimiento.deshabilitarBoton(true);
    try {
        const data = await ClipMovimiento.grabarYEvaluar(
            letraActual(), video, canvas, (texto) => { camaraOverlay.textContent = texto; }
        );
        procesarResultado(data);
    } catch (error) {
        console.error('Error evaluando el clip:', error);
        camaraOverlay.textContent = 'Error al evaluar la seña.';
    } finally {
        grabandoClip = false;
        ClipMovimiento.deshabilitarBoton(false);
    }
}

function setEstado(clase, texto) {
    camaraOverlay.className = `camara-overlay ${clase}`;
    camaraOverlay.textContent = texto;
}

function procesarResultado(data) {
    if (!data.ok) {
        setEstado('estado-detecto', 'Error al evaluar la seña.');
        return;
    }

    if (!data.mano_detectada) {
        setEstado('estado-buscando', data.clip_valido === false
            ? 'No se vio tu mano durante la grabación. Pulsa Grabar e inténtalo de nuevo'
            : 'No se detecta tu mano');
        return;
    }

    if (!data.modelo_listo) {
        setEstado('estado-detecto', 'Modelo no disponible');
        return;
    }

    if (data.correcto) {
        setEstado('estado-ok', '¡Correcto! ✓');
        mostrarBarraExito();
    } else {
        setEstado('estado-detecto', ClipMovimiento.esDinamica(letraActual())
            ? `Detecté: ${data.prediccion}. Pulsa Grabar para reintentar`
            : `Detecté: ${data.prediccion}`);
    }
}

function mostrarBarraExito() {
    if (pausado) return;
    pausado = true;
    ClipMovimiento.ocultarBoton();
    camaraBox.classList.add('camara-ok');
    renderPalabra(true);
    if (indiceLetraEnPalabra === palabraActual().length - 1) {
        toastPalabra.classList.add('show');
        setTimeout(() => toastPalabra.classList.remove('show'), 1800);
    }
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
    if (!ClipMovimiento.esDinamica(letraActual())) {
        camaraOverlay.textContent = 'Buscando tu mano…';
    }
}

async function finalizarPrueba() {
    progresoFill.style.width = '100%';
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