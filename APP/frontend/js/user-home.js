// frontend/js/user-home.js

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const [respUsuario, respProgreso] = await Promise.all([
            fetch('/api/usuario-actual'),
            fetch('/api/progreso')
        ]);

        if (!respUsuario.ok || !respProgreso.ok) {
            window.location.href = '/login';
            return;
        }

        const usuario = await respUsuario.json();
        const progreso = await respProgreso.json();

        actualizarCabecera(usuario);
        renderizarInicio(progreso.bloques);

    } catch (error) {
        console.error('Error cargando los datos del usuario:', error);
    }
});

function actualizarCabecera(usuario) {
    const tituloHero = document.getElementById('user-greeting');
    if (tituloHero) tituloHero.textContent = `¡Hola, ${usuario.nombre}!`;

    const avatar = document.getElementById('user-avatar');
    if (avatar && usuario.nombre) avatar.textContent = usuario.nombre.charAt(0).toUpperCase();

    const rachaEl = document.getElementById('racha-val');
    if (rachaEl) rachaEl.textContent = usuario.racha;

    const xpEl = document.getElementById('xp-val');
    if (xpEl) xpEl.textContent = usuario.xp;
}

function renderizarInicio(bloques) {
    const mainContent = document.querySelector('.content');
    mainContent.innerHTML = '';

    const bloqueActivo = bloques.find(b => b.desbloqueado) || bloques[0];
    const heroSub = document.getElementById('hero-sub');
    if (heroSub && bloqueActivo) {
        const completadas = bloqueActivo.lecciones.filter(l => l.estado === 'completada').length;
        heroSub.textContent = `Vas ${completadas} de ${bloqueActivo.totalLecciones} pasos en ${bloqueActivo.titulo}. Sigue practicando para no perder tu racha.`;
    }

    bloques.forEach(bloque => {
        const completadas = bloque.lecciones.filter(l => l.estado === 'completada').length;
        const porcentaje = bloque.totalLecciones ? (completadas / bloque.totalLecciones) * 100 : 0;

        const bloqueDiv = document.createElement('div');
        bloqueDiv.className = `block ${!bloque.desbloqueado ? 'block--locked' : ''}`;

        let htmlBloque = `
            <div class="block-header">
                <div class="block-title">
                    <span class="block-badge">BLOQUE ${bloque.id}</span>
                    <h2>${bloque.titulo}</h2>
                </div>
                <span class="block-count">${completadas}/${bloque.totalLecciones}</span>
            </div>
        `;

        if (bloque.desbloqueado) {
            htmlBloque += `
                <div class="progress-track">
                    <div class="progress-fill" style="width:${porcentaje}%"></div>
                </div>`;
        } else {
            htmlBloque += `
                <div class="lock-banner">
                    <span>🔒</span> ${bloque.id > 1 ? `Se desbloquea al terminar el Bloque ${bloque.id - 1}` : 'Próximamente'}
                </div>`;
        }

        htmlBloque += `<div class="tile-grid">`;

        bloque.lecciones.forEach(leccion => {
            const etiquetaTipo = leccion.tipo === 'teoria' ? 'Teoría' : 'Práctica';
            let claseTile = "is-locked";
            let contenidoTile = `<span class="tile-icon">🔒</span><span class="tile-tipo">${etiquetaTipo}</span><span class="tile-rango">${leccion.titulo}</span>`;
            let disabledAttr = "disabled";

            if (leccion.estado === "completada") {
                claseTile = "is-done";
                contenidoTile = `<span class="tile-icon">✓</span><span class="tile-tipo">${etiquetaTipo}</span><span class="tile-rango">${leccion.titulo}</span>`;
                disabledAttr = "";
            } else if (leccion.estado === "actual") {
                claseTile = "is-current";
                contenidoTile = `<span class="tile-tipo">${etiquetaTipo}</span><span class="tile-rango">${leccion.titulo}</span>`;
                disabledAttr = "";
            }

            htmlBloque += `
                <button class="tile ${claseTile} tile--${leccion.tipo}" ${disabledAttr} onclick="iniciarLeccion('${leccion.id}')">
                    ${contenidoTile}
                </button>
            `;
        });

        htmlBloque += `</div>`;
        bloqueDiv.innerHTML = htmlBloque;
        mainContent.appendChild(bloqueDiv);
    });
}

// El id de cada tile viene como "<idLeccion>-teoria" o "<idLeccion>-practica",
// así que separamos el sufijo para saber a qué pantalla mandar y con qué id real.
function iniciarLeccion(idTile) {
    if (idTile.endsWith('-teoria')) {
        const idLeccion = idTile.replace(/-teoria$/, '');
        window.location.href = `/teoria?leccion=${idLeccion}`;
    } else if (idTile.endsWith('-practica')) {
        const idLeccion = idTile.replace(/-practica$/, '');
        window.location.href = `/practica?leccion=${idLeccion}`;
    }
}