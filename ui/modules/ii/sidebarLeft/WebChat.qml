import qs
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import Quickshell
import Quickshell.Io
import "WebPanelPolicy.js" as WebPanelPolicy
import "WebPanelTheme.js" as WebPanelTheme

Control {
    id: root
    property int selectedSite: 0
    property var configuredSites: Config.options.sidebar.web?.sites ?? WebPanelPolicy.defaults
    readonly property var siteDefinitions: WebPanelPolicy.sites(configuredSites)
    readonly property var currentSite: siteDefinitions[selectedSite]
    readonly property color panelColor: currentSite?.theme === "compact-forum" ? Appearance.colors.colLayer0Base : (web ? web.nativeColor : Appearance.colors.colLayer0Base)
    property var visitedSites: []
    property var web: null
    property bool initialized: false
    onSiteDefinitionsChanged: {
        if (!initialized) return;
        visitedSites=[]; web=null; warmingIndex=-1; warmDeadline.stop();
        selectedSite=Math.min(selectedSite,siteDefinitions.length-1);
        if (GlobalStates.sidebarLeftOpen) visit(selectedSite);
        if (preloadEnabled) preloadTimer.restart();
    }
    property int warmingIndex: -1
    property bool preloadEnabled: Config.options.sidebar.web?.preload ?? false
    onPreloadEnabledChanged: if(initialized && preloadEnabled)preloadTimer.restart()
    // Test hosts can use a separate storage directory without touching the user's sessions.
    property string profileStorageName: "obsidian-panel"
    property string profileDirectory: Quickshell.shellPath("cache")
    property string downloadStatus: ""
    property var downloadQueue: []
    property bool waitingDownload: false

    function themeScript(site) {
        return WebPanelTheme.script({id:site.id, url:site.url, theme:site.theme,
            background:Appearance.colors.colLayer0Base.toString(), separator:Appearance.colors.colLayer0Border.toString(), lookAhead:site.lookAhead});
    }
    function applyPagePalette() {
        if (!pages) return;
        for (let i=0; i<siteDefinitions.length; i++) {
            const view=pages.itemAt(i)?.item;
            if (view) view.updateTheme();
        }
    }
    onPanelColorChanged: applyPagePalette()
    function loadSite(index) {
        if (index<0 || index>=siteDefinitions.length) return;
        const visited=visitedSites.slice(); visited[index]=true; visitedSites=visited;
    }
    function visit(index) {
        if (index<0 || index>=siteDefinitions.length) return;
        selectedSite=index;
        loadSite(index);
        web=pages.itemAt(index)?.item ?? null;
    }
    function initialize() {
        if (initialized || !Config.ready) return;
        initialized=true;
        if (GlobalStates.sidebarLeftOpen) visit(selectedSite);
        if (preloadEnabled) preloadTimer.start();
    }
    function preloadNext() {
        if (!preloadEnabled || warmingIndex>=0) return;
        for (let i=0; i<siteDefinitions.length; i++) {
            if (visitedSites[i]) continue;
            warmingIndex=i; loadSite(i); warmDeadline.restart(); return;
        }
    }
    function finishWarm(index) {
        if (warmingIndex!==index) return;
        warmingIndex=-1; warmDeadline.stop(); preloadTimer.restart();
    }
    function navigate(action) {
        if (!web) return;
        if (action==="back" && !web.canGoBack || action==="forward" && !web.canGoForward) return;
        web.preparing=true; web.presentationReady=false; web.failure="";
        if (action==="back") web.goBack();
        else if (action==="forward") web.goForward();
        else if (action==="home") { if(web.url.toString().replace(/\/$/, "")===currentSite.url.replace(/\/$/, ""))web.reload();else web.url=currentSite.url; }
        else web.reload();
    }
    function pageStates() {
        const states=[];
        for(let i=0;i<root.siteDefinitions.length;i++) {
            const view=pages.itemAt(i)?.item;
            states.push({id:root.siteDefinitions[i].id,loads:view?.navigationStarts ?? 0,ready:view?.presentationReady ?? false,state:view?.lifecycleState ?? null,loading:view?.loading ?? false,progress:view?.loadProgress ?? 0,failed:!!view?.failure});
        }
        return {selected:root.selectedSite,warming:root.warmingIndex,pages:states};
    }
    function focusInput() { if(web) web.forceActiveFocus(); }
    function nextDownload() {
        if (waitingDownload || !downloadQueue.length) return;
        const link=downloadQueue.shift(); waitingDownload=true; downloadTimeout.restart();
        downloader.url="about:blank"; downloader.url=link;
    }

    palette.window: panelColor
    palette.windowText: Appearance.colors.colOnLayer0
    palette.base: panelColor
    palette.text: Appearance.colors.colOnLayer0
    palette.button: Appearance.colors.colLayer2
    palette.buttonText: Appearance.colors.colOnLayer0
    palette.highlight: Appearance.colors.colPrimary
    palette.highlightedText: Appearance.colors.colOnPrimary
    background: Rectangle { color: "transparent"; radius: 12 }

    WebEngineProfile {
        id: browserProfile
        storageName: root.profileStorageName
        persistentStoragePath: root.profileDirectory + "/web-profile"
        cachePath: root.profileDirectory + "/web-http"
        offTheRecord: false
        httpCacheType: WebEngineProfile.DiskHttpCache
        persistentCookiesPolicy: WebEngineProfile.ForcePersistentCookies
        onDownloadRequested: download => {
            download.downloadDirectory=Quickshell.env("HOME")+"/Downloads";
            download.accept();
            root.downloadStatus="Descargando: "+download.downloadFileName;
            debrid.downloadStarted(); root.waitingDownload=false; downloadTimeout.stop();
            downloader.url="about:blank"; Qt.callLater(root.nextDownload);
        }
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 14
            Layout.bottomMargin: 4
            Layout.leftMargin: 16
            Layout.rightMargin: 16
            Repeater {
                model: root.siteDefinitions
                RippleButton {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    implicitHeight: 34
                    toggled: root.selectedSite===index
                    colBackgroundToggled: Appearance.colors.colSecondaryContainer
                    colBackgroundToggledHover: Appearance.colors.colSecondaryContainerHover
                    onClicked: root.visit(index)
                    contentItem: StyledText {
                        text: modelData.name
                        color: Appearance.colors.colOnLayer0
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 13
                    }
                }
            }
        }
        RowLayout {
            visible: root.currentSite.navigation
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 5
            spacing: 2
            WebNavigationButton { glyph:"arrow_back"; hint:"Atrás"; enabled:root.web?.canGoBack ?? false; onClicked:root.navigate("back") }
            WebNavigationButton { glyph:"arrow_forward"; hint:"Adelante"; enabled:root.web?.canGoForward ?? false; onClicked:root.navigate("forward") }
            WebNavigationButton { glyph:"home"; hint:"Inicio"; enabled:!!root.web; onClicked:root.navigate("home") }
            StyledText {
                Layout.fillWidth: true
                text: root.web?.title || root.currentSite.name
                elide: Text.ElideRight
                color: Appearance.colors.colSubtext
                font.pixelSize: 11
            }
            WebNavigationButton {
                glyph:root.web?.loading ? "close" : "refresh"
                hint:root.web?.loading ? "Detener" : "Recargar"
                enabled:!!root.web
                onClicked: { if(root.web.loading)root.web.stop();else root.navigate("reload"); }
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            Repeater {
                id: pages
                model: root.siteDefinitions.length
                Loader {
                    id: siteLoader
                    required property int index
                    anchors.fill: parent
                    active: root.visitedSites[index] ?? false
                    visible: GlobalStates.sidebarLeftOpen && root.selectedSite===index
                    onLoaded: if(root.selectedSite===index)root.web=item
                    sourceComponent: Component {
                        WebEngineView {
                            id: siteView
                            readonly property var site: root.siteDefinitions[siteLoader.index]
                            readonly property bool displayed: GlobalStates.sidebarLeftOpen && root.selectedSite===siteLoader.index
                            property int navigationStarts: 0
                            property color nativeColor: site.theme==="compact-forum" ? Appearance.colors.colLayer0Base : (site.id==="chatgpt" ? "#111111" : "#131314")
                            property bool preparing: true
                            property bool presentationReady: false
                            property bool hasPresentedContent: false
                            property bool showNavigationProgress: false
                            property string failure: ""
                            property var themeInjection: null
                            function updateTheme() {
                                if (!themeInjection) return;
                                themeInjection.sourceCode=root.themeScript(site);
                                if (lifecycleState===WebEngineView.LifecycleState.Active) runJavaScript(themeInjection.sourceCode,WebEngineScript.ApplicationWorld);
                            }
                            function confirmReady() {
                                const generation=navigationStarts;
                                runJavaScript("document.readyState!=='loading' && !!document.body && !!document.getElementById('steel-intelligence-theme')",WebEngineScript.ApplicationWorld,ready=>{
                                    if(ready && generation===navigationStarts && !presentationReady)revealTimer.restart();
                                });
                            }
                            function sampleNativeColor() {
                                if(site.theme==="compact-forum")return;
                                runJavaScript("(function(){for(const selector of ['main','chat-window','bard-sidenav-container','body','html']){const node=document.querySelector(selector);if(!node)continue;const color=getComputedStyle(node).backgroundColor;if(color && color!=='transparent' && color!=='rgba(0, 0, 0, 0)')return color;}return null;})()",WebEngineScript.ApplicationWorld,color=>{if(color)siteView.nativeColor=color;});
                            }
                            anchors.fill: parent
                            visible: displayed
                            enabled: displayed
                            profile: browserProfile
                            backgroundColor: nativeColor
                            // Hide first, then freeze: Chromium rejects freezing a still-visible view.
                            function syncLifecycle() {
                                if(!displayed && lifecycleState===WebEngineView.LifecycleState.Discarded)return;
                                lifecycleState=displayed || preparing || loading || warmSettleTimer.running || root.warmingIndex===siteLoader.index ? WebEngineView.LifecycleState.Active : WebEngineView.LifecycleState.Frozen;
                            }
                            onDisplayedChanged: {
                                if(displayed) { lifecycleState=WebEngineView.LifecycleState.Active;updateTheme();if(presentationReady)sampleNativeColor();else if(!loading)confirmReady(); }
                                lifecycleTimer.restart();
                            }
                            onPreparingChanged: {
                                if(preparing)lifecycleState=WebEngineView.LifecycleState.Active;
                                else lifecycleTimer.restart();
                            }
                            Timer { id:lifecycleTimer;interval:150;onTriggered:siteView.syncLifecycle() }
                            Timer {
                                interval:3000
                                running:site.discardWhenHidden && !siteView.displayed && siteView.lifecycleState!==WebEngineView.LifecycleState.Discarded
                                onTriggered: {
                                    if(siteView.loading)siteView.stop();
                                    siteView.lifecycleState=WebEngineView.LifecycleState.Discarded;
                                    siteView.presentationReady=false;siteView.hasPresentedContent=false;
                                }
                            }
                            Component.onCompleted: {
                                themeInjection=WebEngine.script();
                                themeInjection.name="Steel Intelligence theme";
                                themeInjection.injectionPoint=WebEngineScript.DocumentCreation;
                                themeInjection.worldId=WebEngineScript.ApplicationWorld;
                                themeInjection.runsOnSubFrames=false;
                                themeInjection.sourceCode=root.themeScript(site);
                                userScripts.insert(themeInjection);
                                // Set URL only after the early injection has been registered.
                                url=site.url;
                            }
                            settings.forceDarkMode: false
                            settings.showScrollBars: false
                            settings.javascriptCanAccessClipboard: true
                            zoomFactor: site.zoom
                            function startDebridDownload(link) { root.downloadQueue=root.downloadQueue.concat([link]); root.nextDownload(); }
                            onNewWindowRequested: request => request.openIn(siteView)
                            onJavaScriptConsoleMessage: (level,message) => {
                                // DOM is themed and usable; do not wait for images/ads to finish downloading.
                                if(message==="STEEL_INTELLIGENCE_DOCUMENT_READY "+url.toString() && !presentationReady && !failure)revealTimer.restart();
                            }
                            onLoadingChanged: request => {
                                if(request.status===WebEngineView.LoadStartedStatus) {
                                    showNavigationProgress=hasPresentedContent; navigationStarts++; preparing=true; presentationReady=false; failure=""; revealTimer.stop();warmSettleTimer.stop();
                                } else if(request.status===WebEngineView.LoadSucceededStatus) {
                                    const generation=navigationStarts;
                                    runJavaScript(root.themeScript(site),WebEngineScript.ApplicationWorld,()=>{if(generation===navigationStarts)revealTimer.restart();});
                                    sampleNativeColor();
                                    warmSettleTimer.restart();
                                } else if(request.status===WebEngineView.LoadFailedStatus || request.status===WebEngineView.LoadStoppedStatus) {
                                    failure=request.status===WebEngineView.LoadStoppedStatus && presentationReady ? "" : (request.status===WebEngineView.LoadStoppedStatus ? "Loading stopped" : "Unable to load this page");
                                    preparing=false; root.finishWarm(siteLoader.index);
                                }
                            }
                            Timer {
                                id: revealTimer
                                interval: 60
                                onTriggered: {
                                    siteView.preparing=false; siteView.presentationReady=true;siteView.hasPresentedContent=true;

                                }
                            }
                            Timer {
                                id:warmSettleTimer
                                interval:1000
                                onTriggered: {
                                    // Let application hydration finish before suspending the prepared page.
                                    if(!siteView.loading && siteView.presentationReady)root.finishWarm(siteLoader.index);
                                    lifecycleTimer.restart();
                                }
                            }
                            onRenderProcessTerminated: {
                                if(lifecycleState===WebEngineView.LifecycleState.Discarded)return;
                                preparing=false; presentationReady=false; failure="This page closed. You can reload it.";
                                root.finishWarm(siteLoader.index);
                            }
                            onContextMenuRequested: request => {
                                if(request.isContentEditable || request.selectedText || request.mediaType!==ContextMenuRequest.MediaTypeNone) { request.accepted=false;return; }
                                linkMenu.link=request.linkUrl.toString(); linkMenu.popup(request.position.x,request.position.y); request.accepted=true;
                            }
                        }
                    }
                }
            }
            Rectangle {
                id: initialLoadingCover
                anchors.fill: parent
                opacity: !root.web || (!root.web.hasPresentedContent && !root.web.presentationReady) || !!root.web.failure ? 1 : 0
                visible: opacity>0
                Behavior on opacity { NumberAnimation { duration:260;easing.type:Easing.InOutCubic } }
                color: root.panelColor
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 14
                    WebLoadingIndicator {
                        label:"Loading "+root.currentSite.name
                        running:GlobalStates.sidebarLeftOpen && initialLoadingCover.visible && !root.web?.failure
                        visible:!root.web?.failure
                        Layout.alignment:Qt.AlignHCenter
                    }
                    StyledText { text:root.web?.failure || "";visible:!!root.web?.failure;color:Appearance.colors.colSubtext;Layout.alignment:Qt.AlignHCenter }
                    DialogButton { visible:!!root.web?.failure;buttonText:"Retry";Layout.alignment:Qt.AlignHCenter;onClicked:root.navigate("reload") }
                }
            }
            Rectangle {
                id: navigationLoadingChip
                readonly property bool pending: !!root.web && root.web.showNavigationProgress && root.web.hasPresentedContent && (!root.web.presentationReady || root.web.loading) && !root.web.failure
                property bool showAfterDelay: false
                onPendingChanged: {
                    showAfterDelay=false;
                    if(pending)chipDelay.restart();else chipDelay.stop();
                }
                Timer { id:chipDelay;interval:180;onTriggered:navigationLoadingChip.showAfterDelay=navigationLoadingChip.pending }
                anchors.top: parent.top
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.topMargin: 12
                width: chipContent.implicitWidth+24
                height: 32
                radius: 16
                color: root.panelColor
                border.width: 1
                border.color: Appearance.colors.colLayer0Border
                opacity: showAfterDelay ? 1 : 0
                visible: opacity>0
                Behavior on opacity { NumberAnimation { duration:160;easing.type:Easing.InOutSine } }
                WebLoadingIndicator {
                    id:chipContent
                    anchors.centerIn: parent
                    label:"Loading"
                    running:GlobalStates.sidebarLeftOpen && navigationLoadingChip.visible
                }
            }
        }
        Label {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 6
            visible: root.downloadStatus.length>0
            text: root.downloadStatus
            elide: Text.ElideMiddle
            color: Appearance.colors.colSubtext
            font.pixelSize: 11
        }
    }
    WebEngineView { id:downloader;visible:false;width:1;height:1;profile:browserProfile;url:"about:blank" }
    Timer { id:preloadTimer;interval:800;onTriggered:root.preloadNext() }
    Timer {
        id:warmDeadline
        interval:25000
        onTriggered: { const view=pages.itemAt(root.warmingIndex)?.item;if(view)view.stop();root.finishWarm(root.warmingIndex); }
    }
    Timer {
        id:downloadTimeout
        interval:60000
        onTriggered: { root.waitingDownload=false;root.downloadQueue=[];downloader.stop();debrid.downloadError("El servidor no inició la descarga. Puedes volver a intentarlo."); }
    }
    DebridLink { id:debrid;webviewItem:web }
    Menu {
        id:linkMenu
        parent:web
        property string link:""
        MenuItem { text:"Volver";enabled:web && web.canGoBack;onTriggered:root.navigate("back") }
        MenuItem { text:"Recargar";onTriggered:root.navigate("reload") }
        MenuSeparator {}
        MenuItem { text:"Descargar partes con Debrid-Link";onTriggered:debrid.requestBatch() }
        MenuItem { text:"Configurar Debrid-Link";onTriggered:debrid.configure() }
        MenuItem { visible:linkMenu.link.length>0;text:"Abrir en el panel";onTriggered: { web.preparing=true;web.url=linkMenu.link; } }
        MenuItem { visible:linkMenu.link.length>0;text:"Descargar con Debrid-Link";onTriggered:debrid.requestDownload(linkMenu.link) }
        MenuItem { visible:linkMenu.link.length>0;text:"Copiar enlace";onTriggered:Quickshell.execDetached(["wl-copy","--",linkMenu.link]) }
    }
    IpcHandler {
        target:"webChat"
        function status(): string {
            return JSON.stringify(root.pageStates());
        }
        function open(id:string): void {
            const index=root.siteDefinitions.findIndex(site=>site.id===id);
            if(index>=0) { root.visit(index);GlobalStates.sidebarLeftOpen=true; }
        }
        function chatgpt(): void { open("chatgpt"); }
        function gemini(): void { open("gemini"); }
    }
    Connections {
        target:GlobalStates
        function onSidebarLeftOpenChanged() { if(GlobalStates.sidebarLeftOpen)root.visit(root.selectedSite); }
    }
    Connections { target:Config;function onReadyChanged() { root.initialize(); } }
    Connections { target:Appearance.colors;function onColLayer0BaseChanged() { root.applyPagePalette(); } }
    Component.onCompleted: initialize()
}
