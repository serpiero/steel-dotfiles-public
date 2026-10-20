import qs.modules.common
import qs.modules.common.widgets
import qs.services
import Qt5Compat.GraphicalEffects
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    readonly property real viewportHeight: {
        if (Notifications.list.length === 0) return 64;
        // contentHeight updates once delegates have been laid out.
        const total = listview.contentHeight;
        const first = listview.itemAtIndex(0)?.height ?? 80;
        const second = listview.count > 1 ? (listview.itemAtIndex(1)?.height ?? 80) + listview.spacing : 0;
        return Math.min(224, total > 0 ? Math.min(total, first + second) : first + second);
    }
    implicitHeight: viewportHeight + statusRow.implicitHeight + 10

    NotificationListView { // Scrollable window
        id: listview
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: statusRow.top
        anchors.bottomMargin: 5

        clip: true
        layer.enabled: true
        layer.effect: OpacityMask {
            maskSource: Rectangle {
                width: listview.width
                height: listview.height
                radius: Appearance.rounding.normal
            }
        }

        popup: false
        individual: true
    }

    // Placeholder when list is empty
    RowLayout {
        visible: Notifications.list.length === 0
        anchors.horizontalCenter: parent.horizontalCenter
        y: (root.viewportHeight - height) / 2
        spacing: 10
        MaterialSymbol {
            text: "notifications_none"
            iconSize: 24
            color: Appearance.colors.colSubtext
        }
        StyledText {
            text: "No notifications"
            color: Appearance.colors.colSubtext
        }
    }

    ButtonGroup {
        id: statusRow
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        NotificationStatusButton {
            Layout.fillWidth: false
            buttonIcon: "notifications_paused"
            toggled: Notifications.silent
            onClicked: () => {
                Notifications.silent = !Notifications.silent;
            }
        }
        NotificationStatusButton {
            enabled: false
            Layout.fillWidth: true
            buttonText: Translation.tr("%1 notifications").arg(Notifications.list.length)
        }
        NotificationStatusButton {
            Layout.fillWidth: false
            buttonIcon: "delete_sweep"
            onClicked: () => {
                Notifications.discardAllNotifications()
            }
        }
    }
}
