import enum
import json
import logging
from collections.abc import Iterator
from dataclasses import asdict, field
from dataclasses import dataclass as dataclass_python
from datetime import datetime
from functools import partial
from textwrap import indent
from typing import Annotated, Any, ClassVar, Literal, NamedTuple
from urllib.parse import parse_qs
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    conlist,
    create_model,
)
from pydantic.dataclasses import dataclass as dataclass_pydantic
from pydantic.fields import FieldInfo
from pydantic_core import ErrorDetails

logger = logging.getLogger(__name__)


class APIPath(enum.Enum):
    """API endpoint paths for the Realtime API.

    This enum defines the various API endpoints that can be accessed
    through the Realtime API.
    """

    STATUS = "/status"
    RECORDING_START = "/recording:start"
    RECORDING_STOP_AND_SAVE = "/recording:stop_and_save"
    RECORDING_CANCEL = "/recording:cancel"
    EVENT = "/event"
    CALIBRATION = "/../calibration.bin"
    TEMPLATE_DEFINITION = "/template_def"
    TEMPLATE_DATA = "/template_data"

    def full_address(
        self, address: str, port: int, protocol: str = "http", prefix: str = "/api"
    ) -> str:
        """Construct a full URL for this API endpoint."""
        return f"{protocol}://{address}:{port}" + prefix + self.value


class DiscoveredDeviceInfo(NamedTuple):
    """Information about a discovered device on the network."""

    name: str
    """Full mDNS service name.

    Follows `'PI monitor:<phone name>:<hardware id>._http._tcp.local.'` naming pattern.
    """
    server: str
    """mDNS server name. e.g. `'neon.local.' or 'pi.local.'`."""
    port: int
    """Port number, e.g. `8080`."""
    addresses: list[str]
    """IP addresses, e.g. `['192.168.0.2']`."""


class Event(NamedTuple):
    """Event information from the device."""

    name: str | None
    """Name of the event."""
    recording_id: str | None
    """ID of the recording this event belongs to."""
    timestamp: int
    """Unix epoch timestamp in nanoseconds."""

    @classmethod
    def from_dict(cls, event_dict: dict[str, Any]) -> "Event":
        """Create an Event from a dictionary.

        Args:
            event_dict: Dictionary containing event data.

        Returns:
            Event: New Event instance.

        """
        return cls(
            name=event_dict.get("name"),
            recording_id=event_dict.get("recording_id"),
            timestamp=event_dict["timestamp"],
        )

    @property
    def datetime(self) -> datetime:
        """Get the event time as a datetime object.

        Returns:
            datetime: Event time as a Python datetime.

        """
        return datetime.fromtimestamp(self.timestamp / 1e9)

    def __repr__(self) -> str:
        """Get string representation of the event.

        Returns:
            str: String representation of the event.

        """
        return (
            f"Event(name={self.name} "
            f"recording_id={self.recording_id} "
            f"timestamp_unix_ns={self.timestamp} "
            f"datetime={self.datetime})"
        )


class Phone(NamedTuple):
    """Information relative to the Companion Device."""

    battery_level: int
    """Battery percentage (0-100)"""
    battery_state: Literal["OK", "LOW", "CRITICAL"]
    """Battery state."""
    device_id: str
    """Unique device identifier."""
    device_name: str
    """Human-readable device name."""
    ip: str
    """IP address of the phone."""
    memory: int
    """Available memory in bytes."""
    memory_state: Literal["OK", "LOW", "CRITICAL"]
    """Memory state."""
    time_echo_port: int | None = None
    """Port for time synchronization, if available."""


class Hardware(NamedTuple):
    """Information about the Hardware connected (eye tracker)."""

    version: str = "unknown"
    """Hardware version.
        1-> Pupil Invisible
        2-> Neon
    """
    glasses_serial: str = "unknown"
    """Serial number of the glasses. For Pupil Invisible devices."""
    world_camera_serial: str = "unknown"
    """Serial number of the world camera. For Pupil Invisible devices."""
    module_serial: str = "unknown"
    """Serial number of the module. For Neon devices."""


class NetworkDevice(NamedTuple):
    """Information about devices discovered by the host device, not the client.

    This class represents device information made available via the websocket update
    connection by the host device (exposed via
    [`pupil_labs.realtime_api.device.Device.status_updates`][]. Devices
    discovered directly by this library are represented as
    [DiscoveredDeviceInfo][pupil_labs.realtime_api.discovery.DiscoveredDeviceInfo] and
    returned by [discover_devices][pupil_labs.realtime_api.discovery.discover_devices]
    [Network][pupil_labs.realtime_api.discovery.Network].
    """

    ip: str
    """IP address of the device."""
    device_id: str
    """Unique device identifier."""
    device_name: str
    """Human-readable device name (can be modified by the user in the Companion App
    settings)."""
    connected: bool
    """Whether the device is connected."""


class SensorName(enum.Enum):
    """Enumeration of sensor types."""

    ANY = None
    GAZE = "gaze"
    WORLD = "world"
    IMU = "imu"
    EYES = "eyes"
    EYE_EVENTS = "eye_events"
    AUDIO = "audio"


class ConnectionType(enum.Enum):
    """Enumeration of connection types."""

    ANY = None
    WEBSOCKET = "WEBSOCKET"
    DIRECT = "DIRECT"


class Sensor(NamedTuple):
    """Information about a sensor on the device."""

    sensor: str
    """Sensor type (see Name Enum)."""
    conn_type: str
    """Connection type (see ConnectionType Enum)."""
    connected: bool = False
    """Whether the sensor is connected."""
    ip: str | None = None
    """IP address of the sensor."""
    params: str | None = None
    """Additional parameters."""
    port: int | None = None
    """Port number."""
    protocol: str = "rtsp"
    """Protocol used for the connection."""
    stream_error: bool = True
    """Whether the stream errors."""

    @property
    def url(self) -> str | None:
        """Get the URL for accessing this sensor's data stream.

        Returns:
            str | None: URL if connected, None otherwise.

        """
        if self.connected:
            return f"{self.protocol}://{self.ip}:{self.port}/?{self.params}"
        return None


class Recording(NamedTuple):
    """Information about a recording."""

    action: str
    """Current recording action."""
    id: str
    """Unique recording identifier."""
    message: str
    """Status message."""
    rec_duration_ns: int
    """Recording duration in nanoseconds."""

    @property
    def rec_duration_seconds(self) -> float:
        """Get the recording duration in seconds."""
        return self.rec_duration_ns / 1e9


Component = Phone | Hardware | Sensor | Recording | NetworkDevice | Event
"""Type annotation for :class:`Status` components."""

ComponentRaw = dict[str, Any]
"""Type annotation for json-parsed responses from the REST and Websocket API."""

_model_class_map: dict[str, type[Component]] = {
    "Phone": Phone,
    "Hardware": Hardware,
    "Sensor": Sensor,
    "Recording": Recording,
    "Event": Event,
    "NetworkDevice": NetworkDevice,
}

TemplateDataFormat = Literal["api", "simple"]
"""Format specification for template data."""


def _init_cls_with_annotated_fields_only(
    cls: type[Component], d: dict[str, Any]
) -> Component:
    """Initialize a class with only the fields that are annotated.

    Args:
        cls: Class to initialize.
        d: Dictionary of field values.

    Returns:
        Instance of cls with annotated fields from d.

    """
    init_args = {}
    for attr in cls.__annotations__:
        if attr in d:
            init_args[attr] = d[attr]
    try:
        return cls(**init_args)
    except TypeError as e:
        raise ValueError(f"Missing required fields for {cls.__name__} in {d}") from e


class UnknownComponentError(ValueError):
    """Exception raised when a component cannot be parsed."""

    pass


def parse_component(raw: ComponentRaw) -> Component:
    """Initialize an explicitly modelled representation

    (:obj:`pupil_labs.realtime_api.models.Component`) from the json-parsed dictionary
    (:obj:`pupil_labs.realtime_api.models.ComponentRaw`) received from the API.

    Args:
        raw (ComponentRaw): Dictionary containing component data.

    Returns:
        Component: Parsed component instance.

    Raises:
        UnknownComponentError: If the component name cannot be mapped to an
        explicitly modelled class or the contained data does not fit the modelled
        fields.

    """
    model_name = raw["model"]
    data = raw["data"]
    try:
        model_class = _model_class_map[model_name]
        return _init_cls_with_annotated_fields_only(model_class, data)
    except KeyError as err:
        raise UnknownComponentError(
            f"Could not generate component for {model_name} from {data}"
        ) from err


@dataclass_python
class Status:
    """Represents the Companion's Device full status"""

    phone: Phone
    """Information about the connected phone. Always present."""
    hardware: Hardware
    """Information about glasses connected, won't be present if not connected"""
    sensors: list[Sensor]
    """"List of sensor information."""
    recording: Recording | None
    """Current recording, if any."""

    @classmethod
    def from_dict(cls, status_json_result: list[ComponentRaw]) -> "Status":
        """Create a Status from a list of raw components.

        Args:
            status_json_result: List of raw component dictionaries.

        Returns:
            Status: New Status instance.

        """
        phone = None
        recording = None
        hardware = Hardware()
        sensors = []
        for dct in status_json_result:
            try:
                component = parse_component(dct)
            except UnknownComponentError:
                logger.warning(f"Dropping unknown component: {dct}")
                continue
            if isinstance(component, Phone):
                phone = component
            elif isinstance(component, Hardware):
                hardware = component
            elif isinstance(component, Sensor):
                sensors.append(component)
                if (
                    component.sensor == SensorName.WORLD.value
                    and component.conn_type == ConnectionType.DIRECT.value
                ):
                    params = parse_qs(component.params)
                    is_audio_enabled = params.get("audioenable", [None])[0] == "on"
                    audio_component = component._replace(
                        sensor=SensorName.AUDIO.value, connected=is_audio_enabled
                    )
                    sensors.append(audio_component)
            elif isinstance(component, Recording):
                recording = component
            elif isinstance(component, NetworkDevice):
                pass  # no need to handle NetworkDevice updates here
            else:
                logger.warning(f"Unknown model class: {type(component).__name__}")
        sensors.sort(key=lambda s: (not s.connected, s.conn_type, s.sensor))
        if not phone:
            raise ValueError("Status data must include a 'Phone' component.")
        return cls(phone, hardware, sensors, recording)

    def update(self, component: Component) -> None:
        """Update Component.

        Args:
            component: Component to update.

        """
        if isinstance(component, Phone):
            self.phone = component
        elif isinstance(component, Hardware):
            self.hardware = component
        elif isinstance(component, Recording):
            self.recording = component
        elif isinstance(component, Sensor):
            updates = {(component.sensor, component.conn_type): component}
            if (
                component.sensor == SensorName.WORLD.value
                and component.conn_type == ConnectionType.DIRECT.value
            ):
                params = parse_qs(component.params)
                is_audio_enabled = params.get("audioenable", [None])[0] == "on"
                audio_component = component._replace(
                    sensor=SensorName.AUDIO.value, connected=is_audio_enabled
                )
                updates[audio_component.sensor, audio_component.conn_type] = (
                    audio_component
                )
            for i, sensor in enumerate(self.sensors):
                key = (sensor.sensor, sensor.conn_type)
                if key in updates:
                    self.sensors[i] = updates[key]

    def matching_sensors(
        self, name: SensorName, connection: ConnectionType
    ) -> Iterator[Sensor]:
        """Find sensors matching specified criteria.

        Args:
            name: Sensor name to match, or ANY to match any name.
            connection: Connection type to match, or ANY to match any type.

        Yields:
            Sensor: Sensors matching the criteria.

        """
        for sensor in self.sensors:
            if name is not SensorName.ANY and sensor.sensor != name.value:
                continue
            if (
                connection is not ConnectionType.ANY
                and sensor.conn_type != connection.value
            ):
                continue
            yield sensor

    def direct_world_sensor(self) -> Sensor | None:
        """Get the scene camera sensor with direct connection.

        Note:
            Pupil Invisible devices, the world camera can be detached

        """
        return next(
            self.matching_sensors(SensorName.WORLD, ConnectionType.DIRECT),
            Sensor(
                sensor=SensorName.WORLD.value, conn_type=ConnectionType.DIRECT.value
            ),
        )

    def direct_gaze_sensor(self) -> Sensor | None:
        """Get the gaze sensor with direct connection."""
        return next(
            self.matching_sensors(SensorName.GAZE, ConnectionType.DIRECT),
            Sensor(sensor=SensorName.GAZE.value, conn_type=ConnectionType.DIRECT.value),
        )

    def direct_imu_sensor(self) -> Sensor | None:
        """Get the IMU sensor with direct connection."""
        return next(
            self.matching_sensors(SensorName.IMU, ConnectionType.DIRECT),
            Sensor(sensor=SensorName.IMU.value, conn_type=ConnectionType.DIRECT.value),
        )

    def direct_eyes_sensor(self) -> Sensor | None:
        """Get the eye camera sensor with direct connection. Only available on Neon."""
        return next(
            self.matching_sensors(SensorName.EYES, ConnectionType.DIRECT),
            Sensor(sensor=SensorName.EYES.value, conn_type=ConnectionType.DIRECT.value),
        )

    def direct_eye_events_sensor(self) -> Sensor | None:
        """Get blinks, fixations _sensor_.

        Only available on Neon with Companion App version 2.9 or newer.
        """
        return next(
            self.matching_sensors(SensorName.EYE_EVENTS, ConnectionType.DIRECT),
            Sensor(
                sensor=SensorName.EYE_EVENTS.value,
                conn_type=ConnectionType.DIRECT.value,
            ),
        )

    def direct_audio_sensor(self) -> Sensor | None:
        """Get the audio sensor with direct connection."""
        return next(
            self.matching_sensors(SensorName.AUDIO, ConnectionType.DIRECT),
            Sensor(
                sensor=SensorName.AUDIO.value, conn_type=ConnectionType.DIRECT.value
            ),
        )


TemplateItemWidgetType = Literal[
    "TEXT", "PARAGRAPH", "RADIO_LIST", "CHECKBOX_LIST", "SECTION_HEADER", "PAGE_BREAK"
]
"""Type of widget to display for a template item."""

TemplateItemInputType = Literal["any", "integer", "float"]
"""Type of input data for a template item."""


@dataclass_pydantic(kw_only=True)
class TemplateItem:
    """Individual item/ question in a Template."""

    id: UUID
    """Unique identifier for the template item."""
    title: str
    """Title or question text for the template item."""
    widget_type: TemplateItemWidgetType
    """Type of widget to display for this item."""
    input_type: TemplateItemInputType
    """Type of input data for this item."""
    choices: list[str] | None
    """Available choices for selection items (e.g., radio or checkbox)."""
    help_text: str | None
    """Help or description text for the item."""
    required: bool
    """Whether the item is required or not."""

    def validate_answer(
        self,
        answer: Any,
        template_format: TemplateDataFormat = "simple",
        raise_exception: bool = True,
    ) -> list[ErrorDetails]:
        """Validate an answer for this template item.

        Args:
            answer: Answer to validate.
            template_format: Format of the template ("simple" or "api").
            raise_exception: Whether to raise an exception on validation failure.

        Returns:
            list: List of validation errors, or empty list if validation succeeded.

        Raises:
            InvalidTemplateAnswersError: If validation fails and raise_exception is
            True.

        """
        validator = self._pydantic_validator(template_format=template_format)
        if validator is None:
            logger.warning(
                f"Skipping validation for {self.widget_type} item: {self.title}"
            )
            return []
        answers_model_def = {str(self.id): validator}
        model = create_model(
            f"TemplateItem_{self.id}_Answer",
            **answers_model_def,
            __config__=ConfigDict(extra="forbid"),
        )  # type: ignore[call-overload]
        errors = []
        try:
            model.__pydantic_validator__.validate_assignment(
                model.model_construct(), str(self.id), answer
            )
        except ValidationError as e:
            errors = e.errors()

        if errors and raise_exception:
            raise InvalidTemplateAnswersError(self, answers_model_def, errors)
        return errors

    def _pydantic_validator(
        self, template_format: TemplateDataFormat
    ) -> tuple[type, FieldInfo] | None:
        """Create a Pydantic validator for this item.

        Args:
            template_format: Format of the Template ("simple" or "api").

        Returns:
            tuple: (type, field) tuple for Pydantic model creation.

        Raises:
            ValueError: If widget_type or format is invalid.

        """
        if self.widget_type in ("SECTION_HEADER", "PAGE_BREAK"):
            return None
        if self.widget_type not in (
            "RADIO_LIST",
            "TEXT",
            "PARAGRAPH",
            "CHECKBOX_LIST",
        ):
            raise ValueError("unknown widget type")

        if template_format == "simple":
            return self._simple_model_validator()
        elif template_format == "api":
            return self._api_model_validator()
        else:
            raise ValueError(f"unknown format, must be one of: {TemplateDataFormat}")

    @property
    def _value_type(self) -> type:
        """Get the Python type for this item's values.

        Returns:
            type: Python type for values.

        """
        if self.input_type == "integer":
            return int
        if self.input_type == "float":
            return float
        return str

    def _simple_model_validator(self) -> tuple[type, FieldInfo]:
        """Create a simple model validator for the template item.

        Returns:
            tuple: (type, field) tuple for Pydantic model creation.

        """
        field = Field(title=self.title, description=self.help_text)
        answer_input_type: type = self._value_type
        if self.widget_type in {"RADIO_LIST", "CHECKBOX_LIST"}:
            if not self.choices:
                logging.warning(
                    f"Choices are not defined for widget type {self.widget_type}"
                )
            # Mypy raises the [assignment] error because constructs like Annotated[...]
            # or conlist(...) aren't strictly instances of type itself, even though they
            #  represent type information for Pydantic. Thus, we need to ignore
            # the assignment error here.

            answer_input_type = Annotated[  # type: ignore[assignment]
                answer_input_type,
                AfterValidator(partial(option_in_allowed_values, allowed=self.choices)),
            ]
            if not self.required:
                field.default_factory = list

            answer_input_type = conlist(
                answer_input_type,
                min_length=1 if self.required else 0,
                max_length=None if self.widget_type == "CHECKBOX_LIST" else 1,
            )
        else:
            if self.required:
                if self.input_type == "any":
                    answer_input_type = Annotated[  # type: ignore[assignment]
                        answer_input_type, StringConstraints(min_length=1)
                    ]
            else:
                answer_input_type = answer_input_type | None  # type: ignore
                field.default = None

        return (answer_input_type, field)

    def _api_model_validator(self) -> tuple[type, FieldInfo]:
        """Create a validator for "api" format.

        Returns:
            tuple: (type, field) tuple for Pydantic model creation.

        """
        field = Field(title=self.title, description=self.help_text)
        answer_input_entry_type: type = self._value_type

        if self.widget_type in {"RADIO_LIST", "CHECKBOX_LIST"}:
            if not self.choices:
                logging.warning(
                    f"Choices are not defined for widget type {self.widget_type}"
                )
            answer_input_entry_type = Annotated[  # type: ignore[assignment]
                answer_input_entry_type,
                AfterValidator(partial(option_in_allowed_values, allowed=self.choices)),
            ]
        else:
            if self.required:
                answer_input_entry_type = Annotated[  # type: ignore
                    answer_input_entry_type, BeforeValidator(not_empty)
                ]
            else:
                if answer_input_entry_type in (int, float):
                    answer_input_entry_type = Annotated[  # type: ignore[assignment]
                        answer_input_entry_type | None,
                        BeforeValidator(allow_empty),
                    ]

        if not self.required:
            field.default_factory = lambda: [""]

        answer_input_type: type = conlist(
            answer_input_entry_type,
            min_length=1 if self.required else 0,
            max_length=None if self.widget_type == "CHECKBOX_LIST" else 1,
        )
        return (answer_input_type, field)


@dataclass_pydantic(kw_only=True)
class Template:
    """Template Class for data collection."""

    created_at: datetime
    """Creation timestamp."""
    id: UUID
    """Unique identifier."""
    name: str
    """Template name."""
    updated_at: datetime
    """Last update timestamp."""
    recording_name_format: list[str]
    """Format for recording name."""
    items: list[TemplateItem] = field(default_factory=list)
    """List of template items."""
    label_ids: list[UUID] = field(default_factory=list, metadata={"readonly": True})
    """Associated label IDs."""
    is_default_template: bool = True
    """Whether this is the default template for the Workspace"""
    description: str | None = None
    """Template description."""
    recording_ids: list[UUID] | None = None
    """Associated recording IDs."""
    published_at: datetime | None = None
    """Publication timestamp."""
    archived_at: datetime | None = None
    """Archival timestamp (if archived)."""

    def convert_from_simple_to_api_format(
        self, data: dict[str, Any]
    ) -> dict[str, list[Any]]:
        """Convert data from simple format to API format.

        Args:
            data: Data in simple format.

        Returns:
            dict: Data in API format.

        """
        api_format = {}
        for question_id, value in data.items():
            if value is None:
                value = ""
            if not isinstance(value, list):
                value = [value]

            api_format[question_id] = value
        return api_format

    def convert_from_api_to_simple_format(
        self, data: dict[str, list[str]]
    ) -> dict[str, Any]:
        """Convert data from API format to simple format.

        Args:
            data: Data in API format.

        Returns:
            dict: Data in simple format.

        """
        simple_format = {}
        for question_id, value in data.items():
            question = self.get_question_by_id(question_id)
            if question is None:
                logger.warning(
                    f"Skipping unknown question ID '{question_id}' during API to "
                    f"simple conversion."
                )
                continue
            processed_value: Any
            if question.widget_type in {"CHECKBOX_LIST", "RADIO_LIST"}:
                if question.choices is None:
                    logger.warning(
                        f"Question {question_id} (type {question.widget_type}) "
                        f"has no choices defined."
                    )
                    processed_value = []
                elif value == [""] and "" not in question.choices:
                    processed_value = []
            else:
                if not value:
                    value = [""]

                value_str = value[0]
                if question.input_type != "any":
                    processed_value = (
                        None if value_str == "" else question._value_type(value_str)
                    )
                else:
                    processed_value = value

            simple_format[question_id] = processed_value
        return simple_format

    def get_question_by_id(self, question_id: str | UUID) -> TemplateItem | None:
        """Get a template item by ID.

        Args:
            question_id: ID of the template item.

        Returns:
            TemplateItem | None: The template item, or None if not found.

        """
        for item in self.items:
            if str(item.id) == str(question_id):
                return item
        return None

    def _create_answer_model(
        self, template_format: TemplateDataFormat
    ) -> type[BaseModel]:
        """Create a Pydantic model for validating answers.

        Args:
            template_format: Format of the answers ("simple" or "api").

        Returns:
            type: Pydantic model class.

        """
        answer_types = {}
        for question in self.items:
            validator = question._pydantic_validator(template_format=template_format)
            if validator is None:
                continue
            answer_types[f"{question.id}"] = validator

        base_model = make_template_answer_model_base(self)
        model = create_model(
            f"Template_{self.id}_Answers",
            **answer_types,
            __base__=base_model,
        )  # type: ignore[call-overload]

        return model  # type: ignore[no-any-return]

    def validate_answers(
        self,
        answers: dict[str, list[str]],
        template_format: TemplateDataFormat,
        raise_exception: bool = True,
    ) -> list[ErrorDetails]:
        """Validate answers for this Template.

        Args:
            answers: Answers to validate.
            raise_exception: Whether to raise an exception on validation failure.
            template_format: Format of the answers ("simple" or "api").

        Returns:
            list: List of validation errors, or empty list if validation succeeded.

        Raises:
            InvalidTemplateAnswersError: If validation fails and raise_exception is
            True.

        """
        AnswerModel = self._create_answer_model(template_format=template_format)
        errors = []
        try:
            AnswerModel(**answers)
        except ValidationError as e:
            errors = e.errors()

        for error in errors:
            question_id = error["loc"][0]
            question = self.get_question_by_id(str(question_id))
            if question:
                error["question"] = asdict(question)  # type: ignore[typeddict-unknown-key]

        if errors and raise_exception:
            raise InvalidTemplateAnswersError(self, answers, errors)
        return errors


def not_empty(v: str) -> str:
    """Validate that a string is not empty."""
    if not len(v) > 0:
        raise ValueError("value is required")
    return v


def allow_empty(v: str) -> str | None:
    """Convert empty strings to None."""
    if v == "":
        return None
    return v


def option_in_allowed_values(value: Any, allowed: list[str] | None) -> Any:
    """Validate that a value is in a list of allowed values."""
    if allowed is None or value not in allowed:
        raise ValueError(f"{value!r} is not a valid choice from: {allowed}")
    return value


def make_template_answer_model_base(template_: Template) -> type[BaseModel]:
    """Create a base class for template answer models.

    Args:
        template_: Template to create the model for.

    Returns:
        type: Base class for template answer models.

    """

    class TemplateAnswerModelBase(BaseModel):
        template: ClassVar[Template] = template_
        model_config = ConfigDict(extra="forbid")

        def get(self, item_id: str) -> Any | None:
            return self.__dict__.get(item_id)

        def __repr__(self) -> str:
            args = []
            for item_id, _validator in self.model_fields.items():
                question = self.template.get_question_by_id(item_id)
                if not question:
                    raise ValueError(
                        f"Question with ID {item_id} not found in template."
                    )
                infos = map(
                    str,
                    [
                        question.title,
                        question.widget_type,
                        question.input_type,
                        question.choices,
                    ],
                )
                line = (
                    f"    {item_id}={self.__dict__[item_id]!r}, # {' - '.join(infos)}"
                )
                args.append(line)
            args_str = "\n".join(args)

            return f"Template_{self.template.id}_AnswerModel(\n" + args_str + "\n)"

        __str__ = __repr__

    return TemplateAnswerModelBase


class InvalidTemplateAnswersError(Exception):
    """Exception raised when template answers fail validation.

    Attributes:
        template (Template | TemplateItem): Template or item that failed validation.
        errors (list[dict]): List of validation errors.
        answers (dict): The answers that failed validation.

    """

    def __init__(
        self,
        template: Template | TemplateItem,
        answers: dict[str, Any],
        errors: list[ErrorDetails],
    ) -> None:
        self.template = template
        self.errors = errors
        self.answers = answers

    def __str__(self) -> str:
        try:
            error_lines = []
            for error in self.errors:
                error_msg = ""
                error_msg += f"location: {error['loc']}\n"
                error_msg += f"  input: {error['input']}\n"
                error_msg += f"  message: {error['msg']}\n"
                question = error.get("question")
                if question:
                    error_msg += (
                        indent(
                            f"question: {json.dumps(question, indent=4, default=str)}",
                            "  ",
                        )
                        + "\n"
                    )
                error_lines.append(indent(error_msg, "   "))
            error_lines_str = "\n".join(error_lines)

            name = "?"
            if isinstance(self.template, Template):
                name = self.template.name
            elif isinstance(self.template, TemplateItem):
                name = self.template.title

        except Exception as e:
            return f"InvalidTemplateAnswersError.__str__ error: {e}"
        else:
            return f"{name} ({self.template.id}) validation errors:\n{error_lines_str}"
