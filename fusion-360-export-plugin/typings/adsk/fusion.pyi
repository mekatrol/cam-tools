from typing import Final

from .core import BoundingBox3D, Matrix3D, ObjectCollection

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

class Sketch:
    name: str
    entityToken: str
    isVisible: bool
    sketchCurves: _CountedCollection
    geometricConstraints: _CountedCollection
    profiles: _CountedCollection
    transform: Matrix3D

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
