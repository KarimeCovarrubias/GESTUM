document.addEventListener('DOMContentLoaded', async () => {
    try {
        const [respUsuario, respProgreso] = await Promise.all([
            fetch('/api/usuario-actual'),
            fetch('/api/progreso')
        ]);

        if (!respUsuario.ok || !respProgreso.ok) {
            // Sin sesión activa (o algo falló) -> mandar a login
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

// Actualiza el saludo, avatar y estadísticas del topbar con datos reales
function actualizarCabecera(usuario) {
    const tituloHero = document.getElementById('user-greeting');
    if (tituloHero) {
        tituloHero.textContent = `¡Hola, ${usuario.nombre}!`;
    }

    const avatar = document.getElementById('user-avatar');
    if (avatar && usuario.nombre) {
        avatar.textContent = usuario.nombre.charAt(0).toUpperCase();
    }

    const rachaEl = document.getElementById('racha-val');
    if (rachaEl) rachaEl.textContent = usuario.racha;

    const xpEl = document.getElementById('xp-val');
    if (xpEl) xpEl.textContent = usuario.xp;
}

// Renderiza los bloques/lecciones con el progreso real del usuario
function renderizarInicio(bloques) {
    const mainContent = document.querySelector('.content');
    mainContent.innerHTML = '';

    // Actualiza el subtítulo del hero con el primer bloque implementado
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
            let claseTile = "is-locked";
            let contenidoTile = `<span class="tile-icon">🔒</span>${leccion.titulo}`;
            let disabledAttr = "disabled";

            if (leccion.estado === "completada") {
                claseTile = "is-done";
                contenidoTile = `<span class="tile-icon">✓</span>${leccion.titulo}`;
                disabledAttr = "";
            } else if (leccion.estado === "actual") {
                claseTile = "is-current";
                contenidoTile = leccion.titulo;
                disabledAttr = "";
            }

            htmlBloque += `
                <button class="tile ${claseTile}" ${disabledAttr} onclick="iniciarLeccion('${leccion.id}')">
                    ${contenidoTile}
                </button>
            `;
        });

        htmlBloque += `</div>`;
        bloqueDiv.innerHTML = htmlBloque;
        mainContent.appendChild(bloqueDiv);
    });
}

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
        configurarMenuAvatar(); // Inicializa los eventos del menú desplegable

    } catch (error) {
        console.error('Error cargando los datos del usuario:', error);
    }
});

function actualizarCabecera(usuario) {
    const tituloHero = document.getElementById('user-greeting');
    if (tituloHero) {
        tituloHero.textContent = `¡Hola, ${usuario.nombre}!`;
    }

    const avatar = document.getElementById('user-avatar');
    if (avatar && usuario.nombre) {
        avatar.textContent = usuario.nombre.charAt(0).toUpperCase();
    }

    // Actualizar nombre dentro del dropdown del avatar
    const dropdownUsername = document.getElementById('dropdown-username');
    if (dropdownUsername && usuario.nombreUsuario) {
        dropdownUsername.textContent = `@${usuario.nombreUsuario}`;
    }

    const rachaEl = document.getElementById('racha-val');
    if (rachaEl) rachaEl.textContent = usuario.racha;

    const xpEl = document.getElementById('xp-val');
    if (xpEl) xpEl.textContent = usuario.xp;
}

// Lógica para desplegar/ocultar el menú al hacer clic en el avatar (Opción 1)
function configurarMenuAvatar() {
    const avatarBtn = document.getElementById('user-avatar');
    const dropdown = document.getElementById('user-dropdown');

    if (!avatarBtn || !dropdown) return;

    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && e.target !== avatarBtn) {
            dropdown.classList.remove('show');
        }
    });
}

function renderizarInicio(bloques) {
    const mainContent = document.querySelector('.content');
    mainContent.innerHTML = '';

    const bloqueActivo = bloques.find(b => b.desbloqueado) || bloques[0];
    const heroSub = document.getElementById('hero-sub');
    if (heroSub && bloqueActivo) {
        const completadas = bloqueActivo.lecciones.filter(l => l.estado === 'completada').length;
        heroSub.textContent = `Levas ${completadas} de ${bloqueActivo.totalLecciones} lecciones en ${bloqueActivo.titulo}. Sigue practicando para no perder tu racha.`;
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
            let claseTile = "is-locked";
            let contenidoTile = `<span class="tile-icon">🔒</span>${leccion.titulo}`;
            let disabledAttr = "disabled";

            if (leccion.estado === "completada") {
                claseTile = "is-done";
                contenidoTile = `<span class="tile-icon">✓</span>${leccion.titulo}`;
                disabledAttr = "";
            } else if (leccion.estado === "actual") {
                claseTile = "is-current";
                contenidoTile = leccion.titulo;
                disabledAttr = "";
            }

            htmlBloque += `
                <button class="tile ${claseTile}" ${disabledAttr} onclick="iniciarLeccion('${leccion.id}')">
                    ${contenidoTile}
                </button>
            `;
        });

        htmlBloque += `</div>`;
        bloqueDiv.innerHTML = htmlBloque;
        mainContent.appendChild(bloqueDiv);
    });
}

function iniciarLeccion(idLeccion) {
    window.location.href = `practica.html?leccion=${idLeccion}`;
}

// Redirige a la vista de práctica de la lección elegida
function iniciarLeccion(idLeccion) {
    window.location.href = `/practica?leccion=${idLeccion}`;
}