pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Hyprland

import qs.modules.common
import qs.modules.common.functions

/**
 * Configs Hyprland
 */
Singleton {
    id: root
    
    signal reloaded()

    readonly property string configuratorScriptPath: Quickshell.shellPath("scripts/hyprland/hyprconfigurator.py")
    readonly property string shellOverridesPath: Quickshell.shellPath("settings/hypr-overrides.lua")

    function set(key: string, value: var) { const entries={};entries[key]=value;setMany(entries); }
    function setMany(entries: var) {
        const args=["python3",root.configuratorScriptPath,"--file",root.shellOverridesPath];
        for(const key in entries)args.push("--set",key,String(entries[key]));
        Quickshell.execDetached(args);
    }
    function reset(key: string) { resetMany([key]); }
    function resetMany(keys: list<string>) {
        const args=["python3",root.configuratorScriptPath,"--file",root.shellOverridesPath];
        for(const key of keys)args.push("--reset",key);
        Quickshell.execDetached(args);
    }

    Connections {
        target: Hyprland

        function onRawEvent(event) {
            if (event.name == "configreloaded") {
                root.reloaded()
            }
        }
    }
}
