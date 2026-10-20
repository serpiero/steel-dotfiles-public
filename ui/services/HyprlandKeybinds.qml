pragma Singleton
pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.functions
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland

/**
 * A service that provides access to Hyprland keybinds.
 * Uses the `get_keybinds.py` script to parse comments in config files in a certain format and convert to JSON.
 */
Singleton {
    id: root
    property var keybinds: []
    property var keybindCategories: []

    Connections {
        target: Hyprland

        function onRawEvent(event) {
            if (event.name == "configreloaded") {
                getKeybinds.running = true
            }
        }
    }

    Process {
        id: getKeybinds
        running: true
        command: ["hyprctl", "binds", "-j"]
        
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.keybinds = JSON.parse(text).map(bind => Object.assign({},bind,{description:(bind.description || "").replace(/^App:/,"Applications:").replace(/Obsidian/g,"Steel")}))
                    var groups = []
                    for (var i = 0; i < root.keybinds.length; i++) {
                        var bind = root.keybinds[i].description
                        var group = bind.substring(0, bind.indexOf(":"))
                        if (!groups.includes(group) && group.length > 0) {
                            groups.push(group)
                        }
                    }
                    const order=["Shell","App","Applications","Capture","Window","Workspace","Media","Session","Utilities","Configuration"];
                    root.keybindCategories = groups.sort((a,b) => {const ai=order.indexOf(a),bi=order.indexOf(b);return (ai<0?order.length:ai)-(bi<0?order.length:bi);})
                } catch (e) {
                    console.error("[CheatsheetKeybinds] Error parsing keybinds:", e)
                }
            }
        }
    }
}

