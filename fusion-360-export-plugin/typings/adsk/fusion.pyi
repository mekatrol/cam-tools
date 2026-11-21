from typing import Final

from .core import (
    Arc3D,
    BoundingBox3D,
    Circle3D,
    Ellipse3D,
    EllipticalArc3D,
    Line3D,
    Matrix3D,
    NurbsCurve3D,
    ObjectCollection,
    Point3D,
    Vector3D,
)

class DesignTypes:
    ParametricDesignType: Final[int]

class Parameter:
    name: str
    entityToken: str
    expression: str
    value: float
    unit: str
    comment: str

class UserParameter(Parameter): ...

class _CountedCollection:
    count: int
    def item(self, index: int) -> object: ...

class SketchCurve:
    entityToken: str
    isConstruction: bool
    isFixed: bool
    isVisible: bool

class SketchLine(SketchCurve):
    geometry: Line3D
    @staticmethod
    def cast(value: object) -> SketchLine | None: ...

class SketchArc(SketchCurve):
    geometry: Arc3D
    @staticmethod
    def cast(value: object) -> SketchArc | None: ...

class SketchCircle(SketchCurve):
    geometry: Circle3D
    @staticmethod
    def cast(value: object) -> SketchCircle | None: ...

class SketchEllipse(SketchCurve):
    geometry: Ellipse3D
    @staticmethod
    def cast(value: object) -> SketchEllipse | None: ...

class SketchEllipticalArc(SketchCurve):
    geometry: EllipticalArc3D
    @staticmethod
    def cast(value: object) -> SketchEllipticalArc | None: ...

class SketchFittedSpline(SketchCurve):
    geometry: NurbsCurve3D
    @staticmethod
    def cast(value: object) -> SketchFittedSpline | None: ...

class Sketch:
    name: str
    entityToken: str
    isVisible: bool
    sketchCurves: _CountedCollection
    geometricConstraints: _CountedCollection
    sketchDimensions: _CountedCollection
    profiles: _CountedCollection
    transform: Matrix3D

class TriangleMesh:
    nodeCoordinates: list[Point3D]
    nodeIndices: list[int]
    normalVectors: list[Vector3D]

class MeshCalculator:
    surfaceTolerance: float
    def calculate(self) -> TriangleMesh: ...

class MeshManager:
    def createMeshCalculator(self) -> MeshCalculator: ...

class BRepBody:
    name: str
    entityToken: str
    isVisible: bool
    isSolid: bool
    faces: _CountedCollection
    edges: _CountedCollection
    vertices: _CountedCollection
    boundingBox: BoundingBox3D
    appearance: Appearance | None
    meshManager: MeshManager

class Appearance:
    name: str
    id: str

class JointMotion:
    jointType: int

class Joint:
    name: str
    entityToken: str
    occurrenceOne: Occurrence | None
    occurrenceTwo: Occurrence | None
    isSuppressed: bool
    jointMotion: JointMotion

class Configuration:
    name: str
    entityToken: str
    isActive: bool

class Component:
    name: str
    entityToken: str
    sketches: ObjectCollection[Sketch]
    bRepBodies: ObjectCollection[BRepBody]
    occurrences: ObjectCollection[Occurrence]
    joints: ObjectCollection[Joint]
    asBuiltJoints: ObjectCollection[Joint]

class Occurrence:
    name: str
    fullPathName: str
    entityToken: str
    component: Component
    transform2: Matrix3D
    isLightBulbOn: bool
    isGrounded: bool
    childOccurrences: ObjectCollection[Occurrence]

class TimelineObject:
    entity: object | None
    isSuppressed: bool

class Design:
    designType: int
    rootComponent: Component
    allParameters: ObjectCollection[Parameter]
    userParameters: ObjectCollection[UserParameter]
    timeline: ObjectCollection[TimelineObject]
    configurations: ObjectCollection[Configuration]
    @staticmethod
    def cast(value: object) -> Design | None: ...
