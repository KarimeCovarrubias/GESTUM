const INTERVALO_MS = 900;

let indiceActual = 0;
let evaluando = false;
let pausado = false;
let intervaloId = null;
let grabandoClip = false;
let aciertos = 0;   // letras hechas bien
let saltadas = 0;   // letras que el usuario saltó

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const camaraOverlay = document.getElementById('camara-overlay');
const letraObjetivoEl = document.getElementById('letra-objetivo');
const progresoFill = document.getElementById('progreso-fill');
const pantallaCompleta = document.getElementById('pantalla-completa');
const referenciaPlaceholder = document.getElementById('referencia-placeholder');
const referenciaImg = document.getElementById('referencia-img');

const feedbackBar = document.getElementById('feedback-bar');
const feedbackIcon = document.getElementById('feedback-icon');
const feedbackTitulo = document.getElementById('feedback-titulo');
const feedbackSub = document.getElementById('feedback-sub');
const btnContinuar = document.getElementById('btn-continuar');
const btnSaltar = document.getElementById('btn-saltar');

function letraActual() {
    return window.LECCION.letras[indiceActual];
}

function actualizarProgresoUI() {
    const total = window.LECCION.letras.length;
    progresoFill.style.width = total ? `${(indiceActual / total) * 100}%` : '0%';
    letraObjetivoEl.textContent = letraActual() || '';
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
    if (evaluando || pausado || !window.LECCION.letras.length) return;
    if (!video.videoWidth) return;
    if (grabandoClip || ClipMovimiento.esDinamica(letraActual())) return;

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

function procesarResultado(data) {
    if (!data.ok) {
        camaraOverlay.textContent = 'Error al evaluar la seña.';
        return;
    }

    if (!data.mano_detectada) {
        camaraOverlay.textContent = data.clip_valido === false
            ? 'No se vio tu mano durante la grabación. Pulsa Grabar e inténtalo de nuevo'
            : 'No se detecta tu mano';
        return;
    }

    if (!data.modelo_listo) {
        camaraOverlay.textContent = 'Modelo no disponible';
        return;
    }

    if (data.correcto) {
        camaraOverlay.textContent = '¡Correcto! ✓';
        mostrarBarraExito();
    } else {
        camaraOverlay.textContent = ClipMovimiento.esDinamica(letraActual())
            ? `Detecté: ${data.prediccion}. Pulsa Grabar para reintentar`
            : `Detecté: ${data.prediccion}`;
    }
}

function mostrarBarraExito() {
    if (pausado) return;   // ya se contó esta letra
    pausado = true;
    aciertos += 1;
    btnContinuar.disabled = false;
    if (btnSaltar) btnSaltar.disabled = true;
    ClipMovimiento.ocultarBoton();
    feedbackBar.className = 'feedback-bar feedback-bar--ok';
    feedbackIcon.textContent = '✓';
    feedbackTitulo.textContent = '¡Excelente!';
    feedbackSub.textContent = `Lograste la letra ${letraActual()}`;
    
    // Si es la última letra, cambia el texto a "Siguiente Lección" o "Finalizar"
    btnContinuar.textContent = (indiceActual === window.LECCION.letras.length - 1) ? 'Siguiente Lección' : 'Siguiente Letra';
}

function restablecerBarraInferior() {
    feedbackBar.className = 'feedback-bar';
    btnContinuar.disabled = true;           // solo se activa al acertar la letra
    if (btnSaltar) btnSaltar.disabled = false;
    feedbackIcon.textContent = '➔';
    
    const letra = letraActual();
    if (letra) {
        feedbackTitulo.textContent = `Letra ${letra}`;
        feedbackSub.textContent = 'Muestra la seña frente a la cámara';
        btnContinuar.textContent = (indiceActual === window.LECCION.letras.length - 1) ? 'Siguiente Lección' : 'Siguiente Letra';
    } else {
        feedbackTitulo.textContent = '¡Lección completada!';
        feedbackSub.textContent = 'Haz clic para finalizar';
        btnContinuar.textContent = 'Siguiente Lección';
    }
}

function saltarLetra() {
    if (pausado || grabandoClip) return;   // ya la hizo bien, o está grabando
    saltadas += 1;
    avanzarSiguienteLetra();
}

function avanzarSiguienteLetra() {
    indiceActual += 1;
    pausado = false;

    // Si ya completaste todas las letras de la lección actual
    if (indiceActual >= window.LECCION.letras.length) {
        finalizarLeccion();
        return;
    }

    actualizarProgresoUI();
    if (!ClipMovimiento.esDinamica(letraActual())) {
        camaraOverlay.textContent = 'Buscando tu mano…';
    }
}

// XP = (XP total de la lección / letras) x letras hechas bien. Precisión = hechas bien / letras.
function mostrarResultados() {
    const total = window.LECCION.letras.length;
    const xpPorLetra = (window.LECCION.xpTotal || 0) / total;
    const xp = Math.round(aciertos * xpPorLetra);
    const precision = Math.round((aciertos / total) * 100);

    const xpEl = document.getElementById('resultado-xp');
    const precisionEl = document.getElementById('resultado-precision');
    const subEl = document.getElementById('resultado-sub');
    if (xpEl) xpEl.textContent = xp;
    if (precisionEl) precisionEl.textContent = precision;
    if (subEl && saltadas > 0) {
        subEl.textContent = saltadas === 1
            ? 'Saltaste 1 letra. Vuelve a practicarla para dominarla.'
            : `Saltaste ${saltadas} letras. Vuelve a practicarlas para dominarlas.`;
    }
}

function finalizarLeccion() {
    if (typeof intervaloId !== 'undefined' && intervaloId) {
        clearInterval(intervaloId);
    }
    
    const video = document.getElementById('video');
    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }

    mostrarResultados();

    const pantallaCompleta = document.getElementById('pantalla-completa');
    if (pantallaCompleta) {
        pantallaCompleta.removeAttribute('hidden');
    }
}

btnContinuar.addEventListener('click', avanzarSiguienteLetra);
if (btnSaltar) btnSaltar.addEventListener('click', saltarLetra);

const btnComenzar = document.getElementById('btn-comenzar');
const pantallaInicio = document.getElementById('pantalla-inicio');
const practicaContenido = document.getElementById('practica-contenido');

function iniciarPractica() {
    if (!window.LECCION.letras || !window.LECCION.letras.length) {
        camaraOverlay.textContent = 'Sin letras configuradas.';
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
            iniciarPractica();
        });
    } else {
        // Por si esta página se usa sin la pantalla de inicio, arranca directo
        iniciarPractica();
    }
});