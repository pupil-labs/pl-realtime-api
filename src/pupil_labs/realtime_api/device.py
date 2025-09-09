import asyncio
import contextlib
import inspect
import json
import logging
import types
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, cast, get_args

import aiohttp
import websockets

from pupil_labs.neon_recording.calib import Calibration

from .base import DeviceBase
from .models import (
    APIPath,
    Component,
    Event,
    Status,
    Template,
    TemplateDataFormat,
    UnknownComponentError,
    parse_component,
)

logger = logging.getLogger(__name__)

UpdateCallbackSync = Callable[[Component], None]
"""Type annotation for synchronous update callbacks

See Also:
    :class:`~pupil_labs.realtime_api.models.Component`
"""

UpdateCallbackAsync = Callable[[Component], Awaitable[None]]
"""Type annotation for asynchronous update callbacks

See Also:
    :class:`~pupil_labs.realtime_api.models.Component`
"""

UpdateCallback = UpdateCallbackSync | UpdateCallbackAsync
"""Type annotation for synchronous and asynchronous callbacks"""


class DeviceError(Exception):
    """Exception raised when a device operation fails."""

    pass


class Device(DeviceBase):
    """Class representing a Pupil Labs device.

    This class provides methods to interact with the device, such as starting
    and stopping recordings, sending events, and fetching device status.
    It also provides a context manager for automatically closing the device
    session.
    """

    session: aiohttp.ClientSession | None
    """The HTTP session used for making requests."""
    template_definition: Template | None = None
    """The template definition currently selected on the device."""

    @property
    def active_session(self) -> aiohttp.ClientSession:
        """Returns the active session, raising an error if it's None."""
        if self.session is None:
            raise DeviceError("Session is not active or has been closed.")
        return self.session

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Device class."""
        super().__init__(*args, **kwargs)
        self._create_client_session()

    async def get_status(self) -> Status:
        """Get the current status of the device.

        Returns:
            Status: The current device status.

        Raises:
            DeviceError: If the request fails.

        """
        async with self.active_session.get(self.api_url(APIPath.STATUS)) as response:
            confirmation = await response.json()
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])
            result = confirmation["result"]
            logger.debug(f"[{self}.get_status] Received status: {result}")
            return Status.from_dict(result)

    async def status_updates(self) -> AsyncIterator[Component]:
        """Stream status updates from the device.

        Yields:
            Component: Status update components as they arrive.

        Auto-reconnect, see:
            https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html#websockets.asyncio.client.connect

        """
        websocket_status_endpoint = self.api_url(APIPath.STATUS, protocol="ws")
        async for websocket in websockets.connect(websocket_status_endpoint):
            try:
                async for message_raw in websocket:
                    message_json = json.loads(message_raw)
                    try:
                        component = parse_component(message_json)
                    except UnknownComponentError:
                        logger.warning(f"Dropping unknown component: {component}")
                        continue
                    yield component
            except websockets.ConnectionClosed:
                logger.debug("Websocket connection closed. Reconnecting...")
                continue
            except asyncio.CancelledError:
                logger.debug("status_updates() cancelled")
                break

    async def recording_start(self) -> str:
        """Start a recording on the device.

        Returns:
            str: ID of the started recording.

        Raises:
            DeviceError: If recording could not be started. Possible reasons include:
                - Recording already running
                - Template has required fields
                - Low battery
                - Low storage
                - No wearer selected
                - No workspace selected
                - Setup bottom sheets not completed

        """
        async with self.active_session.post(
            self.api_url(APIPath.RECORDING_START)
        ) as response:
            confirmation = await response.json()
            logger.debug(f"[{self}.start_recording] Received response: {confirmation}")
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])
            return cast(str, confirmation["result"]["id"])

    async def recording_stop_and_save(self) -> None:
        """Stop and save the current recording.

        Raises:
            DeviceError: If recording could not be stopped. Possible reasons include:
                - Recording not running
                - Template has required fields

        """
        async with self.active_session.post(
            self.api_url(APIPath.RECORDING_STOP_AND_SAVE)
        ) as response:
            confirmation = await response.json()
            logger.debug(f"[{self}.stop_recording] Received response: {confirmation}")
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])

    async def recording_cancel(self) -> None:
        """Cancel the current recording without saving it.

        Raises:
            DeviceError: If the recording could not be cancelled.
                Possible reasons include:
                - Recording not running

        """
        async with self.active_session.post(
            self.api_url(APIPath.RECORDING_CANCEL)
        ) as response:
            confirmation = await response.json()
            logger.debug(f"[{self}.stop_recording] Received response: {confirmation}")
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])

    async def send_event(
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
        event: dict[str, Any] = {"name": event_name}
        if event_timestamp_unix_ns is not None:
            event["timestamp"] = event_timestamp_unix_ns

        async with self.active_session.post(
            self.api_url(APIPath.EVENT), json=event
        ) as response:
            confirmation = await response.json()
            logger.debug(f"[{self}.send_event] Received response: {confirmation}")
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])
            confirmation["result"]["name"] = (
                event_name  # As the API does not return the name yet
            )
            return Event.from_dict(confirmation["result"])

    async def get_template(self) -> Template:
        """Get the template currently selected on device.

        Returns:
            Template: The currently selected template.

        Raises:
            DeviceError: If the template can't be fetched.

        """
        async with self.active_session.get(
            self.api_url(APIPath.TEMPLATE_DEFINITION)
        ) as response:
            confirmation = await response.json()
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])
            result = confirmation["result"]
            logger.debug(f"[{self}.get_template_def] Received template def: {result}")
            self.template_definition = Template(**result)
            return self.template_definition

    async def get_template_data(
        self, template_format: TemplateDataFormat = "simple"
    ) -> Any:
        """Get the template data entered on device.

        Args:
            template_format (TemplateDataFormat): Format of the returned data.
                - "api" returns the data as is from the api e.g., {"item_uuid": ["42"]}
                - "simple" returns the data parsed e.g., {"item_uuid": 42}

        Returns:
            The template data in the requested format.

        Raises:
            DeviceError: If the template's data could not be fetched.
            AssertionError: If an invalid format is provided.

        """
        assert template_format in get_args(TemplateDataFormat), (
            f"format should be one of {TemplateDataFormat}"
        )

        async with self.active_session.get(
            self.api_url(APIPath.TEMPLATE_DATA)
        ) as response:
            confirmation = await response.json()
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])
            result = confirmation["result"]
            logger.debug(
                f"[{self}.get_template_data] Received data's template: {result}"
            )
            if template_format == "api":
                return result
            elif template_format == "simple":
                template = await self.get_template()
                return template.convert_from_api_to_simple_format(result)

    async def post_template_data(
        self,
        template_answers: dict[str, list[str]],
        template_format: TemplateDataFormat = "simple",
    ) -> Any:
        """Set the data for the currently selected template.

        Args:
            template_answers: The template data to send.
            template_format (TemplateDataFormat): Format of the input data.
                - "api" accepts the data as in realtime api format e.g.,
                    {"item_uuid": ["42"]}
                - "simple" accepts the data in parsed format e.g., {"item_uuid": 42}

        Returns:
            The result of the operation.

        Raises:
            DeviceError: If the data can not be sent.
            ValueError: If invalid data type.
            AssertionError: If an invalid format is provided.

        """
        assert template_format in get_args(TemplateDataFormat), (
            f"format should be one of {TemplateDataFormat}"
        )

        self.template_definition = await self.get_template()

        if template_format == "simple":
            template_answers = (
                self.template_definition.convert_from_simple_to_api_format(
                    template_answers
                )
            )

        pre_populated_data = await self.get_template_data(template_format="api")
        errors = self.template_definition.validate_answers(
            pre_populated_data | template_answers, template_format="api"
        )
        if errors:
            raise ValueError(errors)

        # workaround for issue with api as it fails when passing in an empty list
        # ie. it wants [""] instead of []
        template_answers = {
            key: value or [""] for key, value in template_answers.items()
        }

        async with self.active_session.post(
            self.api_url(APIPath.TEMPLATE_DATA), json=template_answers
        ) as response:
            confirmation = await response.json()
            if response.status != 200:
                raise DeviceError(response.status, confirmation["message"])
            result = confirmation["result"]
            logger.debug(f"[{self}.get_template_data] Send data's template: {result}")
            return result

    async def close(self) -> None:
        """Close the connection to the device."""
        await self.active_session.close()
        self.session = None

    async def __aenter__(self) -> "Device":
        """Async context manager entry.

        Returns:
            Device: This device instance.

        """
        if self.session is None:
            self._create_client_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.

        """
        await self.close()

    def _create_client_session(self) -> None:
        """Create a new aiohttp client session."""
        self.session = aiohttp.ClientSession()

    async def get_calibration(self) -> Calibration:
        """Get the current cameras calibration data.

        Note that Pupil Invisible and Neon are calibration free systems, this refers to
        the intrinsincs and extrinsics of the cameras and is only available for Neon.

        Returns:
            pupil_labs.neon_recording.calib.Calibration: The calibration data.

        Raises:
            DeviceError: If the request fails.

        """
        async with self.active_session.get(
            self.api_url(APIPath.CALIBRATION)
        ) as response:
            if response.status != 200:
                raise DeviceError(response.status, "Failed to fetch calibration")

            raw_data = await response.read()
            return cast(Calibration, Calibration.from_buffer(raw_data))


class StatusUpdateNotifier:
    """Helper class for handling device status update callbacks.

    This class manages the streaming of status updates from a device
    and dispatches them to registered callbacks.

    Attributes:
        _auto_update_task (asyncio.Task | None): Task for the update loop.
        _device (Device): The device to get updates from.
        _callbacks (list[UpdateCallback]): List of callbacks to invoke.

    """

    def __init__(self, device: Device, callbacks: list[UpdateCallback]) -> None:
        self._auto_update_task: asyncio.Task | None = None
        self._device = device
        self._callbacks = callbacks

    async def receive_updates_start(self) -> None:
        """Start receiving status updates.

        This method starts the background task that receives updates
        and dispatches them to registered callbacks.
        """
        if self._auto_update_task is not None:
            logger.debug("Auto-update already started!")
            return
        self._auto_update_task = asyncio.create_task(self._auto_update())

    async def receive_updates_stop(self) -> None:
        """Stop receiving status updates.

        This method cancels the background task that receives updates.
        """
        if self._auto_update_task is None:
            logger.debug("Auto-update is not running!")
            return
        self._auto_update_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            # wait for the task to be cancelled
            await self._auto_update_task
        self._auto_update_task = None

    async def __aenter__(self) -> None:
        """Async context manager entry.

        Returns:
            StatusUpdateNotifier: This notifier instance.

        """
        await self.receive_updates_start()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.

        """
        await self.receive_updates_stop()

    async def _auto_update(self) -> None:
        """Background task that receives updates and dispatches them.

        This is an internal method that should not be called directly.
        """
        async for changed in self._device.status_updates():
            for callback in self._callbacks:
                result = callback(changed)
                if inspect.isawaitable(result):
                    await result
