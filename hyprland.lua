-- Obsidian: portable Lua entry point. Previous configuration is backed up.
local root = os.getenv("RICE_ROOT") or (os.getenv("HOME") .. "/.local/share/rice-profiles")
package.path = root .. "/hyprland-base/?.lua;" .. root .. "/hyprland-base/?/init.lua;" .. package.path
require("hyprland.lib")
require("hyprland.env")
require("hyprland.general")
require("hyprland.rules")
require("hyprland.colors")
require("hyprland.keybinds")
dofile(root .. "/startup.lua")
dofile(root .. "/loader.lua")
local localConfig = root .. "/local.lua"
if is_file_exists(localConfig) then dofile(localConfig) end
