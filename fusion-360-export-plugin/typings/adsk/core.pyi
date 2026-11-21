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

class Application:
    activeProduct: object
    activeDocument: Document
    @staticmethod
    def get() -> Application: ...
