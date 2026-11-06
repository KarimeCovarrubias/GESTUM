const $ = (id) => document.getElementById(id);
let usuarioActual = '';

function toast(texto) {
    const t = $('toast');
    t.textContent = texto;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}

function mensaje(id, texto, ok) {
    const el = $(id);
    el.textContent = texto || '';
    el.className = 'cfg-msg' + (texto ? (ok ? ' ok' : ' error') : '');
}

async function api(url, cuerpo) {
    const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo)
    });
    let data = {};
    try { data = await r.json(); } catch (e) { /* respuesta sin JSON */ }
    return { ok: r.ok && data.ok !== false, data };
}

function pintarCabecera(d) {
    usuarioActual = d.nombreUsuario;
    $('racha-val').textContent = d.racha_actual ?? 0;
    $('xp-val').textContent = d.puntos_xp ?? 0;
    $('user-avatar').textContent = (d.nombreUsuario || '?').charAt(0).toUpperCase();
    $('dropdown-username').textContent = `@${d.nombreUsuario}`;
}

function rellenarFormulario(d) {
    $('c-nombre').value = d.nombre || '';
    $('c-apellidoP').value = d.apellidoP || '';
    $('c-apellidoM').value = d.apellidoM || '';
    $('c-edad').value = d.edad ?? '';
    $('c-usuario').value = d.nombreUsuario || '';
    $('c-correo').value = d.correo || '';
    $('aviso-correo').hidden = !!d.correo;
}

// ---------- Usuario único (comprobación en vivo) ----------
let esperaUsuario = null;
$('c-usuario').addEventListener('input', () => {
    const hint = $('c-usuario-hint');
    const valor = $('c-usuario').value.trim();
    clearTimeout(esperaUsuario);
    hint.className = 'cfg-hint';
    if (valor === usuarioActual) { hint.textContent = 'Es tu usuario actual'; return; }
    hint.textContent = '';
    if (valor.length < 3) return;
    esperaUsuario = setTimeout(async () => {
        try {
            const r = await fetch('/api/usuario/disponible?nombre=' + encodeURIComponent(valor));
            const d = await r.json();
            hint.textContent = d.disponible ? '✓ Disponible' : '✗ ' + d.mensaje;
            hint.className = 'cfg-hint ' + (d.disponible ? 'ok' : 'error');
        } catch (e) { /* sin conexión: se validará al guardar */ }
    }, 400);
});

// ---------- Guardar cuenta ----------
$('form-cuenta').addEventListener('submit', async (e) => {
    e.preventDefault();
    mensaje('msg-cuenta', '');
    const { ok, data } = await api('/api/configuracion/perfil', {
        nombre: $('c-nombre').value,
        apellidoP: $('c-apellidoP').value,
        apellidoM: $('c-apellidoM').value,
        edad: $('c-edad').value,
        nombreUsuario: $('c-usuario').value,
        correo: $('c-correo').value
    });
    if (!ok) { mensaje('msg-cuenta', data.mensaje || 'No se pudo guardar.', false); return; }
    pintarCabecera(data);
    rellenarFormulario(data);
    $('c-usuario-hint').textContent = '';
    toast('Cambios guardados ✓');
});

// ---------- Cambiar contraseña ----------
$('form-contrasena').addEventListener('submit', async (e) => {
    e.preventDefault();
    mensaje('msg-contrasena', '');
    if ($('p-nueva').value.length < 8) { mensaje('msg-contrasena', 'La contraseña nueva debe tener al menos 8 caracteres.', false); return; }
    if ($('p-nueva').value !== $('p-repite').value) { mensaje('msg-contrasena', 'Las contraseñas nuevas no coinciden.', false); return; }
    const { ok, data } = await api('/api/configuracion/contrasena', {
        actual: $('p-actual').value, nueva: $('p-nueva').value
    });
    if (!ok) { mensaje('msg-contrasena', data.mensaje || 'No se pudo cambiar.', false); return; }
    $('form-contrasena').reset();
    toast('Contraseña actualizada ✓');
});

// ---------- Apariencia (tema) ----------
function marcarTema() {
    const actual = window.GestumTema ? window.GestumTema.obtener() : 'claro';
    document.querySelectorAll('.cfg-tema').forEach(b => {
        const activo = b.dataset.temaOpcion === actual;
        b.classList.toggle('activo', activo);
        b.setAttribute('aria-checked', String(activo));
    });
}
document.querySelectorAll('.cfg-tema').forEach(b => {
    b.addEventListener('click', () => {
        if (window.GestumTema) window.GestumTema.establecer(b.dataset.temaOpcion);
        marcarTema();
    });
});
marcarTema();

// ---------- Cámara ----------
const CLAVE_CAMARA = 'gestum_camara';
let streamPreview = null;

function camaraGuardada() {
    try { return localStorage.getItem(CLAVE_CAMARA) || ''; } catch (e) { return ''; }
}
function guardarCamara(id) {
    try { id ? localStorage.setItem(CLAVE_CAMARA, id) : localStorage.removeItem(CLAVE_CAMARA); } catch (e) { /* sin almacenamiento */ }
}

function detenerPreview() {
    if (streamPreview) streamPreview.getTracks().forEach(t => t.stop());
    streamPreview = null;
}

async function mostrarPreview() {
    detenerPreview();
    const id = $('camara-select').value;
    try {
        streamPreview = await navigator.mediaDevices.getUserMedia({
            video: id ? { deviceId: { exact: id } } : true, audio: false
        });
        $('camara-preview').srcObject = streamPreview;
        $('camara-preview').classList.add('activa');
        mensaje('msg-camara', '');
    } catch (error) {
        $('camara-preview').classList.remove('activa');
        mensaje('msg-camara', 'No se pudo abrir esa cámara. Revisa que no la use otra app y que el navegador tenga permiso.', false);
    }
}

async function detectarCamaras() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        mensaje('msg-camara', 'Tu navegador no permite elegir cámara.', false);
        return;
    }
    try {
        // Hace falta el permiso para que el navegador muestre los nombres de las cámaras
        const temporal = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        temporal.getTracks().forEach(t => t.stop());
    } catch (error) {
        mensaje('msg-camara', 'Permite el acceso a la cámara en el navegador para detectarlas.', false);
        return;
    }
    const camaras = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput');
    const guardada = camaraGuardada();
    const select = $('camara-select');
    select.innerHTML = '<option value="">Predeterminada del navegador</option>' +
        camaras.map((c, i) => `<option value="${c.deviceId}">${c.label || 'Cámara ' + (i + 1)}</option>`).join('');
    select.value = camaras.some(c => c.deviceId === guardada) ? guardada : '';
    mensaje('msg-camara', camaras.length ? `Se encontraron ${camaras.length} cámara(s).` : 'No se encontró ninguna cámara.', camaras.length > 0);
    mostrarPreview();
}

$('btn-detectar').addEventListener('click', detectarCamaras);
$('camara-select').addEventListener('change', () => {
    guardarCamara($('camara-select').value);
    mostrarPreview();
    toast('Cámara guardada ✓');
});
window.addEventListener('beforeunload', detenerPreview);

// ---------- Zona delicada (confirmar con contraseña) ----------
let accionPendiente = null;

function abrirModal({ titulo, texto, boton, url, despues }) {
    accionPendiente = { url, despues };
    $('modal-titulo').textContent = titulo;
    $('modal-texto').textContent = texto;
    $('modal-confirmar').textContent = boton;
    $('modal-contrasena').value = '';
    mensaje('modal-error', '');
    $('modal').hidden = false;
    $('modal-contrasena').focus();
}
function cerrarModal() { $('modal').hidden = true; accionPendiente = null; }

$('btn-reiniciar').addEventListener('click', () => abrirModal({
    titulo: '¿Reiniciar tu progreso?',
    texto: 'Perderás tus XP, tu racha, tus logros y el avance de todas las lecciones.',
    boton: 'Sí, reiniciar',
    url: '/api/configuracion/reiniciar-progreso',
    despues: () => { window.location.href = '/user-home'; }
}));
$('btn-eliminar').addEventListener('click', () => abrirModal({
    titulo: '¿Eliminar tu cuenta?',
    texto: 'Se borrará tu cuenta y todo tu progreso para siempre. No se puede deshacer.',
    boton: 'Sí, eliminar mi cuenta',
    url: '/api/configuracion/eliminar-cuenta',
    despues: () => { window.location.href = '/login'; }
}));

$('modal-cancelar').addEventListener('click', cerrarModal);
$('modal').addEventListener('click', (e) => { if (e.target === $('modal')) cerrarModal(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('modal').hidden) cerrarModal(); });
$('modal-contrasena').addEventListener('keydown', (e) => { if (e.key === 'Enter') $('modal-confirmar').click(); });

$('modal-confirmar').addEventListener('click', async () => {
    if (!accionPendiente) return;
    const contrasena = $('modal-contrasena').value;
    if (!contrasena) { mensaje('modal-error', 'Escribe tu contraseña.', false); return; }
    const { ok, data } = await api(accionPendiente.url, { contrasena });
    if (!ok) { mensaje('modal-error', data.mensaje || 'No se pudo completar.', false); return; }
    accionPendiente.despues();
});

// ---------- Carga inicial y menú del avatar ----------
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const r = await fetch('/api/configuracion');
        if (!r.ok) { window.location.href = '/login'; return; }
        const d = await r.json();
        pintarCabecera(d);
        rellenarFormulario(d);
    } catch (error) {
        mensaje('msg-cuenta', 'No se pudieron cargar tus datos.', false);
    }

    const avatarBtn = $('user-avatar');
    const menu = $('user-dropdown');
    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const abierto = avatarBtn.getAttribute('aria-expanded') === 'true';
        avatarBtn.setAttribute('aria-expanded', String(!abierto));
        menu.classList.toggle('show');
    });
    document.addEventListener('click', (e) => {
        if (!menu.contains(e.target) && e.target !== avatarBtn) {
            menu.classList.remove('show');
            avatarBtn.setAttribute('aria-expanded', 'false');
        }
    });

    // Si ya había una cámara elegida, la lista se llena al detectar; mientras tanto se muestra aviso
    if (camaraGuardada()) mensaje('msg-camara', 'Hay una cámara guardada. Pulsa "Detectar cámaras" para cambiarla.', true);
});