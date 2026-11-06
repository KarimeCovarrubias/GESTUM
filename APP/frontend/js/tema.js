// Tema claro / oscuro / automático. Se carga en el <head> de cada página (sin defer)
// para pintar el tema correcto desde el primer momento y evitar el "parpadeo" blanco.
// La elección se guarda en este navegador (localStorage), no en la cuenta.
(function () {
    var CLAVE = 'gestum_tema';   // 'claro' | 'oscuro' | 'auto'
    var sistema = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

    function guardado() {
        try { return localStorage.getItem(CLAVE) || 'claro'; } catch (e) { return 'claro'; }
    }

    function aplicar(modo) {
        var oscuro = modo === 'oscuro' || (modo === 'auto' && sistema && sistema.matches);
        document.documentElement.setAttribute('data-tema', oscuro ? 'oscuro' : 'claro');
    }

    aplicar(guardado());

    // En modo automático, sigue los cambios del sistema operativo
    function alCambiarSistema() { if (guardado() === 'auto') aplicar('auto'); }
    if (sistema) {
        if (sistema.addEventListener) sistema.addEventListener('change', alCambiarSistema);
        else if (sistema.addListener) sistema.addListener(alCambiarSistema);
    }
    // Otra pestaña cambió el tema
    window.addEventListener('storage', function (e) {
        if (e.key === CLAVE) aplicar(guardado());
    });

    window.GestumTema = {
        obtener: guardado,
        establecer: function (modo) {
            try { 
                localStorage.setItem(CLAVE, modo); 
            } catch (e) {
                /* sin almacenamiento */
            }
            aplicar(modo);
        }
    };
})();