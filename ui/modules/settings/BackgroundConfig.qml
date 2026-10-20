import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.modules.common
import qs.modules.common.widgets

ContentPage {
    forceWidth: true
    ContentSection {
        icon: "wallpaper"
        title: "Wallpaper"
        StyledImage {
            Layout.fillWidth: true
            Layout.preferredHeight: 240
            source: Config.options.background.wallpaperPath
            fillMode: Image.PreserveAspectCrop
            cache: false
        }
        RippleButtonWithIcon {
            materialIcon: "folder_open"
            mainText: "Choose wallpaper"
            onClicked: Quickshell.execDetached(["python3", Quickshell.env("HOME")+"/.local/share/rice-profiles/session.py", "wallpaper"])
        }
        StyledText {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: Appearance.colors.colSubtext
            text: "Ctrl+Super+T opens the wallpaper picker."
        }
    }
}
