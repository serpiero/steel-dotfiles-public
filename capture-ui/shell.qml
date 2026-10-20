import QtQuick
import QtQuick.Effects
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Io

PanelWindow {
    id: root
    screen: Quickshell.screens.find(s => s.name === Quickshell.env("OBSIDIAN_CAPTURE_MONITOR")) ?? Quickshell.screens[0]
    anchors { top: true; bottom: true; left: true; right: true }
    implicitWidth: screen.width
    implicitHeight: screen.height
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "obsidian:capture"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    visible: frozen.status === Image.Ready
    color: "transparent"
    property string interfaceFont: "Noto Sans"
    FileView {
        path: Quickshell.env("OBSIDIAN_CAPTURE_ROOT")+"/ui/settings/config.json"
        onLoaded: {try {root.interfaceFont=JSON.parse(text()).appearance.fonts.main;}catch(e){}}
    }
    component CaptureButton: Button {
        id: control
        implicitHeight: 34
        implicitWidth: Math.max(34,label.implicitWidth+20)
        padding: 8
        contentItem: Text {
            id: label
            text: control.text
            font.family: root.interfaceFont
            font.pixelSize: 13
            color: root.theme.text
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 8
            color: root.translucent(root.theme.selection,control.down || control.checked ? 0.95 : control.hovered ? 0.72 : 0.30)
        }
    }
    property var theme: ({background:"#161a1f",text:"#d6dbe0",muted:"#9aa5b1",selection:"#374453",accent:"#9aacc1"})
    function translucent(color, alpha) {const c=Qt.color(color);return Qt.rgba(c.r,c.g,c.b,alpha);}
    FileView {
        path: Quickshell.env("OBSIDIAN_CAPTURE_ROOT")+"/obsidian/generated/spectrum.json"
        onLoaded: {try {root.theme=Object.assign({},root.theme,JSON.parse(text()));}catch(e){}}
    }
    property bool selected: false
    property bool exporting: false
    property real sx: 0
    property real sy: 0
    property real sw: 0
    property real sh: 0
    property string tool: "move"
    property color ink: "#ebebeb"
    property real strokeWidth: 3
    property var marks: []
    property var draft: null
    property string errorMessage: ""
    property bool textEditing: false
    property var textPoint: ({x:20,y:30})
    function beginText(x,y) {
        commitText();
        textPoint={x:Math.max(0,Math.min(sw-20,x)),y:Math.max(0,Math.min(sh-24,y))};
        textEditing=true;
        Qt.callLater(()=>textEntry.forceActiveFocus());
    }
    function commitText() {
        if (!textEditing) return;
        const value=textEntry.text.trim();
        if(value) {marks=[...marks,{kind:"text",points:[{x:textPoint.x,y:textPoint.y+20}],text:value,color:ink,width:strokeWidth}];repaint();}
        textEditing=false;textEntry.text="";keyLayer.forceActiveFocus();
    }
    readonly property real captureScale: Number(Quickshell.env("OBSIDIAN_CAPTURE_SCALE")) || 1
    function setSelection(x, y, w, h) {
        sx = Math.max(0, Math.min(width - 1, x)); sy = Math.max(0, Math.min(height - 1, y));
        sw = Math.min(width - sx, Math.max(1, w)); sh = Math.min(height - sy, Math.max(1, h));
        selected = sw >= 4 && sh >= 4;
    }
    function repaint() { canvas.requestPaint(); }
    function undo() { if (marks.length) { marks = marks.slice(0, -1); repaint(); } }
    function exportCapture(action) {
        if (!selected || exporting) return;
        commitText();
        exporting = true;
        const file = Quickshell.env("OBSIDIAN_CAPTURE_EXPORT");
        capture.grabToImage(result => {
            if (!result.saveToFile(file)) { exporting = false; errorMessage = "No se pudo preparar la captura"; return; }
            exporter.command = ["python3", Quickshell.env("OBSIDIAN_CAPTURE_ROOT") + "/capture-export.py", action, file];
            exporter.running = true;
        }, Qt.size(Math.round(sw * captureScale), Math.round(sh * captureScale)));
    }
    Process {
        id: exporter
        onExited: (code, status) => {
            if (code === 0) Qt.quit();
            else { root.exporting = false; root.errorMessage = "No se pudo copiar o guardar. Puedes intentarlo de nuevo."; }
        }
    }
    IpcHandler {
        target: "capture"
        function state(): string { return JSON.stringify({x:root.sx,y:root.sy,w:root.sw,h:root.sh,selected:root.selected,marks:root.marks.length}); }
        function cancel(): void { Qt.quit(); }
        function select(x: real, y: real, w: real, h: real): void { root.setSelection(x,y,w,h); }
        function rectangle(x: real, y: real, w: real, h: real): void {
            root.marks = [...root.marks, {kind:"rect", points:[{x:x,y:y},{x:x+w,y:y+h}],color:"#b38a8e",width:3}]; root.repaint();
        }
        function text(): void { root.tool="text"; root.beginText(20,30); }
        function preview(): void { root.exportCapture("preview"); }
        function copy(): void { root.exportCapture("copy"); }
        function save(): void { root.exportCapture("save"); }
    }
    Item {
        id: keyLayer
        anchors.fill: parent
        focus: true
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Escape) Qt.quit();
            else if (event.modifiers & Qt.ControlModifier) {
                if (event.key === Qt.Key_C) root.exportCapture("copy");
                else if (event.key === Qt.Key_S) root.exportCapture("save");
                else if (event.key === Qt.Key_Z) root.undo();
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) root.exportCapture("copy");
        }
        Image { id: frozen; anchors.fill: parent; source: "file://" + Quickshell.env("OBSIDIAN_CAPTURE_IMAGE"); fillMode: Image.Stretch; cache: false }
        Rectangle { x:0; y:0; width:parent.width; height:root.selected ? root.sy : parent.height; color:"#88000000" }
        Rectangle { visible:root.selected; x:0; y:root.sy; width:root.sx; height:root.sh; color:"#88000000" }
        Rectangle { visible:root.selected; x:root.sx+root.sw; y:root.sy; width:parent.width-x; height:root.sh; color:"#88000000" }
        Rectangle { visible:root.selected; x:0; y:root.sy+root.sh; width:parent.width; height:parent.height-y; color:"#88000000" }
        MouseArea {
            anchors.fill: parent
            enabled: !root.exporting && !root.selected
            cursorShape: Qt.CrossCursor
            property real startX: 0
            property real startY: 0
            onPressed: mouse => {
                root.selected=false; root.marks=[]; root.draft=null;
                startX=mouse.x; startY=mouse.y;
                root.sx=mouse.x;root.sy=mouse.y;root.sw=0;root.sh=0;
            }
            onPositionChanged: mouse => {
                if (!pressed) return;
                root.sx=Math.min(startX,mouse.x);root.sy=Math.min(startY,mouse.y);
                root.sw=Math.abs(mouse.x-startX);root.sh=Math.abs(mouse.y-startY);
                root.selected=root.sw>=4 && root.sh>=4;
            }
            onReleased: mouse => root.setSelection(root.sx,root.sy,root.sw,root.sh)
        }
        Item {
            id: capture
            visible:root.selected
            x:root.sx; y:root.sy; width:root.sw; height:root.sh
            clip:true
            Image { x:-root.sx; y:-root.sy; width:frozen.width; height:frozen.height; source:frozen.source; fillMode:Image.Stretch; cache:false }
            Canvas {
                id:canvas
                anchors.fill:parent
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                    const ctx=getContext("2d");ctx.reset();
                    const items=root.draft ? [...root.marks,root.draft] : root.marks;
                    for (const mark of items) {
                        const p=mark.points;if (!p.length) continue;
                        ctx.strokeStyle=mark.color;ctx.fillStyle=mark.color;ctx.lineWidth=mark.width;
                        ctx.lineCap="round";ctx.lineJoin="round";ctx.globalAlpha=mark.kind==="highlight" ? 0.35 : 1;
                        if (mark.kind==="text") {ctx.font="20px sans-serif";ctx.fillText(mark.text,p[0].x,p[0].y);continue;}
                        if (mark.kind==="rect" && p.length>1) {ctx.strokeRect(p[0].x,p[0].y,p[1].x-p[0].x,p[1].y-p[0].y);continue;}
                        ctx.beginPath();ctx.moveTo(p[0].x,p[0].y);
                        for(let i=1;i<p.length;i++)ctx.lineTo(p[i].x,p[i].y);
                        ctx.stroke();
                        if(mark.kind==="arrow" && p.length>1) {
                            const last=p[p.length-1];const angle=Math.atan2(last.y-p[0].y,last.x-p[0].x);const len=14;
                            ctx.beginPath();ctx.moveTo(last.x-len*Math.cos(angle-.5),last.y-len*Math.sin(angle-.5));ctx.lineTo(last.x,last.y);ctx.lineTo(last.x-len*Math.cos(angle+.5),last.y-len*Math.sin(angle+.5));ctx.stroke();
                        }
                    }
                }
            }
            MouseArea {
                anchors.fill:parent
                enabled:!root.exporting
                cursorShape:root.tool==="move" ? Qt.SizeAllCursor : Qt.CrossCursor
                property real startX:0
                property real startY:0
                property real originalX:0
                property real originalY:0
                onPressed: mouse => {
                    startX=mouse.x;startY=mouse.y;originalX=root.sx;originalY=root.sy;
                    if(root.tool==="move")return;
                    if(root.tool==="text") {root.beginText(mouse.x,mouse.y);return;}
                    root.draft={kind:root.tool,points:[{x:mouse.x,y:mouse.y}],color:root.ink,width:root.tool==="highlight"?18:root.strokeWidth};
                    root.repaint();
                }
                onPositionChanged: mouse => {
                    if(!pressed)return;
                    if(root.tool==="move") {root.sx=Math.max(0,Math.min(root.width-root.sw,root.sx+mouse.x-startX));root.sy=Math.max(0,Math.min(root.height-root.sh,root.sy+mouse.y-startY));return;}
                    if(!root.draft)return;
                    const point={x:mouse.x,y:mouse.y};
                    root.draft.points=(root.tool==="rect" || root.tool==="arrow")?[root.draft.points[0],point]:[...root.draft.points,point];root.repaint();
                }
                onReleased: {
                    if(root.draft) {root.marks=[...root.marks,root.draft];root.draft=null;root.repaint();}
                }
            }
        }
        Rectangle {
            visible:root.selected
            x:root.sx-1;y:root.sy-1;width:root.sw+2;height:root.sh+2
            color:"transparent";border.width:1;border.color:root.theme.accent
        }
        // Eight visible handles, with continuous hit areas along every edge.
        Repeater {
            model: ["nw", "n", "ne", "e", "se", "s", "sw", "w"]
            delegate: Item {
                id: handle
                required property string modelData
                readonly property bool leftEdge: modelData.includes("w")
                readonly property bool rightEdge: modelData.includes("e")
                readonly property bool topEdge: modelData.includes("n")
                readonly property bool bottomEdge: modelData.includes("s")
                readonly property bool corner: modelData.length === 2
                visible: root.selected && !root.exporting
                x: leftEdge ? root.sx-7 : rightEdge ? root.sx+root.sw-7 : root.sx+7
                y: topEdge ? root.sy-7 : bottomEdge ? root.sy+root.sh-7 : root.sy+7
                width: corner || leftEdge || rightEdge ? 14 : Math.max(14,root.sw-14)
                height: corner || topEdge || bottomEdge ? 14 : Math.max(14,root.sh-14)
                Rectangle {
                    anchors.centerIn: parent
                    width: 9; height: 9; radius: 2
                    color: "#d8dadd"; border.color: root.theme.background; border.width: 1
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: handle.corner ? ((handle.modelData==="nw" || handle.modelData==="se") ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor) : ((handle.leftEdge || handle.rightEdge) ? Qt.SizeHorCursor : Qt.SizeVerCursor)
                    property var initial: null
                    property var pressPoint: null
                    property var initialMarks: []
                    onPressed: mouse => {
                        root.commitText();
                        initial={x:root.sx,y:root.sy,w:root.sw,h:root.sh};
                        pressPoint=mapToItem(keyLayer,mouse.x,mouse.y);
                        initialMarks=root.marks;
                    }
                    onPositionChanged: mouse => {
                        if(!pressed || !initial)return;
                        const point=mapToItem(keyLayer,mouse.x,mouse.y);
                        const dx=point.x-pressPoint.x,dy=point.y-pressPoint.y;
                        let x=initial.x,y=initial.y,right=x+initial.w,bottom=y+initial.h;
                        if(handle.leftEdge)x=Math.max(0,Math.min(right-12,x+dx));
                        if(handle.rightEdge)right=Math.min(root.width,Math.max(x+12,right+dx));
                        if(handle.topEdge)y=Math.max(0,Math.min(bottom-12,y+dy));
                        if(handle.bottomEdge)bottom=Math.min(root.height,Math.max(y+12,bottom+dy));
                        root.setSelection(x,y,right-x,bottom-y);
                        root.marks=initialMarks.map(mark => Object.assign({},mark,{points:mark.points.map(p => ({x:p.x+initial.x-x,y:p.y+initial.y-y}))}));
                        root.repaint();
                    }
                    onReleased: {initial=null;pressPoint=null;}
                }
            }
        }
        Rectangle {
            id: toolbar
            visible:root.selected && !root.exporting
            width:Math.min(buttons.implicitWidth+16,root.width-20);height:48
            x:Math.max(10,Math.min(root.width-width-10,root.sx))
            y:root.sy+root.sh+height+12<root.height ? root.sy+root.sh+10 : Math.max(10,root.sy-height-10)
            radius:14;color:root.translucent(root.theme.background,0.84);border.width:1;border.color:root.translucent(root.theme.accent,0.22)
            ShaderEffectSource {
                id: frozenToolbar
                visible: false
                sourceItem: frozen
                sourceRect: Qt.rect(toolbar.x,toolbar.y,toolbar.width,toolbar.height)
                textureSize: Qt.size(toolbar.width,toolbar.height)
                live: true
            }
            Rectangle {
                id: toolbarMask
                anchors.fill: parent
                radius: toolbar.radius
                color: "white"
                visible: false
                layer.enabled: true
            }
            MultiEffect {
                anchors.fill: parent
                source: frozenToolbar
                blurEnabled: true
                blurMax: 32
                blur: 0.75
                maskEnabled: true
                maskSource: toolbarMask
            }
            Rectangle {
                anchors.fill: parent;radius: toolbar.radius
                color: root.translucent(root.theme.background,0.84)
                border.width:1;border.color:root.translucent(root.theme.accent,0.22)
            }
            RowLayout {
                id:buttons;anchors.centerIn:parent;spacing:3
                Repeater {
                    model:[{name:"Mover",key:"move"},{name:"Trazo",key:"pen"},{name:"Flecha",key:"arrow"},{name:"Recuadro",key:"rect"},{name:"Resaltar",key:"highlight"},{name:"Texto",key:"text"}]
                    CaptureButton {
                        required property var modelData
                        text:modelData.name;checkable:true;checked:root.tool===modelData.key
                        onClicked: {root.commitText();root.tool=modelData.key;if(modelData.key==="text")root.beginText(20,30);}
                        palette.button:root.translucent(root.theme.selection,0.65);palette.buttonText:root.theme.text;palette.highlight:root.theme.selection;palette.highlightedText:root.theme.text
                    }
                }
                Repeater {
                    model:["#ebebeb","#b38a8e","#83988a"]
                    CaptureButton {
                        required property string modelData
                        implicitWidth:26;implicitHeight:30
                        onClicked:root.ink=modelData
                        contentItem:Rectangle {implicitWidth:12;implicitHeight:12;radius:6;color:modelData;border.width:root.ink===modelData?2:0;border.color:"white"}
                        background:Rectangle {radius:6;color:root.translucent(root.theme.selection,0.65)}
                    }
                }
                CaptureButton {text:"Seleccionar";onClicked:{root.commitText();root.selected=false;root.marks=[];root.draft=null;root.tool="move";}palette.button:root.translucent(root.theme.selection,0.65);palette.buttonText:root.theme.text;ToolTip.visible:hovered;ToolTip.text:"Crear una selección nueva"}
                CaptureButton {text:"↶";onClicked:root.undo();palette.button:root.translucent(root.theme.selection,0.65);palette.buttonText:root.theme.text;ToolTip.visible:hovered;ToolTip.text:"Deshacer · Ctrl+Z"}
                CaptureButton {text:"Copiar";onClicked:root.exportCapture("copy");palette.button:root.translucent(root.theme.selection,0.9);palette.buttonText:root.theme.text}
                CaptureButton {text:"Guardar";onClicked:root.exportCapture("save");palette.button:root.translucent(root.theme.selection,0.9);palette.buttonText:root.theme.text}
                CaptureButton {text:"✕";onClicked:Qt.quit();palette.button:root.translucent(root.theme.selection,0.65);palette.buttonText:root.theme.text}
            }
        }
        TextField {
            id:textEntry
            visible:root.selected && root.textEditing
            x:Math.max(0,Math.min(root.width-340,root.sx+root.textPoint.x));y:root.sy+root.textPoint.y;width:340;height:38
            placeholderText:"Escribe texto · Enter para fijar"
            Keys.onReturnPressed: event => {event.accepted=true;root.commitText();}
            Keys.onEnterPressed: event => {event.accepted=true;root.commitText();}
            Keys.onEscapePressed: {root.textEditing=false;textEntry.text="";keyLayer.forceActiveFocus();}
            Accessible.name: "Texto de la captura"
            background: Rectangle {radius:10;color:root.translucent(root.theme.background,0.9);border.color:root.translucent(root.theme.accent,0.3);border.width:1}
            font.family: root.interfaceFont
            palette.base:root.translucent(root.theme.background,0.9);palette.text:root.theme.text;palette.placeholderText:root.theme.muted
        }
        Text {
            visible:!root.selected
            anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;anchors.bottomMargin:40
            text:"Arrastra para seleccionar · Esc para cancelar";color:"white";font.pixelSize:18
        }
        Text {
            visible:root.errorMessage!=="";x:toolbar.x;y:toolbar.y-30;text:root.errorMessage;color:"#e2a4ab";font.pixelSize:15
        }
    }
    Timer {
        id: presetTimer
        interval: 50
        running: Quickshell.env("OBSIDIAN_CAPTURE_SELECTION") !== ""
        repeat: true
        onTriggered: {
            if (root.width !== root.screen.width || root.height !== root.screen.height) return;
            const p=JSON.parse(Quickshell.env("OBSIDIAN_CAPTURE_SELECTION"));
            root.setSelection(p[0],p[1],p[2],p[3]);
            stop();
        }
    }
}
