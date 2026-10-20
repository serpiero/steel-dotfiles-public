# Teléfono como pantalla USB

Requiere Hyprland con Lua, `adb`, `wayvnc`, depuración USB autorizada y AVNC en Android. El vigilante detecta un teléfono USB autorizado (`adb -d`) o el serial de `PHONE_ADB_SERIAL`. Usa únicamente la salida nombrada `HEADLESS-1` y el servidor VNC asociado; no mata otros servidores.

Desde `local.lua`, añade al callback de inicio de Hyprland:

```lua
hl.on("hyprland.start", function()
  local root = os.getenv("RICE_ROOT") or (os.getenv("HOME") .. "/.local/share/rice-profiles")
  hl.exec_cmd(root .. "/features/phone-display/phone-display-watch")
end)
```

Conectar crea la pantalla vertical 1080×2340 a 120 Hz, escala 2×, a la derecha de las salidas activas; restaura `adb reverse` y abre AVNC con localhost:5900. Desconectar elimina solo esa salida y su servidor. Un bloqueo impide vigilantes duplicados y los errores se reintentan. La salida se crea con nombre explícito para evitar la acumulación de monitores headless.

120 Hz es el modo solicitado al compositor y 120 FPS el límite del servidor: no garantiza 120 cuadros recibidos. El rendimiento y la calidad también dependen de AVNC, el contenido y USB. Sus ajustes de codificación/calidad viven en el teléfono.

Para detener manualmente la pantalla: `features/phone-display/phone-display-start --stop`. Para detener el vigilante, envíale SIGTERM; retira el callback para que no arranque en la próxima sesión. No combines este vigilante con scripts antiguos que creen salidas headless sin nombre.
