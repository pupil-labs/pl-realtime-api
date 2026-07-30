import typing as T
from collections.abc import Sequence
from dataclasses import dataclass, fields
from enum import Enum
from typing import Literal

from typing_extensions import NotRequired, TypedDict


class ChangeRequestParameters(TypedDict):
    ae_mode: NotRequired[Literal["auto", "manual"]]
    man_exp: NotRequired[int]
    gain: NotRequired[int]
    brightness: NotRequired[int]
    contrast: NotRequired[int]
    gamma: NotRequired[int]
    camera: Literal["world"]


@dataclass(frozen=True)
class ControlStateEnum:
    current_value: str
    allowed_values: Sequence[str]

    def validate(self, value: str) -> None:
        if value not in self.allowed_values:
            raise ValueError(f"`{value}` not in allowed_values={self.allowed_values}")


class ControlStateEnumResponse(TypedDict):
    control_name: str
    current_value: str
    allowed_values: Sequence[str]
    value_type: str


@dataclass(frozen=True)
class ControlStateInteger:
    current_value: int
    value_min: int
    value_max: int

    def validate(self, value: int) -> None:
        if not (self.value_min <= value <= self.value_max):
            raise ValueError(
                f"`{value!r}` not in range [{self.value_min!r}, {self.value_max!r}]"
            )


class ControlStateIntegerResponse(TypedDict):
    control_name: str
    current_value: int
    value_min: int
    value_max: int
    value_type: str


class ControlStateResponseEnvelope(TypedDict):
    message: str
    result: ControlStateIntegerResponse | ControlStateEnumResponse


@dataclass(frozen=True)
class CameraState:
    ae_mode: ControlStateEnum
    man_exp: ControlStateInteger
    gain: ControlStateInteger
    brightness: ControlStateInteger
    contrast: ControlStateInteger
    gamma: ControlStateInteger

    @classmethod
    def state_class_by_attr(cls, name: str) -> type[T.Any] | str | T.Any:
        return {f.name: f.type for f in fields(cls)}[name]


class Control(Enum):
    AUTOEXPOSURE_MODE = "ae_mode"
    MANUAL_EXPOSURE_TIME = "man_exp"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    GAMMA = "gamma"
    GAIN = "gain"
