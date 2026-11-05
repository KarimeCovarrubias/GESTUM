document.addEventListener('DOMContentLoaded', async () => {
    const avatarBtn = document.getElementById('user-avatar');
    const userDropdown = document.getElementById('user-dropdown');

    try {
        const respuesta = await fetch('/api/perfil');
        if (!respuesta.ok) {
            window.location.href = '/login';
            return;
        }
        pintarPerfil(await respuesta.json());
    } catch (error) {
        console.error('Error cargando el perfil:', error);
        document.getElementById('perfil-nombre').textContent = 'No se pudo cargar tu perfil';
    }

    // Menú desplegable del avatar (igual que en Inicio)
    if (avatarBtn && userDropdown) {
        avatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const abierto = avatarBtn.getAttribute('aria-expanded') === 'true';
            avatarBtn.setAttribute('aria-expanded', String(!abierto));
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

function dias(n) {
    return n === 1 ? '1 día' : `${n} días`;
}

function pintarPerfil(p) {
    const usuario = `@${p.nombreUsuario}`;
    const inicial = (p.nombreUsuario || p.nombre || '?').charAt(0).toUpperCase();

    // Tarjeta principal
    document.getElementById('perfil-nombre').textContent = p.nombreCompleto;
    document.getElementById('perfil-user').textContent = usuario;
    document.getElementById('perfil-avatar').textContent = inicial;

    // Números
    document.getElementById('perfil-xp').textContent = p.xp;
    document.getElementById('perfil-racha').textContent = p.racha;
    document.getElementById('perfil-racha-etiqueta').textContent =
        p.racha === 1 ? 'día de racha' : 'días de racha';
    document.getElementById('perfil-racha-max').textContent =
        p.rachaMaxima > 0 ? `Tu mejor racha: ${dias(p.rachaMaxima)}` : 'Practica hoy para empezar tu racha';
    document.getElementById('perfil-desde').textContent = p.miembroDesde || '—';

    // Barra superior y menú
    document.getElementById('racha-val').textContent = p.racha;
    document.getElementById('xp-val').textContent = p.xp;
    document.getElementById('user-avatar').textContent = inicial;
    document.getElementById('dropdown-username').textContent = usuario;

    pintarLogros(p.logros || []);
    pintarResumen(p.resumen || {});
}

function pintarLogros(logros) {
    const lista = document.getElementById('logros-lista');
    const hechos = logros.filter(l => l.desbloqueado).length;
    document.getElementById('logros-contador').textContent = logros.length ? `${hechos} de ${logros.length}` : '';

    // Desbloqueados primero; luego los que van más avanzados
    const orden = [...logros].sort((a, b) =>
        (b.desbloqueado - a.desbloqueado) || (b.progreso / b.meta - a.progreso / a.meta));

    lista.innerHTML = orden.map(l => `
        <div class="insignia-item ${l.desbloqueado ? 'desbloqueada' : 'bloqueada'}">
            <span class="insignia-icono">${l.icono}</span>
            <div class="insignia-info">
                <h4>${l.titulo}</h4>
                <p>${l.descripcion}</p>
                ${l.desbloqueado ? '' : `
                    <div class="insignia-barra"><span style="width:${Math.round(l.progreso / l.meta * 100)}%"></span></div>
                    <div class="insignia-meta">${l.progreso} / ${l.meta}</div>`}
            </div>
            ${l.desbloqueado ? '<span class="insignia-check">✓</span>' : ''}
        </div>`).join('');
}

function pintarResumen(r) {
    document.getElementById('res-pruebas').textContent = `${r.pruebasAprobadas ?? 0} de ${r.totalLecciones ?? 0}`;
    document.getElementById('res-letras').textContent = `${r.letrasDominadas ?? 0} de ${r.totalLetras ?? 28}`;
    document.getElementById('res-precision').textContent = r.precision == null ? '—' : `${r.precision}%`;
}