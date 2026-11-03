// Teoría de una lección: una letra a la vez, con su imagen de referencia y su
// video explicativo. El botón de abajo avanza de letra; en la última manda a
// practicar (y cuenta como actividad del día para la racha).

const letras = window.LECCION.letras || [];
const BASE = window.STATIC_BASE || '/frontend/';

let indice = 0;

const imagenBox = document.getElementById('imagen-box');
const videoBox = document.getElementById('video-box');
const contador = document.getElementById('letra-contador');
const nombreEl = document.getElementById('letra-nombre');
const btnSiguiente = document.getElementById('btn-siguiente');
const progresoFill = document.getElementById('progreso-fill');

async function existeArchivo(url) {
    try {
        const respuesta = await fetch(url, { method: 'HEAD' });
        return respuesta.ok;
    } catch (error) {
        return false;
    }
}

// Devuelve la primera ruta que exista, o null.
async function primeraQueExista(rutas) {
    for (const ruta of rutas) {
        if (await existeArchivo(ruta)) return ruta;
    }
    return null;
}

async function mostrarLetraActual() {
    const letra = letras[indice];
    const enEstaLetra = indice;   // por si el usuario avanza antes de que termine la búsqueda

    contador.textContent = `${indice + 1} / ${letras.length}`;
    nombreEl.textContent = letra;
    progresoFill.style.width = `${(indice / letras.length) * 100}%`;
    btnSiguiente.textContent = (indice === letras.length - 1) ? 'Ir a practicar' : 'Siguiente Letra';

    imagenBox.innerHTML = '<span class="placeholder-icon">🤟</span>';
    videoBox.innerHTML = '<span class="placeholder-icon">🎥</span>';

    const nombre = encodeURIComponent(letra);
    const [rutaImagen, rutaVideo] = await Promise.all([
        primeraQueExista([`${BASE}imagenes/abecedario/${nombre}.png`,
                          `${BASE}imagenes/abecedario/${nombre}.jpg`,
                          `${BASE}imagenes/letras/${nombre}.png`]),
        primeraQueExista([`${BASE}videos/abecedario/${nombre}.mp4`,
                          `${BASE}videos/letras/${nombre}.mp4`])
    ]);

    if (enEstaLetra !== indice) return;

    if (rutaImagen) {
        imagenBox.innerHTML = `<img src="${rutaImagen}" alt="Seña de la letra ${letra}">`;
    }
    if (rutaVideo) {
        videoBox.innerHTML = `<video src="${rutaVideo}" controls playsinline
            aria-label="Video de cómo hacer la letra ${letra}"></video>`;
    }
}

btnSiguiente.addEventListener('click', () => {
    if (indice < letras.length - 1) {
        indice += 1;
        mostrarLetraActual();
    } else {
        progresoFill.style.width = '100%';
        // Terminar la teoría cuenta como actividad del día para la racha
        const ir = () => { window.location.href = `/practica?leccion=${window.LECCION.id}`; };
        fetch('/api/teoria/completar', { method: 'POST', keepalive: true }).then(ir, ir);
    }
});

document.addEventListener('DOMContentLoaded', () => {
    if (!letras.length) {
        contador.textContent = '';
        nombreEl.textContent = '';
        document.querySelector('.media-grid').innerHTML =
            '<p>Esta lección todavía no tiene contenido.</p>';
        btnSiguiente.hidden = true;
        return;
    }
    mostrarLetraActual();
});