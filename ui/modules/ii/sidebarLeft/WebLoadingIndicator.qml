import QtQuick
import QtQuick.Layouts
import qs.modules.common
import qs.modules.common.widgets

RowLayout {
    id: root
    property string label: "Loading"
    property bool running: false
    spacing: 8

    StyledText {
        text: root.label
        color: Appearance.colors.colSubtext
        font.pixelSize: 13
        font.weight: Font.Medium
    }
    Row {
        spacing: 4
        Layout.alignment: Qt.AlignVCenter
        Repeater {
            model: 3
            Rectangle {
                id: dot
                required property int index
                width: 4
                height: 4
                radius: 2
                color: Appearance.colors.colPrimary
                opacity: 0.25
                SequentialAnimation {
                    running: root.running && root.visible
                    loops: Animation.Infinite
                    PauseAnimation { duration: dot.index * 110 }
                    OpacityAnimator { target: dot; from: 0.25; to: 1; duration: 320; easing.type: Easing.InOutSine }
                    OpacityAnimator { target: dot; from: 1; to: 0.25; duration: 440; easing.type: Easing.InOutSine }
                    PauseAnimation { duration: (2 - dot.index) * 110 }
                }
            }
        }
    }
}
