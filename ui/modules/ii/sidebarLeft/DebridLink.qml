import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.workspace.dbus as DBus

Item {
    id: bridge
    property var webviewItem
    property string apiKey: ""
    property string pendingLink: ""
    property string message: ""
    property bool busy: false
    property bool walletLoaded: false
    property bool setupMode: false
    property bool batchMode: false
    property var batchLinks: []
    property int batchIndex: 0
    property var batchFiles: []
    property var batchHosts: []
    ListModel { id: linkChoices }
    property string storageWarning: ""
    property var files: []
    property var currentRequest: null
    property int walletHandle: -1
    readonly property string appId: "ChatAI-DebridLink"
    readonly property string walletFolder: "ChatAI"
    // Injectable interfaces allow tests without real credentials or downloads.
    property var requestFactory: function() { return new XMLHttpRequest(); }
    property var walletTransport: function(member, signature, args, done, fail) {
        DBus.SessionBus.asyncCall({service: "org.kde.kwalletd6", path: "/modules/kwalletd6",
            iface: "org.kde.KWallet", member: member, signature: "(" + signature + ")", arguments: args},
            function(reply) { done(reply.value); },
            function(error) { fail(); });
    }

    function fail(text) {
        busy = false;
        message = text;
        panel.open();
    }
    function openWallet(done, failed) {
        walletTransport("networkWallet", "", [], function(name) {
            walletTransport("open", "sxs", [name, new DBus.int64(0), appId], function(handle) {
                if (Number(handle) < 0) { failed(); return; }
                walletHandle = Number(handle);
                done();
            }, failed);
        }, failed);
    }
    function loadKey(done) {
        if (walletLoaded) { done(); return; }
        openWallet(function() {
            walletTransport("readPassword", "isss", [walletHandle, walletFolder, "Debrid-Link", appId],
                function(value) { apiKey = String(value || ""); walletLoaded = true; done(); },
                function() { walletLoaded = true; done(); });
        }, function() { walletLoaded = true; done(); });
    }
    function requestBatch() {
        if (busy) return;
        setupMode = false;
        batchMode = true;
        files = [];
        pendingLink = "";
        batchLinks = [];
        linkChoices.clear();
        batchHosts = [];
        message = "Selecciona un servidor o marca las partes que quieres descargar.";
        panel.open();
        if (webviewItem && typeof webviewItem.runJavaScript === "function") {
            webviewItem.runJavaScript("(function(){return Array.from(new Set(Array.from(document.querySelectorAll('a[href]')).map(function(a){return a.href;}).filter(function(url){return /^https?:/.test(url) && new URL(url).hostname !== location.hostname;})));})()", function(links) {
                const hosts = [];
                (links || []).forEach(function(link) {
                    const match = String(link).match(/^https?:\/\/([^/]+)/i);
                    if (!match) return;
                    const host = match[1].toLowerCase();
                    if (hosts.indexOf(host) < 0) hosts.push(host);
                    linkChoices.append({href: String(link), host: host, selected: false});
                });
                batchHosts = hosts;
                if (hosts.length === 1) selectHost(hosts[0]);
                if (!linkChoices.count) message = "No se detectaron enlaces. Abre primero la página de Peeplink.";
            });
        }
    }
    function selectHost(host) {
        for (let i = 0; i < linkChoices.count; i++)
            linkChoices.setProperty(i, "selected", linkChoices.get(i).host === host);
    }
    function beginBatch() {
        const selected = [];
        for (let i = 0; i < linkChoices.count; i++) {
            if (linkChoices.get(i).selected && selected.indexOf(linkChoices.get(i).href) < 0)
                selected.push(linkChoices.get(i).href);
        }
        if (!selected.length) { message = "Marca al menos un enlace."; return; }
        if (selected.length > 50) { message = "Selecciona como máximo 50 enlaces por grupo."; return; }
        batchLinks = selected;
        batchIndex = 0;
        batchFiles = [];
        batchMode = false;
        busy = true;
        loadKey(function() {
            busy = false;
            if (!apiKey) configure();
            else generateBatch();
        });
    }
    function generateBatch() {
        if (busy) return;
        if (batchIndex >= batchLinks.length) {
            files = batchFiles;
            batchLinks = [];
            message = "Se prepararon " + files.length + " archivos. Iniciando las descargas…";
            files.forEach(function(file) { startFile(file); });
            return;
        }
        busy = true;
        message = "Preparando parte " + (batchIndex + 1) + " de " + batchLinks.length + "…";
        apiRequest("/downloader/add", {url: batchLinks[batchIndex]}, function(error, value) {
            busy = false;
            if (error) { batchLinks = []; files = batchFiles; fail(error); return; }
            const candidates = Array.isArray(value) ? value : [value];
            const valid = candidates.filter(function(file) { return file && /^https:\/\//i.test(String(file.downloadUrl || "")); });
            if (!valid.length) { batchLinks = []; files = batchFiles; fail("Una de las partes no produjo un enlace de descarga. No se inició el grupo."); return; }
            batchFiles = batchFiles.concat(valid);
            batchIndex++;
            generateBatch();
        });
    }

    function configure() {
        batchMode = false;
        setupMode = true;
        message = "Genera una clave de Debrid-Link y pégala aquí. Se guardará en KWallet.";
        panel.open();
    }
    function requestDownload(link) {
        if (busy) return;
        if (!/^https?:\/\//i.test(link)) { fail("Selecciona un enlace web válido."); return; }
        batchMode = false;
        batchLinks = [];
        pendingLink = link;
        files = [];
        setupMode = false;
        message = "Abriendo la cartera de KDE…";
        busy = true;
        panel.open();
        loadKey(function() {
            busy = false;
            if (!apiKey) configure();
            else generate();
        });
    }
    function apiRequest(path, payload, done) {
        const xhr = requestFactory();
        currentRequest = xhr;
        let settled = false;
        function finish(error, value) {
            if (settled) return;
            settled = true;
            requestTimeout.stop();
            currentRequest = null;
            done(error, value);
        }
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== 4) return;
            let data;
            try { data = JSON.parse(xhr.responseText); }
            catch (e) { finish("Debrid-Link no respondió correctamente. Inténtalo de nuevo.", null); return; }
            if (xhr.status < 200 || xhr.status >= 300 || data.success !== true) {
                const code = String(data.error || "");
                const errors = {
                    badToken: "La clave no es válida o ha caducado. Abre Configurar Debrid-Link para cambiarla.",
                    hostNotValid: "Debrid-Link no admite este enlace. En Peeplink, selecciona el enlace del servidor de descarga.",
                    hostNotAvailable: "Este servidor no está disponible en Debrid-Link ahora.",
                    maxLink: "Se alcanzó el límite de enlaces de tu cuenta.",
                    maxData: "Se alcanzó el límite de datos de tu cuenta.",
                    notPremium: "Este enlace requiere un plan que tu cuenta no tiene. No se realizó ninguna compra."
                };
                finish(errors[code] || "Debrid-Link no pudo procesar el enlace (" + (code || xhr.status) + ").", null);
                return;
            }
            finish(null, data.value);
        };
        xhr.open(payload === null ? "GET" : "POST", "https://debrid-link.com/api/v2" + path);
        xhr.setRequestHeader("Authorization", "Bearer " + apiKey);
        xhr.setRequestHeader("Accept", "application/json");
        if (payload !== null) xhr.setRequestHeader("Content-Type", "application/json");
        requestTimeout.restart();
        try { xhr.send(payload === null ? null : JSON.stringify(payload)); }
        catch (e) { finish("No se pudo conectar con Debrid-Link.", null); }
    }
    function saveKey(key) {
        const value = key.trim();
        if (!value || /\s/.test(value)) { message = "Pega una clave válida, sin espacios."; return; }
        apiKey = value;
        busy = true;
        message = "Comprobando la clave…";
        apiRequest("/account/infos", null, function(error) {
            if (error) { apiKey = ""; fail(error); return; }
            function finishSave(saved) {
                busy = false;
                walletLoaded = true;
                setupMode = false;
                keyField.text = "";
                storageWarning = saved ? "" : "La clave solo se conserva durante esta sesión: KWallet no está disponible.";
                message = saved ? "Clave guardada en KWallet." : "KWallet no está disponible. La clave solo se conservará hasta cerrar sesión en KDE.";
                if (batchLinks.length) generateBatch();
                else if (pendingLink) generate();
            }
            openWallet(function() {
                walletTransport("createFolder", "iss", [walletHandle, walletFolder, appId], function() {
                    walletTransport("writePassword", "issss", [walletHandle, walletFolder, "Debrid-Link", value, appId],
                        function(result) { finishSave(Number(result) === 0); }, function() { finishSave(false); });
                }, function() { finishSave(false); });
            }, function() { finishSave(false); });
        });
    }
    function generate() {
        if (!pendingLink || !apiKey || busy) return;
        busy = true;
        setupMode = false;
        message = "Generando el enlace con tu cuenta de Debrid-Link…";
        apiRequest("/downloader/add", {url: pendingLink}, function(error, value) {
            busy = false;
            if (error) { fail(error); return; }
            const candidates = Array.isArray(value) ? value : [value];
            files = candidates.filter(function(file) {
                return file && /^https:\/\//i.test(String(file.downloadUrl || ""));
            });
            if (files.length === 0) { fail("No hay un enlace de descarga listo. Inténtalo de nuevo más tarde."); return; }
            pendingLink = "";
            if (files.length === 1) startFile(files[0]);
            else message = "Selecciona el archivo que quieres descargar:";
        });
    }
    function startFile(file) {
        if (!webviewItem || !file || !/^https:\/\//i.test(String(file.downloadUrl || ""))) return;
        try {
            webviewItem.startDebridDownload(file.downloadUrl);
            message = "Iniciando la descarga…";
        } catch (e) {
            fail("No se pudo iniciar la descarga en el widget.");
        }
    }
    function downloadStarted() {
        message = "Descarga iniciada. Puedes seguir navegando.";
        panel.close();
    }
    function downloadError(text) { fail(text); }

    Timer {
        id: requestTimeout
        interval: 60000
        onTriggered: {
            const xhr = bridge.currentRequest;
            bridge.currentRequest = null;
            if (xhr) { xhr.onreadystatechange = function() {}; xhr.abort(); }
            bridge.fail("Debrid-Link tardó más de un minuto. Puedes volver a intentarlo.");
        }
    }
    Dialog {
        id: panel
        parent: bridge.webviewItem || bridge
        anchors.centerIn: parent
        width: Math.min(440, parent.width - 24)
        title: "Debrid-Link"
        modal: true
        dim: false // The compositor must not blur an overlay outside the sidebar.
        padding: 18
        palette.window: Appearance.colors.colLayer1
        palette.windowText: Appearance.colors.colOnLayer0
        palette.text: Appearance.colors.colOnLayer0
        palette.base: Appearance.colors.colLayer2
        palette.button: Appearance.colors.colLayer2
        palette.buttonText: Appearance.colors.colOnLayer0
        palette.highlight: Appearance.colors.colPrimary
        background: Rectangle {
            color: Appearance.colors.colLayer1
            radius: Appearance.rounding.normal
            border.width: 1
            border.color: Appearance.colors.colLayer0Border
        }
        header: StyledText {
            text: panel.title
            padding: 18
            bottomPadding: 4
            color: Appearance.colors.colOnLayer0
            font.pixelSize: 16
            font.bold: true
        }
        closePolicy: Popup.CloseOnEscape
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            Label {
                Layout.fillWidth: true
                text: bridge.message
                wrapMode: Text.Wrap
            }
            Label {
                Layout.fillWidth: true
                visible: bridge.storageWarning.length > 0
                text: bridge.storageWarning
                wrapMode: Text.Wrap
            }
            BusyIndicator { running: bridge.busy; visible: running; Layout.alignment: Qt.AlignHCenter }
            TextField {
                id: keyField
                Layout.fillWidth: true
                visible: bridge.setupMode
                enabled: !bridge.busy
                placeholderText: "Clave API de Debrid-Link"
                echoMode: TextInput.Password
                onAccepted: if (!bridge.busy) bridge.saveKey(text)
            }
            RowLayout {
                visible: bridge.setupMode
                Button {
                    text: "Obtener clave"
                    enabled: !bridge.busy
                    onClicked: {
                        if (bridge.webviewItem) bridge.webviewItem.url = "https://debrid-link.com/webapp/apikey";
                        panel.close();
                    }
                }
                Button { text: "Guardar"; enabled: !bridge.busy; onClicked: bridge.saveKey(keyField.text) }
            }
            ComboBox {
                Layout.fillWidth: true
                visible: bridge.batchMode
                model: bridge.batchHosts
                currentIndex: -1
                displayText: currentIndex < 0 ? "Seleccionar todas las partes de un servidor…" : currentText
                onActivated: bridge.selectHost(currentText)
            }
            ScrollView {
                ScrollBar.vertical.policy: ScrollBar.AlwaysOff
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                visible: bridge.batchMode
                clip: true
                ListView {
                    model: linkChoices
                    delegate: CheckBox {
                        width: ListView.view.width
                        text: model.href
                        checked: model.selected
                        onClicked: linkChoices.setProperty(index, "selected", checked)
                        contentItem: Label { text: parent.text; leftPadding: parent.indicator.width + 8; elide: Text.ElideMiddle; verticalAlignment: Text.AlignVCenter }
                    }
                }
            }
            Button {
                visible: bridge.batchMode
                enabled: !bridge.busy && linkChoices.count > 0
                text: "Descargar partes seleccionadas"
                onClicked: bridge.beginBatch()
            }
            Repeater {
                model: bridge.files.length > 1 ? bridge.files : []
                Button {
                    required property var modelData
                    Layout.fillWidth: true
                    text: String(modelData.name || "Descargar archivo")
                    onClicked: bridge.startFile(modelData)
                }
            }
            DialogButton { buttonText: "Cerrar"; enabled: !bridge.busy; onClicked: panel.close() }
        }
    }
}
