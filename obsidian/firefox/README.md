# Base web de Steel

Los CSS de este directorio se generan desde `styles/firefox/` y `themes/steel.json`; no los edites directamente. La base conserva el fondo del ecosistema, elimina fondos estructurales distintos y deja opacos los menús y diálogos. Hyprland aporta el blur. Las imágenes, vídeos y fondos fotográficos se mantienen.

Dark Reader debe usar modo dinámico, detección de tema oscuro desactivada y los colores de `darkreader-palette.json`. Revisa los overrides por sitio: otro motor o tema específico puede impedir que se aplique la base común. La receta no contiene datos de extensiones ni sesiones.

Google centra y amplía resultados de escritorio y elimina el rectángulo del degradado del resumen. El texto conserva su desvanecimiento y “Mostrar más” conserva su expansión. WhatsApp desactiva el pseudo-elemento del brillo del logo que producía la franja oscura. DuckDuckGo conserva su configuración nativa de ancho; en el teléfono se limita al viewport. Los aumentos de páginas y controles se aplican solo bajo la condición de pantalla pequeña y alta densidad.

Firefox lee estos archivos al arrancar: cerrar completamente y volver a abrir después de generar cambios. `tools/firefox-theme.py` crea el perfil limpio dedicado en una nueva instalación. Un equipo existente puede mantener sus enlaces locales; no se comparte su perfil de navegador.
