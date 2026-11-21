class ObjectCollection[T]:
    @property
    def count(self) -> int: ...
    def item(self, index: int) -> T: ...

class Point3D:
    x: float
    y: float
    z: float

class BoundingBox3D:
    minPoint: Point3D
    maxPoint: Point3D

class Matrix3D:
    def getCell(self, row: int, column: int) -> float: ...

class Document:
    name: str

class FileDialog:
    title: str
    filter: str
    initialFilename: str
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
