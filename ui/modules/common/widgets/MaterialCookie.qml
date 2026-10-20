import QtQuick
import QtQuick.Shapes
import Quickshell
import qs.modules.common
import qs.modules.common.widgets.shapes
import "shapes/geometry/offset.js" as Offset
import "shapes/shapes/corner-rounding.js" as CornerRounding
import "shapes/shapes/rounded-polygon.js" as RoundedPolygon
import "shapes/material-shapes.js" as MaterialShapes

Item {
    id: root
    property int sides: 12  
    property int implicitSize: 100
    property alias color: shapeCanvas.color

    implicitWidth: implicitSize
    implicitHeight: implicitSize

    property var cornerRounding: new CornerRounding.CornerRounding((sides < 17 ? 1.5 : 1.1) / Math.max(sides, 1))

    ShapeCanvas {
        id: shapeCanvas
        anchors.fill: parent
        roundedPolygon: MaterialShapes.getCircle()
    }
}

