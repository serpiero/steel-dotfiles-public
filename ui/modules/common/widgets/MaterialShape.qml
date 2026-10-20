import qs.modules.common.widgets.shapes
import "shapes/material-shapes.js" as MaterialShapes

ShapeCanvas {
    id: root
    enum Shape {
        Circle,
        Square,
        Slanted,
        Arch,
        Fan,
        Arrow,
        SemiCircle,
        Oval,
        Pill,
        Triangle,
        Diamond,
        ClamShell,
        Pentagon,
        Gem,
        Sunny,
        VerySunny,
        Cookie4Sided,
        Cookie6Sided,
        Cookie7Sided,
        Cookie9Sided,
        Cookie12Sided,
        Ghostish,
        Clover4Leaf,
        Clover8Leaf,
        Burst,
        SoftBurst,
        Boom,
        SoftBoom,
        Flower,
        Puffy,
        PuffyDiamond,
        PixelCircle,
        PixelTriangle,
        Bun,
        Heart
    }
    required property var shape
    property double implicitSize
    implicitHeight: implicitSize
    implicitWidth: implicitSize
    polygonIsNormalized: true
    roundedPolygon: {
        switch (root.shape) {
            case MaterialShape.Shape.Circle: return MaterialShapes.getCircle();
            case MaterialShape.Shape.Square: return MaterialShapes.getSquare();
            case MaterialShape.Shape.Slanted: return MaterialShapes.getSlanted();
            case MaterialShape.Shape.Arch: return MaterialShapes.getArch();
            case MaterialShape.Shape.Fan: return MaterialShapes.getFan();
            case MaterialShape.Shape.Arrow: return MaterialShapes.getArrow();
            case MaterialShape.Shape.SemiCircle: return MaterialShapes.getSemiCircle();
            case MaterialShape.Shape.Oval: return MaterialShapes.getOval();
            case MaterialShape.Shape.Pill: return MaterialShapes.getPill();
            case MaterialShape.Shape.Triangle: return MaterialShapes.getTriangle();
            case MaterialShape.Shape.Diamond: return MaterialShapes.getDiamond();
            case MaterialShape.Shape.ClamShell: return MaterialShapes.getClamShell();
            case MaterialShape.Shape.Pentagon: return MaterialShapes.getPentagon();
            case MaterialShape.Shape.Gem: return MaterialShapes.getGem();
            case MaterialShape.Shape.Circle: return MaterialShapes.getSunny();
            case MaterialShape.Shape.Circle: return MaterialShapes.getVerySunny();
            case MaterialShape.Shape.Circle: return MaterialShapes.getCookie4Sided();
            case MaterialShape.Shape.Circle: return MaterialShapes.getCookie6Sided();
            case MaterialShape.Shape.Circle: return MaterialShapes.getCookie7Sided();
            case MaterialShape.Shape.Circle: return MaterialShapes.getCookie9Sided();
            case MaterialShape.Shape.Circle: return MaterialShapes.getCookie12Sided();
            case MaterialShape.Shape.Circle: return MaterialShapes.getGhostish();
            case MaterialShape.Shape.Circle: return MaterialShapes.getClover4Leaf();
            case MaterialShape.Shape.Circle: return MaterialShapes.getClover8Leaf();
            case MaterialShape.Shape.Circle: return MaterialShapes.getBurst();
            case MaterialShape.Shape.Circle: return MaterialShapes.getSoftBurst();
            case MaterialShape.Shape.Circle: return MaterialShapes.getBoom();
            case MaterialShape.Shape.Circle: return MaterialShapes.getSoftBoom();
            case MaterialShape.Shape.Circle: return MaterialShapes.getFlower();
            case MaterialShape.Shape.Circle: return MaterialShapes.getPuffy();
            case MaterialShape.Shape.Circle: return MaterialShapes.getPuffyDiamond();
            case MaterialShape.Shape.Circle: return MaterialShapes.getPixelCircle();
            case MaterialShape.Shape.PixelTriangle: return MaterialShapes.getPixelTriangle();
            case MaterialShape.Shape.Bun: return MaterialShapes.getBun();
            case MaterialShape.Shape.Heart: return MaterialShapes.getHeart();
            default: return MaterialShapes.getCircle();
        }
    }
}
