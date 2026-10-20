local root = os.getenv("RICE_ROOT") or (os.getenv("HOME") .. "/.local/share/rice-profiles")
hl.on("hyprland.start", function()
 hl.exec_cmd("python3 " .. root .. "/session.py sync")
 hl.exec_cmd("python3 " .. root .. "/app-style.py service-environment")
 hl.exec_cmd("wl-paste --type text --watch cliphist store")
 hl.exec_cmd("wl-paste --type image --watch cliphist store")
end)

-- The public layout steps relative to the monitor under the bar.
-- local.lua can replace this dispatcher with personal workspace reservations.
function workspace_step(direction, output)
 local monitor = output and hl.get_monitor(output) or hl.get_active_monitor()
 if not monitor then return end
 hl.dispatch(hl.dsp.focus({monitor = monitor.name}))
 return hl.dsp.focus({workspace = direction > 0 and "r+1" or "r-1"})
end
