import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Qt.labs.synchronizer

Item {
    id: root
    required property var scopeRoot
    property int sidebarPadding: 0
    anchors.fill: parent
    property bool aiChatEnabled: false
    property bool opaqueWeb: true
    readonly property bool intelligenceLoaded: swipeView.itemAt(0)?.active ?? false
    readonly property color webPanelColor: swipeView.currentItem && swipeView.currentItem.panelColor ? swipeView.currentItem.panelColor : Appearance.colors.colLayer0Base
    property bool translatorEnabled: Config.options.sidebar.translator.enable
    property bool animeEnabled: Config.options.policies.weeb !== 0
    property bool animeCloset: Config.options.policies.weeb === 2
    property var tabButtonList: [
        {"icon": "neurology", "name": "Intelligence"},
        ...(root.aiChatEnabled ? [{"icon": "neurology", "name": "Gemini API"}] : []),
        ...(root.translatorEnabled ? [{"icon": "translate", "name": Translation.tr("Translator")}] : []),
        ...((root.animeEnabled && !root.animeCloset) ? [{"icon": "bookmark_heart", "name": Translation.tr("Anime")}] : [])
    ]
    property int tabCount: swipeView.count

    function focusActiveItem() {
        swipeView.currentItem.forceActiveFocus()
    }

    Keys.onPressed: (event) => {
        if (event.modifiers === Qt.ControlModifier) {
            if (event.key === Qt.Key_PageDown) {
                swipeView.incrementCurrentIndex()
                event.accepted = true;
            }
            else if (event.key === Qt.Key_PageUp) {
                swipeView.decrementCurrentIndex()
                event.accepted = true;
            }
        }
    }

    ColumnLayout {
        anchors {
            fill: parent
            margins: sidebarPadding
        }
        spacing: sidebarPadding

        Toolbar {
            visible: false
            Layout.alignment: Qt.AlignHCenter
            enableShadow: false
            ToolbarTabBar {
                id: tabBar
                Layout.alignment: Qt.AlignHCenter
                tabButtonList: root.tabButtonList
                currentIndex: swipeView.currentIndex
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            implicitWidth: swipeView.implicitWidth
            implicitHeight: swipeView.implicitHeight
            radius: Appearance.rounding.normal
            color: "transparent"

            SwipeView { // Content pages
                id: swipeView
                anchors.fill: parent
                spacing: 10
                currentIndex: tabBar.currentIndex

                clip: true
                // Release the offscreen texture when the panel is hidden.
                layer.enabled: GlobalStates.sidebarLeftOpen
                layer.effect: OpacityMask {
                    maskSource: Rectangle {
                        width: swipeView.width
                        height: swipeView.height
                        radius: Appearance.rounding.screenRounding - Appearance.sizes.hyprlandGapsOut + 1
                    }
                }

                contentChildren: [
                    webChat.createObject(),
                    ...(root.aiChatEnabled ? [aiChat.createObject()] : []),
                    ...(root.translatorEnabled ? [translator.createObject()] : []),
                    ...((root.tabButtonList.length === 0 || (!root.aiChatEnabled && !root.translatorEnabled && root.animeCloset)) ? [placeholder.createObject()] : []),
                    ...(root.animeEnabled ? [anime.createObject()] : []),
                ]
            }
        }

        Component {
            id: webChat
            Loader {
                id: intelligenceLoader
                objectName: "steelIntelligenceLoader"
                readonly property bool requested: GlobalStates.sidebarLeftOpen
                readonly property color panelColor: item?.panelColor ?? Appearance.colors.colLayer0Base
                property bool keepLoaded: false
                property bool pendingTransfers: false
                active: keepLoaded || pendingTransfers
                function syncTransfers() {
                    pendingTransfers = (item?.waitingDownload ?? false) || ((item?.downloadQueue?.length ?? 0) > 0);
                }
                Component.onCompleted: keepLoaded = requested
                onItemChanged: syncTransfers()
                onRequestedChanged: {
                    if (requested) {
                        releaseDelay.stop();
                        keepLoaded = true;
                    } else if (keepLoaded) releaseDelay.restart();
                }
                onActiveFocusChanged: if (activeFocus && item) item.forceActiveFocus()
                sourceComponent: WebChat {}
                Connections {
                    target: intelligenceLoader.item
                    function onWaitingDownloadChanged() { intelligenceLoader.syncTransfers(); }
                    function onDownloadQueueChanged() { intelligenceLoader.syncTransfers(); }
                }
                Timer { id: releaseDelay; interval: 3000; onTriggered: intelligenceLoader.keepLoaded = false }
            }
        }
        Component {
            id: aiChat
            AiChat {}
        }
        Component {
            id: translator
            Translator {}
        }
        Component {
            id: anime
            Anime {}
        }
        Component {
            id: placeholder
            Item {
                StyledText {
                    anchors.centerIn: parent
                    text: root.animeCloset ? Translation.tr("Nothing") : Translation.tr("Enjoy your empty sidebar...")
                    color: Appearance.colors.colSubtext
                }
            }
        }
    }
}
