# Steel

Versión pública para **Arch/CachyOS + Hyprland con configuración Lua**. Composición de Illogical Impulse, decoraciones inicialmente derivadas de cybrdots y una base propia de acero oscuro: `#161a1f`, blur y colores comunes entre aplicaciones compatibles.

## Instalar en la laptop

```sh
git clone https://github.com/serpiero/steel-dotfiles-public.git
cd steel-dotfiles-public
./install.sh --verify-source
./install.sh --check
# Si faltan dependencias: actualiza Arch e instala las necesarias.
./install.sh --dependencies
./install.sh --install
```

La instalación respalda `~/.config/hypr/hyprland.lua`, instala en `~/.local/share/rice-profiles` y verifica la configuración antes de darla por válida. No reinicia Hyprland ni cierra las aplicaciones: vuelve a iniciar la sesión de Hyprland cuando estés listo. Conserva KDE. Si ya existe una instalación de rice-profiles, se detiene para preservar tus ajustes.

Quickshell se compila desde una revisión fija con el parche WebEngine incluido. Es necesario compilarlo contra la versión de Qt de la laptop; copiar el ejecutable de otra máquina puede romper su ABI. Usa dos trabajos de compilación por defecto para contener el uso de memoria; cambia `OBSIDIAN_BUILD_JOBS` si lo necesitas. La compilación puede tardar. No instala AUR automáticamente ni cambia el paquete Hyprland: su soporte Lua ya debe funcionar.

Los monitores usan resolución preferida y detección automática. Ajusta la laptop en `~/.local/share/rice-profiles/local.lua`, que se carga al final y nunca se comparte. No se copian reglas de monitores, entrada o atajos personales de la computadora de origen. La configuración previa permanece en el respaldo.

## Navegador y aplicaciones

```sh
python3 ~/.local/share/rice-profiles/tools/firefox-theme.py
```

El adaptador crea un perfil limpio de Firefox dedicado a Steel en Hyprland. No modifica el perfil de KDE ni copia cookies, sesiones o extensiones. Inicia sesión tú mismo en el perfil nuevo. El navegador usa Wayland; los controles y páginas se agrandan únicamente en la pantalla pequeña de alta densidad del teléfono. Google usa resultados anchos y centrados en escritorio; DuckDuckGo admite su ajuste nativo de ancho. El adaptador no cambia tu perfil original. Instala Dark Reader desde el catálogo oficial de Firefox y configura modo dinámico, detección de tema oscuro desactivada y los colores de `obsidian/firefox/darkreader-palette.json`. Ese archivo es una receta; no es una copia de tu almacenamiento de extensiones.

GTK/Qt reciben configuraciones locales derivadas de las preferencias de la laptop. Code, Kitty/Alacritty/Konsole, Kate/KWrite, MiniMeters y qBittorrent tienen ajustes propios. Discord se mantiene con el cliente del paquete de Arch y conserva la ruta original del actualizador; el tema vive en una copia privada. Spotify usa el paquete nativo `spotify`: se copia una versión completa y coherente del cliente y se añade únicamente CSS, conservando su JavaScript. El ejecutable y `libcef.so` nunca se mezclan entre versiones; la copia se renueva al actualizar el paquete o el tema. El antiguo instalador de Spicetify está retirado. Las cuentas permanecen en la máquina de destino.

Las interfaces propias de Wine/Ableton, juegos y otros motores necesitan trabajo específico; no se promete uniformidad absoluta. MiniMeters conserva sus parámetros de audio; su revisión funcional sigue pendiente. Aerion solo utiliza su adaptador si hay WebKitGTK 4.1 y compilador disponibles.

La fuente de iconos Material Symbols Rounded se descarga de Google con revisión y SHA-256 fijados, e incluye licencia y procedencia. Los nombres de fuentes actuales se conservan; si no están instaladas, Qt utiliza sustitución. Noto Sans y JetBrains Mono Nerd Font están en las dependencias. No se redistribuyen fuentes personales.

## Tema central y ajustes

[`themes/steel.json`](themes/steel.json) es la fuente común de colores, escala del teléfono y tamaños del layout. [`styles/`](styles/) contiene las reglas por aplicación; los CSS de `obsidian/` son resultados generados. [`theme.py`](theme.py) valida, resuelve alias y compila los adaptadores. [`palette.py`](palette.py) lleva esos colores a Quickshell, GTK, Qt, terminal, prompt y btop; los menús y colores de Hyprland usan la misma fuente.

```sh
python3 theme.py check
python3 theme.py render     # Compilar sin abrir ni cerrar aplicaciones.
python3 theme.py apply      # Aplicar a una instalación activa.
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Para cambiar el color general, edita `palette.colors.background`, `accent`, `text`, etc. Los alias como `"surface": "{background}"` mantienen las superficies relacionadas. Para crear otra variante, copia el JSON a `themes/otro.json` y guarda `{"theme":"otro"}` en `theme-selection.json`. Los ajustes personales van en `local-theme.json`: se combinan recursivamente con la variante y están excluidos de Git. Los tamaños y controles permanecen separados de la paleta; el color de la terminal puede variar sin alterar el resto.

El modo `fixed` usa la paleta declarada. En modo `wallpaper`, los tokens que omitas en `palette.colors` se derivan del wallpaper; los que mantengas son overrides explícitos. La sesión detecta cambios de tokens, plantillas y adaptadores; no depende solo de que cambie la imagen. Firefox carga sus CSS al abrirse y Dark Reader requiere actualizar su receta cuando cambias de variante. Los clientes Electron/Spotify actualizan la copia temática al volver a abrirlos.

La escala adicional del navegador está limitada por la consulta de pantalla pequeña y densidad alta. En este equipo distingue el Samsung del MSI; una pantalla física de tamaño lógico y densidad similares también puede cumplir la condición. Los límites y zooms se configuran en `layout.phone`.

## WhatsApp

Instala el archivo generado [`features/whatsapp/whatsapp.user.js`](features/whatsapp/whatsapp.user.js) en Tampermonkey. Solo se ejecuta en WhatsApp Web. Los dos botones de la barra lateral permiten ocultar/restaurar la lista y alternar nombres/previews con solo fotos de perfil. En modo completo, arrastra su borde derecho, usa las flechas con el separador enfocado o haz doble clic para restaurar el ancho. Al reducir la ventana con un chat abierto, se prioriza el chat y la lista se compacta.

El modo compacto mantiene los avatares nativos, sus máscaras SVG y la marca de mensajes temporales: no clona las imágenes. Los previews se ocultan por completo. El ancho y modo se guardan localmente; no se exportan chats, nombres ni fotos. Ajusta sus valores iniciales en `layout.whatsapp` y vuelve a generar/reinstalar el script si los cambias.

Las páginas de Intelligence con `navigation: true` incluyen atrás, adelante, inicio y recargar; ChatGPT y Gemini mantienen solo sus pestañas. La carga inicial muestra `Loading`. Intelligence se crea al abrir el panel y se destruye tres segundos después de cerrarlo, salvo que esté resolviendo una descarga pendiente. No hay precarga en segundo plano. El inicio de sesión se conserva en el perfil del navegador; volver a abrir requiere cargar la página. Mientras el panel está abierto, las pestañas ocultas también se descartan a los tres segundos por defecto. `discardWhenHidden: false` permite retener una pestaña durante esa apertura, sin impedir la liberación al cerrar el panel.

El popup de música muestra solo fuentes que están reproduciendo. Al detenerse la última, se cierra y libera sus tarjetas y el visualizador; no crea una tarjeta vacía para navegadores precargados.

Las aplicaciones de terminal usan un lanzador explícito de Kitty y argumentos separados. Así CachyUpdate abre correctamente desde el menú y el tray; si está instalado, su applet arranca con Hyprland. Steel Settings usa una regla propia flotante de 900×650. La barra resuelve nombres desde las entradas de escritorio, también para web apps de Firefox.

Aerion recibe la paleta como canales HSL, conservando sus fondos opacos y el layout original. El inyector se limita al marco principal de la aplicación: no recolorea los documentos de correo. El lanzador resuelve el ejecutable nativo una sola vez y usa la configuración original de Aerion. Si ya está activado su autostart, conserva el inicio oculto; una apertura manual muestra la ventana después de esa inicialización.

Las páginas se eligen en `ui/settings/config.json`, dentro de `sidebar.web.sites`. La configuración básica contiene ChatGPT y Gemini. Cada entrada acepta `id`, `name`, `url`, `zoom` (opcional, 0.9 por defecto), `navigation` (opcional, falso por defecto) y `theme` (opcional). `compact-forum` adapta una página de foro al panel estrecho y aplica la paleta común; solo actúa en el dominio de inicio de esa entrada. Las páginas y sesiones personales no se añaden al export público.

Los iconos de workspaces usan la implementación de Illogical Impulse: AppIcon/Kirigami, tamaño redondeado de 18 px, máscara circular y tinte común, con las animaciones y márgenes originales. Se resuelven desde las entradas de escritorio y el tema local de iconos; `workspace_icons.py` genera un índice local de archivos de imagen, priorizando SVG. La barra carga esos archivos directamente para que la escala de otro monitor no seleccione un dibujo diferente. El índice se regenera durante la compilación del tema y no se exporta a Git. ChatGPT utiliza un emblema vectorial plano exclusivo de este widget; `monochromeIcons` controla su grado de tinte. El botón de Intelligence utiliza el cerebro de Material Symbols.

## RuTracker opcional

[`features/rutracker/`](features/rutracker/README.md) incluye un userscript con portada de logo/buscador centrados y cabecera compacta en resultados. Las opciones avanzadas empiezan ocultas y se abren con un botón. Con Visual Enhancer 1, la fila Filter → Columns → SO permanece visible; View options despliega Visual, S/M/L, Light/Dark e Infinite scroll. Visual Enhancer 2 conserva su botón VE y su diseño, controles y preferencias originales. Traduce localmente los controles comunes al inglés. Usa el formulario nativo y la paleta compartida, incluyendo controles y tarjetas de la extensión de previews; conserva sus funciones y ajustes.

## Pantalla USB opcional

[`features/phone-display/README.md`](features/phone-display/README.md) documenta el vigilante del teléfono. La instalación general no crea una salida virtual ni activa VNC por defecto. La geometría y los bloques de workspaces personales se mantienen en `local.lua`.

El control USB del teléfono es independiente de la pantalla virtual: con `scrcpy` instalado, `Super+Alt+O` entra al Samsung sin terminal ni icono, y `Alt` devuelve cursor/foco a la aplicación anterior y apaga OTG. Cada nueva pulsación vuelve a entrar; no funciona como un interruptor alternante. El cursor de Hyprland se oculta desde el inicio del cambio y recupera su visibilidad previa al salir o si falla el arranque. No aparecen notificaciones de OTG. La ventana de entrada es transparente, de 16×16 píxeles, y se excluye de los workspaces y previews de la barra. El atajo espera que sueltes los modificadores y activa la captura SDL3 al ganar foco, sin simular teclas ni enviar un clic al teléfono. Super devuelve el foco antes de ejecutar acciones de ventanas. El control automático requiere `scrcpy`, SDL3/cc y `ydotool` con su servicio de usuario activo (`systemctl --user enable --now ydotool.service`). El adaptador se compila localmente con SDL3/cc y solo se carga en el proceso OTG; responde a eventos, sin otro vigilante. El servicio temporal no arranca automáticamente ni captura vídeo/audio; no modifica VNC o monitores. El helper solo detiene sesiones OTG; nunca cierra mirroring normal. Sus registros quedan en `journalctl --user -u steel-phone-otg.service`.

## Atajos principales

| Atajo | Acción |
|---|---|
| Super+Return / Super+T / Ctrl+Alt+T | Terminal |
| Super+A | Panel izquierdo |
| Ctrl+Super+A | Intelligence |
| Super+N | Panel derecho |
| Super+/ | Lista de atajos |
| Super+I | Settings de Obsidian |
| Super+V / Super+Alt+Space | Alternar ventana flotante/mosaico |
| Super+H | Historial del portapapeles |
| Super+R | Steel Spotlight |
| Super+Alt+O / Alt | Entrar al teléfono / salir y apagar OTG |
| Ctrl+Super+T | Wallpaper |
| Super+Shift+S | Seleccionar y anotar captura |
| Print | Pantalla completa |
| Ctrl+Print | Ventana activa |
| Ctrl+Super+Alt+Slash | Editar atajos de Obsidian |
| Ctrl+Super+Alt+P | Selector de perfiles |

La selección de captura permanece al hacer clic fuera. Ocho tiradores y todos los bordes permiten cambiar el tamaño. “Seleccionar” comienza otra selección. Enter/Ctrl+C copian, Ctrl+S guarda, Esc cancela. La barra de herramientas utiliza la paleta activa y blur de la imagen congelada.

Los settings muestran la base fija, transparencia de paneles, blur del sistema y acciones efectivas. El botón de configuración abre el archivo real de este fork. No se ofrecen los generadores heredados de colores que aquí están desactivados.

## Restaurar

```sh
python3 ~/.local/share/rice-profiles/tools/uninstall.py
```

Restaura el archivo previo y los lanzadores originales; conserva la instalación retirada y su estado local en el respaldo. Si modificaste el archivo principal de Hyprland después de instalar, se detiene para que conserves tus cambios. El perfil limpio de Firefox de Steel queda conservado dentro de la instalación retirada; tu perfil original de KDE no se modifica. Vuelve a iniciar sesión para terminar la restauración.

## Privacidad y fuente

Este repositorio solo contiene fuentes, temas y una paleta generada. **No contiene cookies, cuentas, tokens, perfiles de navegador, chats, historial, descargas, cachés, clientes parcheados ni respaldos.** Intelligence inicia sin tus sesiones. El wallpaper personal se sustituye por el SVG incluido; puedes elegir el tuyo después de instalar.

`tools/audit-export.py` comprueba las rutas prohibidas y los patrones de credenciales antes de compartir. `.gitignore` impide añadir el estado generado habitual. No conviertas la carpeta instalada en un repositorio público ni copies todo su contenido de vuelta aquí.

Procedencia y licencias: [Illogical Impulse](https://github.com/end-4/dots-hyprland), [cybrdots/cybr-hyprland](https://github.com/cybrcore/cybr-hyprland), [Quickshell](https://github.com/quickshell-mirror/quickshell), [Material Symbols](https://github.com/google/material-design-icons). Se conservan avisos y licencias en `licenses/` y `web-runtime/`. El fork se distribuye bajo GPL-3.0; los componentes conservan sus licencias respectivas.

## Validación actual

Se verificó la instalación y restauración en un HOME temporal con el ejecutable Quickshell compatible ya compilado en la computadora de origen. La configuración Lua pasó el verificador. La compilación desde cero y la experiencia real en la laptop todavía deben comprobarse allí. Las capturas tienen pruebas de clic fuera y de los ocho tiradores; se comprobaron los settings y los perfiles de Hyprland.


## Controles y consumo

General conserva sus secciones e incorpora controles funcionales del panel derecho. Los toggles originales editables se eligen mediante `sidebar.quickToggles.style: "android"`; el lápiz permite añadir, ocultar y reordenar los controles disponibles. Los sliders separados permanecen ocultos por defecto. Game mode está fuera de la lista inicial; en el panel clásico lo controla `classic.showGameMode`. Solo reduce efectos visuales, no instala ni activa un optimizador externo.

Bar incluye una opción para ocultar el fondo, sin cambiar el diseño predeterminado. La lista Super+/ se obtiene de los atajos activos de Hyprland y conserva sus categorías; los nombres de este fork aparecen como Steel. El tray conserva los estados del icono de CachyUpdate y sus avisos usan la selección de monitor de la configuración actual.

qBittorrent recibe un recurso `steel.qbtheme` compilado con Qt6 y la paleta común. Su lanzador carga además un adaptador pequeño que iguala la paleta inactiva con la activa, conservando los controles deshabilitados y el layout nativo. Funciona también con su AppImage: el adaptador resuelve Qt desde la aplicación, sin cargar otra versión de Qt ni mantener procesos adicionales. Se necesitan `c++`, `pkg-config` y las cabeceras de Qt6 para compilarlo una sola vez. El formato del recurso está documentado por [qBittorrent](https://github.com/qbittorrent/qBittorrent/wiki/Create-custom-themes-for-qBittorrent).

CPU y RAM aparecen a la derecha del botón de reproducción. El actualizador nativo Arch/Cachy permanece visible incluso cuando no hay actualizaciones; `tools/update-tray.py` inicia un servicio de usuario al arrancar el perfil y lo vuelve a levantar si el applet termina. Sus estados y comprobaciones siguen siendo los del actualizador instalado.

Super+R abre Rofi Spotlight con los colores de Steel, blur y la misma altura que Overview. El buscador no lleva texto de ejemplo y la fuente se obtiene de `appearance.fonts.main` en Settings. Las zonas transparentes alrededor del panel permiten cerrarlo con un clic también en Wayland. El launcher existente conserva su atajo.

RetroArch puede usar una compilación personal de Ozone con la paleta común:

```bash
python3 ~/.local/share/rice-profiles/tools/build-retroarch.py
```

El constructor fija RetroArch 1.22.2, verifica su código y el [parche oficial de compatibilidad con FFmpeg](https://github.com/libretro/RetroArch/commit/f5b422d5a81f0b4d263e2f52c8419ea9ce7467f6), y restaura los assets oficiales Ozone/XMB verificando las firmas de los paquetes Arch. Usa dos tareas de compilación con prioridad reducida. Necesita las herramientas de compilación y dependencias de desarrollo de RetroArch, Qt6, `pacman-key` y `bsdtar`. No instala archivos en `/usr`: el ejecutable y los assets quedan en `obsidian/application-style/clients/retroarch/`, excluidos de Git. Steel usa una copia privada de la configuración original para conservar sus controles y preferencias; KDE continúa usando la versión del sistema. Vuelve a ejecutar el constructor después de cambiar la paleta; reutiliza los objetos ya compilados.

## Pulido de paneles y ajustes

Intelligence conserva su apariencia original, sin efectos de profundidad adicionales. Solo carga la página seleccionada al abrirlo; al cerrar libera la página tras tres segundos, incluso si está separado, salvo descargas pendientes. La precarga permanece desactivada.

El panel derecho muestra dos notificaciones individuales y permite recorrer el resto con scroll; el estado vacío y el calendario ocupan menos espacio. Los ajustes mantienen su organización y ocultan controles sin función en este fork o sin hardware compatible. La selección de monitor para notificaciones usa la opción efectiva del servicio.

Rofi no lleva borde exterior. RuTracker oculta las barras de desplazamiento sin bloquear el scroll, tanto en el estilo de Firefox como en el userscript. Gemini mantiene transparentes los contenedores de posicionamiento de sus menús y aplica Steel únicamente al menú visible.

## CLI pública: Intelligence y colores

Desde la copia descargada, ejecuta `./steel-ctl intelligence` para listar, agregar o quitar tus propias fuentes mediante un menú. También admite `./steel-ctl intelligence add --name MiFuente --url https://example.org` y `./steel-ctl intelligence remove --id mifuente`. Se admiten hasta seis fuentes HTTP/HTTPS; el panel empieza con ChatGPT y Gemini, sin fuentes personales ni cuentas.

`./steel-ctl theme show` muestra los colores. `./steel-ctl theme set background=#202830 accent=#aabbcc` guarda tus cambios en `local-theme.json` y regenera las plantillas. Desde la instalación activa, ejecuta `~/.local/share/rice-profiles/steel-ctl theme set background=#202830 --apply` para aplicar los adaptadores disponibles. Los cambios locales están excluidos de Git. Este repositorio contiene únicamente Hyprland; Arc Steel KDE se mantiene separado.

## Apps Problemáticas

Los adaptadores generan CSS y configuraciones desde `themes/steel.json`, sus ajustes locales y `styles/`. Kitty admite actualización de la instancia configurada para Steel; varias aplicaciones necesitan volver a abrirse. Firefox usa el perfil dedicado del lanzador Steel y carga `userChrome.css` y `userContent.css` al reiniciarse. El comando existente `tools/firefox-theme.py` prepara ese perfil; aún no detecta automáticamente el perfil activo de `profiles.ini`.

Las copias de Discord y Spotify reciben los estilos al abrirse. WhatsApp Web utiliza el userscript generado y requiere reinstalarlo si cambia su contenido. ChatGPT/Gemini en Intelligence conservan por ahora sus colores nativos. Aerion depende del adaptador y sus dependencias. RetroArch requiere recompilar su variante; Wine y aplicaciones con motores propios no tienen uniformidad automática garantizada. Esta publicación no promete recarga en vivo universal; esos trabajos siguen pendientes.

Plantilla de prompt para adaptar otra aplicación:

> Adapta [aplicación y versión] a la paleta central de este repositorio Hyprland. Examina theme.py, palette.py y styles/. Añade una plantilla que use tokens existentes, sin colores duplicados. Identifica su configuración y mecanismo real de recarga. Conserva cuentas, datos y preferencias; aplica cambios solo a la instancia Steel, sin tocar KDE. Valida en un HOME temporal y documenta si hace falta reiniciar o recompilar. No prometas recarga en vivo si la aplicación no la admite.

## Alcance de esta publicación

La auditoría de exportación, las pruebas de tema y el CLI se verifican por terminal. La instalación real en otra laptop, el motor completo de recarga de aplicaciones y el empaquetado privado aún requieren trabajo. No se incluyen credenciales, sesiones, respaldos ni otros proyectos locales.
