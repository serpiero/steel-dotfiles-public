---------------------------------------
-- cybrcore    lucid theme config for hyprland
-- Project:    https://github.com/cybrcore/cybr-hyprland
-- Author:     scherrer-txt   |   License:     GPL-3.0
-- Source:     ~/.config/hypr/theme.lua
---------------------------------------

local dir = debug.getinfo(1, "S").source:sub(2):match("(.*/)")
local _ENV = setmetatable({}, {__index = _G})
local variables = dofile(dir .. "variables.lua")
local colors = dofile(dir .. "colors.lua")

for k, v in pairs(variables) do _ENV[k] = v end
for k, v in pairs(colors) do _ENV[k] = v end

-- DECORATION
hl.config({
    general = {
        border_size = border,
        col = {
            inactive_border = "rgba(" .. cy0 .. tr0 .. ")",
            active_border = "rgba(" .. re0 .. trF .. ")",
        },
        gaps_in = gapS,
        gaps_out = gapM,
    },
    decoration = {
        rounding = radius,
        rounding_power = power,
        active_opacity = activeTr,
        inactive_opacity = inActiveTr,
        blur = {
            enabled = true,
            size = blurSize,
            passes = blurPass,
            noise = noise,
            ignore_opacity = true,
            new_optimizations = true,
            xray = false,
            popups = true,
        },
        shadow = {
            enabled = false,
            range = 10,
            scale = 1,
            render_power = 2,
            color = "rgba(" .. re0 .. tr2 .. ")",
            color_inactive = "rgba(" .. no0 .. tr2 .. ")",
        },
        dim_inactive = false,
        dim_strength = 0.05,
        dim_special = 0,
    },
    group = {
        col = {
            border_active = "rgba(" .. re0 .. trF .. ")",
            border_inactive = "rgba(" .. re1 .. trF .. ")",
            border_locked_active = "rgba(" .. vi0 .. trF .. ")",
            border_locked_inactive = "rgba(" .. vi0 .. tr7 .. ")",
        },
        groupbar = {
            col = {
                active = "rgba(" .. re0 .. trF .. ")",
                inactive = "rgba(" .. re1 .. trF .. ")",
                locked_active = "rgba(" .. vi0 .. trF .. ")",
                locked_inactive = "rgba(" .. vi0 .. tr7 .. ")",
            },
            font_size = fontM,
            text_color = "rgba(" .. no0 .. trF .. ")",
            height = 1,
            indicator_height = 24,
            text_offset = -12,
        },
    },

-- ANIMATIONS
    animations = {
        enabled = false,
    },
})

-- Obsidian Glass: overrides apply only inside this profile.
hl.config({
 general = { border_size = 0, gaps_in = 5, gaps_out = 10 },
 input = { follow_mouse = 1 },
 decoration = {
  rounding = 20, rounding_power = 2,
  dim_inactive = true, dim_strength = 0.04,
  blur = { enabled = true, size = 14, passes = 3, noise = 0.015,
   contrast = 1.12, brightness = 1.08, vibrancy = 0.12,
   ignore_opacity = true, xray = false, popups = true },
  shadow = { enabled = true, range = 24, render_power = 3, scale = 1,
   color = "rgba(00000055)" }
 }, animations = { enabled = true }
})
hl.window_rule({match={class=".*"}, no_blur=false, border_size=0})
hl.window_rule({match={class=".*"}, opacity="0.82 override 0.80 override 1.0 override"})
hl.window_rule({match={class="(Chatgpt|[Cc]hat[Gg][Pp][Tt]|firefox|org.mozilla.firefox|org.kde.dolphin|dolphin|[Ww]hats[Aa]pp.*)"}, opacity="0.82 override 0.80 override 1.0 override"})
hl.window_rule({match={class="(kitty|foot|Alacritty|org.kde.konsole)"}, opacity="1.0 override 0.94 override 1.0 override"})
hl.window_rule({match={class="(mpv|vlc|steam_app_.*)"}, opacity="1.0 override 1.0 override 1.0 override"})
hl.layer_rule({match={namespace="(quickshell:.*|waybar|rofi|swaync-control-center|swaync-notification-window)"},blur=true,ignore_alpha=0.1})
local root = os.getenv("RICE_ROOT") or (os.getenv("HOME") .. "/.local/share/rice-profiles")
local function bind(key,action,description)
 hl.unbind(key)
 hl.bind(key,hl.dsp.exec_cmd("python3 " .. root .. "/session.py " .. action),{description=description})
end
bind("SUPER + Return","terminal","Applications: Open terminal")
bind("SUPER + T","terminal","Applications: Open terminal")
bind("CTRL + ALT + T","terminal","Applications: Open terminal")
bind("SUPER + R","spotlight","Applications: Open Steel Spotlight")
hl.unbind("CTRL + SUPER + T")
hl.bind("CTRL + SUPER + T", hl.dsp.global("quickshell:wallpaperSelectorToggle"), {description="Shell: Choose wallpaper"})
bind("CTRL + SUPER + A","web-chat","Shell: Open Intelligence")
bind("CTRL + SUPER + R","sync","Configuration: Start shell if stopped")
hl.env("qsConfig", "obsidian")

-- Persistent screenshot selection overlay, scoped to Obsidian.
local function capture(key, mode)
 hl.unbind(key)
 hl.bind(key, hl.dsp.exec_cmd("python3 " .. root .. "/capture-overlay.py " .. mode), {description=mode=="screen" and "Capture: Capture full screen" or mode=="window" and "Capture: Capture active window" or "Capture: Select and annotate region"})
end
capture("SUPER + SHIFT + S", "region")
capture("Print", "screen")
capture("CTRL + Print", "window")
hl.window_rule({match={class="(spectacle|org.kde.spectacle)"}, float=true, center=true,
 size={"(monitor_w*0.72)","(monitor_h*0.80)"}, opacity="1.0 override 1.0 override 1.0 override", no_dim=true})

-- No entrance/exit motion for the frozen screenshot selection.
hl.layer_rule({match={namespace="obsidian:capture"},no_anim=true,blur=false})

-- Opaque launcher surface needs no backdrop blur fringe.
hl.layer_rule({match={namespace="quickshell:overview"},blur=false})

-- Google Lens is intentionally disabled in this profile.
hl.unbind("SUPER + SHIFT + A")

-- Obsidian settings replace inherited controls that do not affect this fork.
bind("SUPER + I", "settings", "Configuration: Open Obsidian settings")
hl.unbind("CTRL+SUPER+ALT+Slash")
hl.bind("CTRL+SUPER+ALT+Slash", hl.dsp.exec_cmd("xdg-open " .. root .. "/obsidian/theme.lua"), {description="Configuration: Edit Obsidian keybinds"})
-- Fixed dark palette: inherited light/dark and palette-family actions are inapplicable.
hl.unbind("CTRL + SUPER + SHIFT + D")
hl.unbind("CTRL + SUPER + P")
hl.unbind("CTRL + SUPER + ALT + T")

local overrides = root .. "/ui/settings/hypr-overrides.lua"
local f = io.open(overrides,"r")
if f then f:close(); dofile(overrides) end

