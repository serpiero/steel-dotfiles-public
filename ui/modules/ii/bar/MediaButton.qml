import QtQuick
import qs
import qs.modules.common
import qs.modules.common.widgets

RippleButton {
    implicitWidth: 32
    implicitHeight: 32
    buttonRadius: 16
    toggled: GlobalStates.mediaControlsOpen
    colBackground: "transparent"
    colBackgroundToggled: Appearance.colors.colSecondaryContainer
    onClicked: GlobalStates.mediaControlsOpen = !GlobalStates.mediaControlsOpen
    contentItem: MaterialSymbol {
        text: "music_note"
        iconSize: 20
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        color: Appearance.colors.colOnLayer0
    }
}
