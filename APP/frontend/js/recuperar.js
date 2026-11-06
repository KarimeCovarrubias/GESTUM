// Sirve a las dos pantallas: /olvide (pide el enlace) y /restablecer (guarda la nueva contraseña).

function msg(texto, ok) {
    const el = document.getElementById('msg');
    el.textContent = texto || '';
    el.className = 'rec-msg' + (texto ? (ok ? ' ok' : ' error') : '');
}

async function enviar(url, cuerpo) {
    const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo)
    });
    let data = {};
    try { data = await r.json(); } catch (e) { /* sin JSON */ }
    return { ok: r.ok && data.ok !== false, data };
}

const formOlvide = document.getElementById('form-olvide');
if (formOlvide) {
    formOlvide.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn');
        const correo = document.getElementById('correo').value.trim();
        if (!correo) { msg('Escribe tu correo.', false); return; }
        btn.disabled = true;
        msg('');
        try {
            const { ok, data } = await enviar('/api/recuperar', { correo });
            msg(data.mensaje || (ok ? 'Listo.' : 'No se pudo enviar.'), ok);
            if (ok) btn.textContent = 'Enviar de nuevo';
        } catch (error) {
            msg('No se pudo conectar con el servidor.', false);
        }
        btn.disabled = false;
    });
}

const formRestablecer = document.getElementById('form-restablecer');
if (formRestablecer) {
    formRestablecer.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn');
        const nueva = document.getElementById('nueva').value;
        if (nueva.length < 8) { msg('La contraseña debe tener al menos 8 caracteres.', false); return; }
        if (nueva !== document.getElementById('repite').value) { msg('Las contraseñas no coinciden.', false); return; }
        btn.disabled = true;
        try {
            const { ok, data } = await enviar('/api/restablecer', {
                token: formRestablecer.dataset.token, contrasena: nueva
            });
            msg(data.mensaje || (ok ? 'Listo.' : 'No se pudo guardar.'), ok);
            if (ok) { setTimeout(() => { window.location.href = '/login'; }, 1800); return; }
        } catch (error) {
            msg('No se pudo conectar con el servidor.', false);
        }
        btn.disabled = false;
    });
}