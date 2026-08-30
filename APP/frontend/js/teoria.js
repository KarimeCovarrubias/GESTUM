let indice = 0;
const letras = window.LECCION.letras || [];

const mediaBoxImg = document.getElementById('media-box-img');
const mediaBoxVideo = document.getElementById('media-box-video');
const contador = document.getElementById('letra-contador');
const nombreEl = document.getElementById('letra-nombre');
const btnSiguiente = document.getElementById('btn-siguiente');

async function existeArchivo(url) {
    try {
        const respuesta = await fetch(url, { method: 'HEAD' });
        return respuesta.ok;
    } catch (error) {
        return false;
    }
}

async function renderizarMedios() {
    const letra = letras[indice];
    const rutaImagen = `../frontend/imagenes/abecedario/${letra}.png`;
    const rutaVideo = `../frontend/videos/abecedario/${letra}.mp4`;

    // Cargar Imagen
    if (await existeArchivo(rutaImagen)) {
        mediaBoxImg.innerHTML = `<img src="${rutaImagen}" alt="Seña de la letra ${letra}">`;
    } else {
        mediaBoxImg.innerHTML = `<span class="sin-medio">Imagen no disponible</span>`;
    }

    // Cargar Video
    if (await existeArchivo(rutaVideo)) {
        mediaBoxVideo.innerHTML = `
            <video src="${rutaVideo}" autoplay loop muted playsinline
                   aria-label="Video explicativo de la letra ${letra}"></video>
        `;
    } else {
        mediaBoxVideo.innerHTML = `<span class="sin-medio">Video no disponible aún</span>`;
    }
}

async function mostrarLetraActual() {
    const letra = letras[indice];
    contador.textContent = `${indice + 1} / ${letras.length}`;
    nombreEl.textContent = letra;

    await renderizarMedios();

    btnSiguiente.textContent = (indice === letras.length - 1) ? 'Ir a practicar' : 'Siguiente Letra';
}

btnSiguiente.addEventListener('click', () => {
    if (indice < letras.length - 1) {
        indice += 1;
        mostrarLetraActual();
    } else {
        window.location.href = `/practica?leccion=${window.LECCION.id}`;
    }
});

document.addEventListener('DOMContentLoaded', () => {
    if (!letras.length) {
        contador.textContent = '';
        nombreEl.textContent = '';
        document.querySelector('.letra-card').innerHTML = '<p class="sin-medio">Esta lección todavía no tiene contenido.</p>';
        btnSiguiente.style.display = 'none';
        return;
    }
    mostrarLetraActual();
});