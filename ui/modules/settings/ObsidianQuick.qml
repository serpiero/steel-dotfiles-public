import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.modules.common
import qs.modules.common.widgets

ContentPage {
    forceWidth: true
    property int blurSize: 14
    property int blurPasses: 3
    property bool blurReady: false
    Process {
        running: true
        command: ["hyprctl","getoption","decoration:blur:size","-j"]
        stdout: StdioCollector { onStreamFinished: { try { blurSize=JSON.parse(text).int; } catch(e) {} } }
    }
    Process {
        running: true
        command: ["hyprctl","getoption","decoration:blur:passes","-j"]
        stdout: StdioCollector { onStreamFinished: { try { blurPasses=JSON.parse(text).int; } catch(e) {} blurReady=true; } }
    }
    ContentSection {
        icon: "palette"
        title: "Steel"
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Background #161a1f · steel accents · system blur. Fonts and application layouts are preserved. Intelligence keeps the approved native ChatGPT and Gemini colors."
        }
        StyledImage {
            Layout.fillWidth: true
            Layout.preferredHeight: 140
            source: Config.options.background.wallpaperPath
            fillMode: Image.PreserveAspectCrop
            cache: false
        }
        RippleButtonWithIcon {
            materialIcon: "wallpaper"
            mainText: "Choose wallpaper · Ctrl+Super+T"
            onClicked: Quickshell.execDetached(["python3",Quickshell.env("HOME")+"/.local/share/rice-profiles/session.py","wallpaper"])
        }
        ConfigSwitch {
            buttonIcon: "ev_shadow"
            text: "Panel transparency"
            checked: Config.options.appearance.transparency.enable
            onCheckedChanged: Config.options.appearance.transparency.enable=checked
        }
    }
    ContentSection {
        icon: "blur_on"
        title: "System blur"
        ConfigSpinBox {
            icon: "blur_on";text: "Blur size"
            value: blurSize;from: 1;to: 20;stepSize: 1
            onValueChanged: {if(blurReady && value!==blurSize){blurSize=value;HyprlandConfig.set("decoration:blur:size",value);}}
        }
        ConfigSpinBox {
            icon: "layers";text: "Blur passes"
            value: blurPasses;from: 1;to: 4;stepSize: 1
            onValueChanged: {if(blurReady && value!==blurPasses){blurPasses=value;HyprlandConfig.set("decoration:blur:passes",value);}}
        }
        StyledText {
            Layout.fillWidth: true;wrapMode: Text.WordWrap
            text: "These controls apply to Hyprland and persist in this profile. The Steel palette stays unchanged. Higher blur values increase GPU work."
        }
    }
    ContentSection {
        icon: "keyboard"
        title: "Shortcuts & captures"
        StyledText {
            Layout.fillWidth: true;wrapMode: Text.WordWrap
            text: "Super+/ · current shortcuts\nSuper+R · Steel Spotlight\nSuper+V · float/tile\nSuper+H · clipboard history\nSuper+Alt+O · phone control (Alt to return)\nSuper+Shift+S · region capture\nPrint · full screen\nCtrl+Print · active window\nSuper+I · Steel settings\n\nCapture: drag any edge or corner to resize. Clicking outside keeps your selection. Select again with the selection button; Enter copies, Ctrl+S saves, Esc cancels."
        }
    }
}
