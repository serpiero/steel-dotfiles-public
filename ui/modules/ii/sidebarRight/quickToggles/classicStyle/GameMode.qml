import qs.modules.common.widgets
import qs.modules.common.models.quickToggles

QuickToggleButton {
    id: root
    GameModeToggle { id: model }
    buttonIcon: model.icon
    toggled: model.toggled
    onClicked: model.mainAction()
    StyledToolTip { text: model.tooltipText }
}
