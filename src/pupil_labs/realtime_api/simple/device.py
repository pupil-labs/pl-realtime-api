import asyncio
import collections
import enum
import threading
import weakref
from typing import Any, Literal, TypeAlias, cast

from pupil_labs.neon_recording.calib import Calibration

from ..base import DeviceBase
from ..device import Device as _DeviceAsync
from ..device import StatusUpdateNotifier
from ..models import (
    Component,
    ConnectionType,
    Event,
    Recording,
    Sensor,
    SensorName,
    Status,
    Template,
    TemplateDataFormat,
)
from ..streaming import (
    BlinkEventData,
    FixationEventData,
    FixationOnsetEventData,
    IMUData,
    RTSPEyeEventStreamer,
    RTSPGazeStreamer,
    RTSPImuStreamer,
    RTSPVideoFrameStreamer,
)
from ..time_echo import TimeEchoEstimates, TimeOffsetEstimator
from ._utils import _AsyncEventManager, _StreamManager, logger
from .models import (
    MATCHED_GAZE_EYES_LABEL,
    MATCHED_ITEM_LABEL,
    GazeDataType,
    MatchedGazeEyesSceneItem,
    MatchedItem,
    SimpleVideoFrame,
)

ReceivedItemType = (
    SimpleVideoFrame
    | GazeDataType
    | IMUData
    | MatchedItem
    | MatchedGazeEyesSceneItem
    | None
)


class Device(DeviceBase):
    """Simple synchronous API for interacting with Pupil Labs devices.

    This class provides a simplified, synchronous interface to Pupil Labs devices,
    wrapping the asynchronous API with a more user-friendly interface.

    Important:
        Use [discover_devices](../../api/simple/#pupil_labs.realtime_api.simple.discover_devices)
        instead of initializing the class manually.
        See the [simple_discovery_example](../../methods/simple/connect-to-a-device/#discover-multiple-devices) example.

    """  # noqa: E501

    def __init__(
        self,
        address: str,
        port: int,
        full_name: str | None = None,
        dns_name: str | None = None,
        start_streaming_by_default: bool = False,
        suppress_decoding_warnings: bool = True,
    ) -> None:
        """Initialize a Device instance.

        Args:
            address: IP address of the device.
            port: Port number of the device.
            full_name: Full service discovery name.
            dns_name: DNS name of the device.
            start_streaming_by_default: Whether to start streaming automatically.
            suppress_decoding_warnings: Whether to suppress decoding warnings.

        """
        super().__init__(
            address,
            port,
            full_name=full_name,
            dns_name=dns_name,
            suppress_decoding_warnings=suppress_decoding_warnings,
        )
        self._status = self._get_status()
        self._start_background_worker(start_streaming_by_default)

        self._errors: list[str] = []

        self.stream_name_start_event_map = {
            SensorName.GAZE.value: self._EVENT.SHOULD_START_GAZE,
            SensorName.WORLD.value: self._EVENT.SHOULD_START_WORLD,
            SensorName.EYES.value: self._EVENT.SHOULD_START_EYES,
            SensorName.IMU.value: self._EVENT.SHOULD_START_IMU,
            SensorName.EYE_EVENTS.value: self._EVENT.SHOULD_START_EYE_EVENTS,
        }

        self.stream_name_stop_event_map = {
            SensorName.GAZE.value: self._EVENT.SHOULD_STOP_GAZE,
            SensorName.WORLD.value: self._EVENT.SHOULD_STOP_WORLD,
            SensorName.EYES.value: self._EVENT.SHOULD_STOP_EYES,
            SensorName.IMU.value: self._EVENT.SHOULD_STOP_IMU,
            SensorName.EYE_EVENTS.value: self._EVENT.SHOULD_STOP_EYE_EVENTS,
        }

    @property
    def phone_name(self) -> str:
        """Get the name of the connected phone."""
        return self._status.phone.device_name

    @property
    def phone_id(self) -> str:
        """Get the ID of the connected phone."""
        return self._status.phone.device_id

    @property
    def phone_ip(self) -> str:
        """Get the IP address of the connected phone."""
        return self._status.phone.ip

    @property
    def battery_level_percent(self) -> int:
        """Get the battery level of the connected phone in percentage."""
        return self._status.phone.battery_level

    @property
    def battery_state(self) -> Literal["OK", "LOW", "CRITICAL"]:
        """Get the battery state of the connected phone.

        Possible values are "OK", "LOW", or "CRITICAL".
        """
        return self._status.phone.battery_state

    @property
    def memory_num_free_bytes(self) -> int:
        """Get the available memory of the connected phone in bytes."""
        return self._status.phone.memory

    @property
    def memory_state(self) -> Literal["OK", "LOW", "CRITICAL"]:
        """Get the memory state of the connected phone.

        Possible values are "OK", "LOW", or "CRITICAL".
        """
        return self._status.phone.memory_state

    @property
    def version_glasses(self) -> str | None:
        """Get the version of the connected glasses.

        Returns:
            str: 1 -> Pupil Invisible, 2 -> Neon, or None -> No glasses connected.

        """
        return self._status.hardware.version

    @property
    def module_serial(self) -> str | Literal["default"] | None:
        """Returns ``None`` or ``"default"`` if no glasses are connected

        Info:
            Only available on **Neon**.
        """
        return self._status.hardware.module_serial

    @property
    def serial_number_glasses(self) -> str | Literal["default"] | None:
        """Returns ``None`` or ``"default"`` if no glasses are connected

        Info:
            Only available on **Pupil Invisible**.
        """
        return self._status.hardware.glasses_serial

    @property
    def serial_number_scene_cam(self) -> str | None:
        """Returns ``None`` if no scene camera is connected

        Info:
            Only available on **Pupil Invisible**.
        """
        return self._status.hardware.world_camera_serial

    def get_errors(self) -> list[str]:
        """Get a list of errors from the device.

        Returns:
            list[str]: List of error messages.

        """
        errors = self._errors.copy()
        self._errors.clear()

        return errors

    def world_sensor(self) -> Sensor | None:
        """Get the world sensor."""
        return self._status.direct_world_sensor()

    def gaze_sensor(self) -> Sensor | None:
        """Get the gaze sensor."""
        return self._status.direct_gaze_sensor()

    def eye_events_sensor(self) -> Sensor | None:
        """Get the eye events sensor."""
        return self._status.direct_eye_events_sensor()

    def get_calibration(self) -> Calibration:
        """Get the current cameras calibration data.

        Note that Pupil Invisible and Neon are calibration free systems, this refers to
        the intrinsincs and extrinsics of the cameras.

        Returns:
            pupil_labs.neon_recording.calib.Calibration: The calibration data.

        Raises:
            DeviceError: If the request fails.

        """

        async def _get_calibration() -> Calibration:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.get_calibration()

        return asyncio.run(_get_calibration())

    def recording_start(self) -> str:
        """Start a recording on the device.

        Wraps [pupil_labs.realtime_api.device.Device.recording_start][]

        Returns:
            str: ID of the started recording.

        Raises:
            DeviceError: If the recording could not be started. Possible reasons
            include:
                - Recording already running
                - Template has required fields
                - Low battery
                - Low storage
                - No wearer selected
                - No workspace selected
                - Setup bottom sheets not completed

        """

        async def _start_recording() -> str:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.recording_start()

        return asyncio.run(_start_recording())

    def recording_stop_and_save(self) -> None:
        """Stop and save the current recording.

        Wraps [pupil_labs.realtime_api.device.Device.recording_stop_and_save][]

        Raises:
            DeviceError: If the recording could not be stopped. Possible reasons
            include:
                - Recording not running
                - Template has required fields

        """

        async def _stop_and_save_recording() -> None:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.recording_stop_and_save()

        return asyncio.run(_stop_and_save_recording())

    def recording_cancel(self) -> None:
        """Cancel the current recording without saving it.

        Wraps [pupil_labs.realtime_api.device.Device.recording_cancel][]

        Raises:
            DeviceError: If the recording could not be cancelled. Possible reasons
            include:
                - Recording not running

        """

        async def _cancel_recording() -> None:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.recording_cancel()

        return asyncio.run(_cancel_recording())

    def send_event(
        self, event_name: str, event_timestamp_unix_ns: int | None = None
    ) -> Event:
        """Send an event to the device.

        Args:
            event_name: Name of the event.
            event_timestamp_unix_ns: Optional timestamp in unix nanoseconds.
                If None, the current time will be used.

        Returns:
            Event: The created event.

        Raises:
            DeviceError: If sending the event fails.

        """

        async def _send_event() -> Event:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.send_event(event_name, event_timestamp_unix_ns)

        return asyncio.run(_send_event())

    def get_template(self) -> Template:
        """Get the template currently selected on the device.

        Wraps [pupil_labs.realtime_api.device.Device.get_template][]

        Returns:
            Template: The currently selected template.

        Raises:
            DeviceError: If the template can't be fetched.

        """

        async def _get_template() -> Template:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.get_template()

        return asyncio.run(_get_template())

    def get_template_data(self, template_format: TemplateDataFormat = "simple") -> Any:
        """Get the template data entered on the device.

        Wraps [pupil_labs.realtime_api.device.Device.get_template_data][]

        Args:
            template_format: Format of the returned data.
                "api" returns the data as is from the api e.g., {"item_uuid": ["42"]}
                "simple" returns the data parsed e.g., {"item_uuid": 42}

        Returns:
            The result from the GET request.

        Raises:
            DeviceError: If the template's data could not be fetched.

        """

        async def _get_template_data() -> Any:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.get_template_data(template_format=template_format)

        return asyncio.run(_get_template_data())

    def post_template_data(
        self,
        template_data: dict[str, list[str]],
        template_format: TemplateDataFormat = "simple",
    ) -> Any:
        """Send the data to the currently selected template.

        Wraps [pupil_labs.realtime_api.device.Device.post_template_data][]

        Args:
            template_data: The template data to send.
            template_format: Format of the input data.
                "api" accepts the data as in realtime api format e.g.,
                {"item_uuid": ["42"]}
                "simple" accepts the data in parsed format e.g., {"item_uuid": 42}

        Returns:
            The result from the POST request.

        Raises:
            DeviceError: If the data can not be sent.
            ValueError: If invalid data type.

        """

        async def _post_template_data() -> Any:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.post_template_data(
                    template_data, template_format=template_format
                )

        return asyncio.run(_post_template_data())

    def receive_scene_video_frame(
        self, timeout_seconds: float | None = None
    ) -> SimpleVideoFrame | None:
        """Receive a scene (world) video frame.

        Args:
            timeout_seconds: Maximum time to wait for a new frame.
                If None, wait indefinitely.

        Returns:
            SimpleVideoFrame or None: The received video frame, or None if timeout was
            reached.

        """
        return cast(
            SimpleVideoFrame,
            self._receive_item(SensorName.WORLD.value, timeout_seconds),
        )

    def receive_gaze_datum(
        self, timeout_seconds: float | None = None
    ) -> GazeDataType | None:
        """Receive a gaze data point.

        Args:
            timeout_seconds: Maximum time to wait for a new gaze datum.
                If None, wait indefinitely.

        Returns:
            GazeDataType or None: The received gaze data, or None if timeout was
            reached.

        """
        return cast(
            GazeDataType, self._receive_item(SensorName.GAZE.value, timeout_seconds)
        )

    def receive_eyes_video_frame(
        self, timeout_seconds: float | None = None
    ) -> SimpleVideoFrame | None:
        """Receive an eye camera video frame.

        Args:
            timeout_seconds: Maximum time to wait for a new frame.
                If None, wait indefinitely.

        Returns:
            SimpleVideoFrame or None: The received video frame, or None if timeout
            was reached.

        """
        return cast(
            SimpleVideoFrame,
            self._receive_item(SensorName.EYES.value, timeout_seconds),
        )

    def receive_imu_datum(self, timeout_seconds: float | None = None) -> IMUData | None:
        """Receive an IMU data point.

        Args:
            timeout_seconds: Maximum time to wait for a new IMU datum.
                If None, wait indefinitely.

        Returns:
            IMUData or None: The received IMU data, or None if timeout was reached.

        """
        return cast(IMUData, self._receive_item(SensorName.IMU.value, timeout_seconds))

    def receive_eye_events(
        self, timeout_seconds: float | None = None
    ) -> FixationEventData | BlinkEventData | FixationOnsetEventData | None:
        """Receive an eye event.

        Args:
            timeout_seconds: Maximum time to wait for a new eye event.
                If None, wait indefinitely.

        Returns:
            FixationEventData | BlinkEventData | FixationOnsetEventData or None:
            The received eye event, or None if timeout was reached.

        """
        return cast(
            FixationEventData | BlinkEventData | FixationOnsetEventData,
            self._receive_item(SensorName.EYE_EVENTS.value, timeout_seconds),
        )

    def receive_matched_scene_video_frame_and_gaze(
        self, timeout_seconds: float | None = None
    ) -> MatchedItem | None:
        """Receive a matched pair of scene video frame and gaze data.

        Args:
            timeout_seconds: Maximum time to wait for a matched pair.
                If None, wait indefinitely.

        Returns:
            MatchedItem or None: The matched pair, or None if timeout was reached.

        """
        return cast(
            MatchedItem, self._receive_item(MATCHED_ITEM_LABEL, timeout_seconds)
        )

    def receive_matched_scene_and_eyes_video_frames_and_gaze(
        self, timeout_seconds: float | None = None
    ) -> MatchedGazeEyesSceneItem | None:
        """Receive a matched triplet of scene video frame, eye video frame, and gaze.

        Args:
            timeout_seconds: Maximum time to wait for a matched triplet.
                If None, wait indefinitely.

        Returns:
            MatchedGazeEyesSceneItem or None: The matched triplet, or None if timeout
            was reached.

        """
        return cast(
            MatchedGazeEyesSceneItem,
            self._receive_item(MATCHED_GAZE_EYES_LABEL, timeout_seconds),
        )

    def _receive_item(
        self, sensor: str, timeout_seconds: float | None = None
    ) -> ReceivedItemType:
        """Receive an item from the specified sensor.

        Args:
            sensor: Sensor name to receive from.
            timeout_seconds: Maximum time to wait for an item.

        Returns:
            The received item, or None if timeout was reached.

        """
        if sensor == MATCHED_ITEM_LABEL:
            self.start_stream_if_needed(SensorName.GAZE.value)
            self.start_stream_if_needed(SensorName.WORLD.value)

        elif sensor == MATCHED_GAZE_EYES_LABEL:
            self.start_stream_if_needed(SensorName.GAZE.value)
            self.start_stream_if_needed(SensorName.EYES.value)
            self.start_stream_if_needed(SensorName.WORLD.value)

        else:
            self.start_stream_if_needed(sensor)

        try:
            return self._most_recent_item[sensor].popleft()
        except IndexError:
            # no cached frame available, waiting for new one
            event_new_item = self._event_new_item[sensor]
            event_new_item.clear()
            if event_new_item.wait(timeout=timeout_seconds):
                return self._most_recent_item[sensor].popleft()
            return None

    def start_stream_if_needed(self, sensor: str) -> None:
        """Start streaming if not already streaming.

        Args:
            sensor: Sensor name to check.

        """
        if not self._is_streaming_flags[sensor].is_set():
            logger.debug("receive_* called without being streaming")
            self.streaming_start(sensor)

    def streaming_start(self, stream_name: str) -> None:
        """Start streaming data from the specified sensor.

        Args:
            stream_name: Name of the sensor to start streaming from. It can be one of
            :py:attr:`SensorName` values or None, which will start all streams.

        Raises:
            ValueError: If the stream name is not recognized.

        """
        if stream_name is None:
            for event in (
                self._EVENT.SHOULD_START_GAZE,
                self._EVENT.SHOULD_START_WORLD,
                self._EVENT.SHOULD_START_EYES,
                self._EVENT.SHOULD_START_IMU,
                self._EVENT.SHOULD_START_EYE_EVENTS,
            ):
                self._streaming_trigger_action(event)
            return

        event = self.stream_name_start_event_map[stream_name]
        self._streaming_trigger_action(event)

    def streaming_stop(self, stream_name: str | None = None) -> None:
        """Stop streaming data from the specified sensor.

        Args:
            stream_name: Name of the sensor to start streaming from. It can be one of
            :py:attr:`SensorName` values or None, which will stop all streams.

        Raises:
            ValueError: If the stream name is not recognized.

        """
        if stream_name is None:
            for event in (
                self._EVENT.SHOULD_STOP_GAZE,
                self._EVENT.SHOULD_STOP_WORLD,
                self._EVENT.SHOULD_STOP_EYES,
                self._EVENT.SHOULD_STOP_IMU,
                self._EVENT.SHOULD_STOP_EYE_EVENTS,
            ):
                self._streaming_trigger_action(event)
            return

        event = self.stream_name_stop_event_map[stream_name]
        self._streaming_trigger_action(event)

    def _streaming_trigger_action(self, action: "Device._EVENT") -> None:
        """Trigger the specified action."""
        if self._event_manager and self._background_loop:
            logger.debug(f"Sending {action.name} trigger")
            self._event_manager.trigger_threadsafe(action)
        else:
            logger.debug(f"Could not send {action.name} trigger")

    @property
    def is_currently_streaming(self) -> bool:
        """Check if data streaming is currently active.

        Returns:
            bool: True if streaming is active, False otherwise.

        """
        return any(flag.is_set() for flag in self._is_streaming_flags.values())

    def estimate_time_offset(
        self,
        number_of_measurements: int = 100,
        sleep_between_measurements_seconds: float | None = None,
    ) -> TimeEchoEstimates | None:
        """Estimate the time offset between the host device and the client.

        This uses the Time Echo protocol to estimate the clock offset between
        the device and the client.

        Args:
            number_of_measurements: Number of measurements to take.
            sleep_between_measurements_seconds: Optional sleep time between
            measurements.

        Returns:
            TimeEchoEstimates: Statistics for roundtrip durations and time offsets,
                or None if estimation failed or device doesn't support the protocol.

        See Also:
            :mod:`pupil_labs.realtime_api.time_echo` for more details.

        """
        if self._status.phone.time_echo_port is None:
            logger.warning(
                "You Pupil Invisible Companion app is out-of-date and does not yet "
                "support the Time Echo protocol. Upgrade to version 1.4.28 or newer."
            )
            return None
        estimator = TimeOffsetEstimator(
            self.phone_ip, self._status.phone.time_echo_port
        )
        return asyncio.run(
            estimator.estimate(
                number_of_measurements, sleep_between_measurements_seconds
            )
        )

    def close(self) -> None:
        """Close the device connection and stop all background threads.

        This method should be called when the device is no longer needed
        to free up resources.
        """
        if self._event_manager:
            if self.is_currently_streaming:
                self.streaming_stop()
            self._event_manager.trigger_threadsafe(self._EVENT.SHOULD_WORKER_CLOSE)
            self._auto_update_thread.join()

    def __del__(self) -> None:
        """Clean up resources when the object is destroyed."""
        self.close()

    class _EVENT(enum.Enum):
        """Internal events for the background worker."""

        SHOULD_WORKER_CLOSE = "should worker close"
        SHOULD_START_GAZE = "should start gaze"
        SHOULD_START_WORLD = "should start world"
        SHOULD_START_EYES = "should start eyes"
        SHOULD_START_IMU = "should start imu"
        SHOULD_START_EYE_EVENTS = "should start eye events"
        SHOULD_STOP_GAZE = "should stop gaze"
        SHOULD_STOP_WORLD = "should stop world"
        SHOULD_STOP_EYES = "should stop eyes"
        SHOULD_STOP_IMU = "should stop imu"
        SHOULD_STOP_EYE_EVENTS = "should stop eye events"

    def _start_background_worker(self, start_streaming_by_default: bool) -> None:
        """Start the background worker thread.

        Args:
            start_streaming_by_default: Whether to start streaming automatically.

        """
        self._event_manager = None
        self._background_loop = None

        # List of sensors that will
        sensor_names = [
            SensorName.GAZE.value,
            SensorName.WORLD.value,
            SensorName.EYES.value,
            SensorName.IMU.value,
            SensorName.EYE_EVENTS.value,
            MATCHED_ITEM_LABEL,
            MATCHED_GAZE_EYES_LABEL,
        ]
        self._most_recent_item: dict[str, collections.deque[ReceivedItemType]] = {
            name: collections.deque(maxlen=1) for name in sensor_names
        }
        self._event_new_item: dict[str, threading.Event] = {
            name: threading.Event() for name in sensor_names
        }

        # only cache 3-4 seconds worth of gaze data in case no scene camera is connected
        GazeCacheType: TypeAlias = collections.deque[tuple[float, GazeDataType]]
        EyesCacheType: TypeAlias = collections.deque[tuple[float, SimpleVideoFrame]]

        self._cached_gaze_for_matching: GazeCacheType = collections.deque(maxlen=200)
        self._cached_eyes_for_matching: EyesCacheType = collections.deque(maxlen=200)

        event_auto_update_started = threading.Event()
        self._is_streaming_flags = {
            SensorName.GAZE.value: threading.Event(),
            SensorName.WORLD.value: threading.Event(),
            SensorName.EYES.value: threading.Event(),
            SensorName.IMU.value: threading.Event(),
            SensorName.EYE_EVENTS.value: threading.Event(),
        }
        self._auto_update_thread = threading.Thread(
            target=self._auto_update,
            kwargs={
                "device_weakref": weakref.ref(self),  # weak ref to avoid cycling ref
                "auto_update_started_flag": event_auto_update_started,
                "is_streaming_flags": self._is_streaming_flags,
                "start_streaming_by_default": start_streaming_by_default,
            },
            name=f"{self} auto-update thread",
        )
        self._auto_update_thread.start()
        event_auto_update_started.wait()

    def _get_status(self) -> Status:
        """Request the device's current status.

        Wraps [pupil_labs.realtime_api.device.Device.get_status][]

        Returns:
            Status: The current device status.

        Raises:
            DeviceError: If the request fails.

        """

        async def _get_status() -> Status:
            async with _DeviceAsync.convert_from(self) as control:
                return await control.get_status()

        return asyncio.run(_get_status())

    @staticmethod
    def _auto_update(  # noqa: C901 for now
        device_weakref: weakref.ReferenceType,
        auto_update_started_flag: threading.Event,
        is_streaming_flags: dict[str, threading.Event],
        start_streaming_by_default: bool = False,
    ) -> None:
        """Background thread for auto-updating device status and handling streams.

        Args:
            device_weakref: Weak reference to the device instance.
            auto_update_started_flag: Event to signal when the update thread has
            started.
            is_streaming_flags: Dict of Event to signal streaming state.
            start_streaming_by_default: Whether to start streaming automatically.

        """
        stream_managers = {
            SensorName.GAZE.value: _StreamManager(
                device_weakref,
                RTSPGazeStreamer,
                should_be_streaming_by_default=start_streaming_by_default,
            ),
            SensorName.WORLD.value: _StreamManager(
                device_weakref,
                RTSPVideoFrameStreamer,
                should_be_streaming_by_default=start_streaming_by_default,
            ),
            SensorName.EYES.value: _StreamManager(
                device_weakref,
                RTSPVideoFrameStreamer,
                should_be_streaming_by_default=start_streaming_by_default,
            ),
            SensorName.IMU.value: _StreamManager(
                device_weakref,
                RTSPImuStreamer,
                should_be_streaming_by_default=start_streaming_by_default,
            ),
            SensorName.EYE_EVENTS.value: _StreamManager(
                device_weakref,
                RTSPEyeEventStreamer,
                should_be_streaming_by_default=start_streaming_by_default,
            ),
        }

        async def _process_status_changes(changed: Component) -> None:
            """Process status changes from the device."""
            device_instance = device_weakref()
            if device_instance is None:
                # The device object might have been garbage collected, do nothing.
                logger.warning(
                    "Device instance no longer available in _process_status_changes."
                )
                return
            if (
                isinstance(changed, Sensor)
                and changed.conn_type == ConnectionType.DIRECT.value
            ):
                if changed.sensor in stream_managers:
                    await stream_managers[changed.sensor].handle_sensor_update(changed)
                else:
                    logger.debug(f"Unhandled DIRECT sensor {changed.sensor}")

            elif isinstance(changed, Recording) and changed.action == "ERROR":
                device_instance._errors.append(changed.message)

            elif isinstance(changed, Sensor) and changed.stream_error:
                error = f"Stream error in sensor {changed.sensor}"
                if error not in device_instance._errors:
                    device_instance._errors.append(error)

        async def _auto_update_until_closed() -> None:
            """Run the auto-update loop until closed."""
            async with _DeviceAsync.convert_from(device_weakref()) as device:  # type: ignore
                event_manager = _AsyncEventManager(Device._EVENT)
                device_weakref()._event_manager = event_manager  # type: ignore
                device_weakref()._background_loop = asyncio.get_running_loop()  # type: ignore

                notifier = StatusUpdateNotifier(
                    device,
                    callbacks=[
                        device_weakref()._status.update,  # type: ignore
                        _process_status_changes,
                    ],
                )
                await notifier.receive_updates_start()
                auto_update_started_flag.set()
                if start_streaming_by_default:
                    logger.debug("Streaming started by default")
                    start_stream(SensorName.GAZE.value)
                    start_stream(SensorName.WORLD.value)
                    start_stream(SensorName.EYES.value)
                    start_stream(SensorName.IMU.value)
                    start_stream(SensorName.EYE_EVENTS.value)

                while True:
                    logger.debug("Background worker waiting for event...")
                    event = await event_manager.wait_for_first_event()
                    logger.debug(f"Background worker received {event}")

                    if event is Device._EVENT.SHOULD_WORKER_CLOSE:
                        break

                    try:
                        func = event_func_map[event]
                        stream = event_stream_map[event]
                        func(stream.value)
                    except KeyError:
                        raise RuntimeError(f"Unhandled {event!r}") from None

                await notifier.receive_updates_stop()
                device_weakref()._event_manager = None  # type: ignore

        def start_stream(stream_name: str) -> None:
            """Start streaming data from the specified sensor.

            Args:
                stream_name: Name of the sensor to start streaming from.

            """
            is_streaming_flags[stream_name].set()
            stream_managers[stream_name].should_be_streaming = True
            logger.debug(f"Streaming started {stream_name}")

        def stop_stream(stream_name: str) -> None:
            """Stop streaming data from the specified sensor.

            Args:
                stream_name: Name of the sensor to start streaming from.

            """
            stream_managers[stream_name].should_be_streaming = False
            is_streaming_flags[stream_name].clear()
            logger.debug(f"Streaming stopped {stream_name}")

        event_func_map = {
            Device._EVENT.SHOULD_START_GAZE: start_stream,
            Device._EVENT.SHOULD_START_WORLD: start_stream,
            Device._EVENT.SHOULD_START_EYES: start_stream,
            Device._EVENT.SHOULD_START_IMU: start_stream,
            Device._EVENT.SHOULD_START_EYE_EVENTS: start_stream,
            Device._EVENT.SHOULD_STOP_GAZE: stop_stream,
            Device._EVENT.SHOULD_STOP_WORLD: stop_stream,
            Device._EVENT.SHOULD_STOP_EYES: stop_stream,
            Device._EVENT.SHOULD_STOP_IMU: stop_stream,
            Device._EVENT.SHOULD_STOP_EYE_EVENTS: stop_stream,
        }

        event_stream_map = {
            Device._EVENT.SHOULD_START_GAZE: SensorName.GAZE,
            Device._EVENT.SHOULD_START_WORLD: SensorName.WORLD,
            Device._EVENT.SHOULD_START_EYES: SensorName.EYES,
            Device._EVENT.SHOULD_START_IMU: SensorName.IMU,
            Device._EVENT.SHOULD_START_EYE_EVENTS: SensorName.EYE_EVENTS,
            Device._EVENT.SHOULD_STOP_GAZE: SensorName.GAZE,
            Device._EVENT.SHOULD_STOP_WORLD: SensorName.WORLD,
            Device._EVENT.SHOULD_STOP_EYES: SensorName.EYES,
            Device._EVENT.SHOULD_STOP_IMU: SensorName.IMU,
            Device._EVENT.SHOULD_STOP_EYE_EVENTS: SensorName.EYE_EVENTS,
        }

        return asyncio.run(_auto_update_until_closed())
