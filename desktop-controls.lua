-- Input shortcuts are independent of the visual profile.
local root = os.getenv("RICE_ROOT") or (os.getenv("HOME") .. "/.local/share/rice-profiles")

hl.unbind("SUPER + V")
hl.bind("SUPER + V", hl.dsp.window.float({action = "toggle"}),
 {description = "Window: Float/Tile"})

hl.unbind("SUPER + H")
hl.bind("SUPER + H", hl.dsp.global("quickshell:overviewClipboardToggle"),
 {description = "Utilities: Clipboard history"})
hl.bind("SUPER + H", hl.dsp.exec_cmd(
 "qs -c $qsConfig ipc call TEST_ALIVE || pkill fuzzel || cliphist list | fuzzel --match-mode fzf --dmenu | cliphist decode | wl-copy"))

hl.unbind("SUPER + ALT + O")
local function enterPhoneWhenReleased()
 if hl.is_key_down("Super_L") or hl.is_key_down("Super_R") or hl.is_key_down("Alt_L") then
  hl.timer(enterPhoneWhenReleased, {timeout = 30, type = "oneshot"})
 else
  hl.exec_cmd("python3 " .. string.format("%q", root .. "/phone-control.py") .. " start")
 end
end
hl.bind("SUPER + ALT + O", function()
 local runtime = os.getenv("XDG_RUNTIME_DIR")
 if runtime then
  local file = io.open(runtime .. "/steel-phone-cursor", "w")
  if file then
   local invisible = hl.get_config("cursor:invisible")
   file:write((invisible == true or invisible == 1) and "1" or "0")
   file:close()
  end
 end
 hl.config({cursor = {invisible = true}})
 hl.timer(enterPhoneWhenReleased, {timeout = 30, type = "oneshot"})
end,
 {description = "Phone: Enter USB keyboard/mouse control"})

local function returnFromPhone()
 local window = hl.get_active_window()
 if not window or window.title ~= "Phone OTG" or window.class ~= "scrcpy" then return end
 local runtime = os.getenv("XDG_RUNTIME_DIR")
 if not runtime then return end
 local cursorFile = io.open(runtime .. "/steel-phone-cursor", "r")
 if cursorFile then
  local invisible = cursorFile:read("*a") == "1"
  cursorFile:close()
  hl.config({cursor = {invisible = invisible}})
  os.remove(runtime .. "/steel-phone-cursor")
 end
 local file = io.open(runtime .. "/steel-phone-focus", "r")
 if not file then return end
 local address = file:read("*l")
 local x, y = file:read("*n", "*n")
 file:close()
 if x and y then hl.dispatch(hl.dsp.cursor.move({x = x, y = y})) end
 if address and hl.get_window("address:" .. address) then hl.dispatch(hl.dsp.focus({window = "address:" .. address})) end
end
hl.bind("Alt_L", function()
 local window = hl.get_active_window()
 if not window or window.title ~= "Phone OTG" or window.class ~= "scrcpy" then return end
 returnFromPhone()
 hl.exec_cmd("python3 " .. string.format("%q", root .. "/phone-control.py") .. " stop")
end, {release = true, ignore_mods = true, transparent = true, non_consuming = true})
hl.bind("Super_L", returnFromPhone, {ignore_mods = true, transparent = true, non_consuming = true})
hl.bind("Super_R", returnFromPhone, {ignore_mods = true, transparent = true, non_consuming = true})

-- Match only this helper's control window, not normal scrcpy mirroring.
hl.window_rule({name = "steel-phone-control", match = {class = "^scrcpy$", title = "^Phone OTG$"},
 float = true, size = {16, 16}, min_size = {16, 16},
 move = {"(monitor_w-20)", "(monitor_h-20)"}, pin = false,
 opacity = "0.0 override 0.0 override 0.0 override",
 no_shadow = true, no_blur = true, border_size = 0, rounding = 0})

hl.window_rule({name = "steel-settings", match = {title = "^Steel Settings$"},
 float = true, center = true, size = {900, 650}, pin = true})
