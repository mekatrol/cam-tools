class ObjectCollection[T]:
    @property
    def count(self) -> int: ...
    def item(self, index: int) -> T: ...

class Point3D:
    x: float
    y: float
    z: float

class Vector3D:
    x: float
    y: float
    z: float

class Line3D:
    startPoint: Point3D
    endPoint: Point3D

class Arc3D:
    center: Point3D
    normal: Vector3D
    startPoint: Point3D
    endPoint: Point3D
    radius: float
    startAngle: float
    endAngle: float

class Circle3D:
    center: Point3D
    normal: Vector3D
    radius: float

class Ellipse3D:
    center: Point3D
    normal: Vector3D
    majorAxis: Vector3D
    majorRadius: float
    minorRadius: float

class EllipticalArc3D(Ellipse3D):
    startAngle: float
    endAngle: float

class CurveEvaluator3D:
    def getParameterExtents(self) -> tuple[bool, float, float]: ...
    def getStrokes(
        self, start_parameter: float, end_parameter: float, tolerance: float
    ) -> tuple[bool, list[Point3D]]: ...

class NurbsCurve3D:
    degree: int
    isPeriodic: bool
    isRational: bool
    controlPoints: list[Point3D]
    knots: list[float]
    weights: list[float]
    evaluator: CurveEvaluator3D

class BoundingBox3D:
    minPoint: Point3D
    maxPoint: Point3D

class Matrix3D:
    def getCell(self, row: int, column: int) -> float: ...

class Document:
    name: str

class DialogResults:
    DialogOK: int

class FileDialog:
    title: str
    filter: str
    filename: str
    def showSave(self) -> int: ...

class ProgressDialog:
    isCancelButtonShown: bool
    progressValue: int
    wasCancelled: bool
    def show(self, title: str, message: str, minimum: int, maximum: int) -> None: ...
    def hide(self) -> None: ...

class UserInterface:
    def messageBox(self, message: str) -> int: ...
    def createFileDialog(self) -> FileDialog: ...
    def createProgressDialog(self) -> ProgressDialog: ...

class Application:
    activeProduct: object
    activeDocument: Document
    userInterface: UserInterface
    @staticmethod
    def get() -> Application: ...
