import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Controls

RippleButton {
        property string glyph
        property string hint
        implicitWidth: 30
        implicitHeight: 28
        buttonRadius: 8
        ToolTip.visible: hovered
        ToolTip.text: hint
        ToolTip.delay: 500
        contentItem: MaterialSymbol {
            text: parent.glyph
            iconSize: 18
            color: Appearance.colors.colOnLayer0
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
