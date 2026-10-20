pragma ComponentBehavior: Bound

import qs.modules.common.widgets
import qs.services
import QtQuick
import Quickshell

StyledListView { // Scrollable window
    id: root
    property bool popup: false
    // Sidebar history can show individual cards; popups keep their app groups.
    property bool individual: false

    spacing: 3

    model: ScriptModel {
        values: root.individual ? Notifications.list.slice().sort((a, b) => b.time - a.time) :
            (root.popup ? Notifications.popupAppNameList : Notifications.appNameList)
    }
    delegate: NotificationGroup {
        required property int index
        required property var modelData
        popup: root.popup
        width: ListView.view.width // https://doc.qt.io/qt-6/qml-qtquick-listview.html
        notificationGroup: root.individual ? ({
            appName: modelData.appName, appIcon: modelData.appIcon,
            notifications: [modelData], time: modelData.time
        }) : (popup ? Notifications.popupGroupsByAppName[modelData] : Notifications.groupsByAppName[modelData])
    }
}
