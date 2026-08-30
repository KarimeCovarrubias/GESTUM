document.addEventListener('DOMContentLoaded', async () => {
    // 1. Elementos del DOM del menú desplegable
    const avatarBtn = document.getElementById('user-avatar');
    const userDropdown = document.getElementById('user-dropdown');

    // 2. Cargar datos del usuario y progreso de la plataforma
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

        // Asignar dinámicamente el destino del botón "Continuar lección"
        const btnContinuar = document.getElementById('btn-continuar-leccion');
        if (btnContinuar && progreso.url_continuar) {
            btnContinuar.href = progreso.url_continuar;
        }

    } catch (error) {
        console.error('Error cargando los datos del usuario:', error);
    }

    // 3. Control del menú desplegable del avatar
    if (avatarBtn && userDropdown) {
        avatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = avatarBtn.getAttribute('aria-expanded') === 'true';
            avatarBtn.setAttribute('aria-expanded', !isExpanded);
            userDropdown.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target) && e.target !== avatarBtn) {
                userDropdown.classList.remove('show');
                avatarBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }
});

function actualizarCabecera(usuario) {
    const username = usuario.nombreUsuario || usuario.username || usuario.nombre_usuario || usuario.nombre || 'Usuario';
    const usernameConArroba = `@${username}`;

    const tituloHero = document.getElementById('user-greeting');
    if (tituloHero) tituloHero.textContent = `¡Hola, ${usernameConArroba}!`;

    const dropdownUsername = document.getElementById('dropdown-username');
    if (dropdownUsername) dropdownUsername.textContent = usernameConArroba;

    const avatar = document.getElementById('user-avatar');
    if (avatar) avatar.textContent = username.charAt(0).toUpperCase();

    const rachaEl = document.getElementById('racha-val');
    if (rachaEl) rachaEl.textContent = usuario.racha || 0;

    const xpEl = document.getElementById('xp-val');
    if (xpEl) xpEl.textContent = usuario.xp || 0;
}

function renderizarInicio(bloques) {
    const mainContent = document.querySelector('.content');
    if (!mainContent) return;
    mainContent.innerHTML = '';

    const bloqueActivo = bloques.find(b => b.desbloqueado) || bloques[0];
    const heroSub = document.getElementById('hero-sub');
    if (heroSub && bloqueActivo) {
        const completadas = bloqueActivo.lecciones.filter(l => l.estado === 'completada').length;
        heroSub.textContent = `Llevas ${completadas} de ${bloqueActivo.totalLecciones} lecciones en ${bloqueActivo.titulo}. Sigue practicando para no perder tu racha.`;
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

function iniciarLeccion(idTile) {
    if (idTile.endsWith('-teoria')) {
        const idLeccion = idTile.replace(/-teoria$/, '');
        window.location.href = `/teoria?leccion=${idLeccion}`;
    } else if (idTile.endsWith('-practica')) {
        const idLeccion = idTile.replace(/-practica$/, '');
        window.location.href = `/practica?leccion=${idLeccion}`;
    }
}