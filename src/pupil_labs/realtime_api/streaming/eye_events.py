import datetime
import logging
import struct
from collections.abc import AsyncIterator
from typing import Any, NamedTuple, cast

from .base import RTSPData, RTSPRawStreamer

logger = logging.getLogger(__name__)


class BlinkEventData(NamedTuple):
    """Data for a blink event.

    Represents a detected blink event with timing information.
    """

    event_type: int
    """Type of event (4 -> blink events)."""
    start_time_ns: int
    """Start time of the blink in nanoseconds."""
    end_time_ns: int
    """End time of the blink in nanoseconds."""
    rtp_ts_unix_seconds: float
    """RTP timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "BlinkEventData":
        """Create a BlinkEventData instance from raw RTSP data."""
        (
            event_type,
            start_time_ns,
            end_time_ns,
        ) = struct.unpack("!iqq", data.raw)
        return cls(event_type, start_time_ns, end_time_ns, data.timestamp_unix_seconds)

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.rtp_ts_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since the Unix epoch."""
        return int(self.rtp_ts_unix_seconds * 1e9)


class FixationEventData(NamedTuple):
    """Data for a fixation or saccade event.

    Represents a completed fixation or saccade event with detailed information.
    """

    event_type: int
    """Type of event (0 for saccade, 1 for fixation)."""
    start_time_ns: int
    """Start time of the event in nanoseconds."""
    end_time_ns: int
    """End time of the event in nanoseconds."""
    start_gaze_x: float
    """Start gaze x-coordinate in pixels."""
    start_gaze_y: float
    """Start gaze y-coordinate in pixels."""
    end_gaze_x: float
    """End gaze x-coordinate in pixels."""
    end_gaze_y: float
    """End gaze y-coordinate in pixels."""
    mean_gaze_x: float
    """Mean gaze x-coordinate in pixels."""
    mean_gaze_y: float
    """Mean gaze y-coordinate in pixels."""
    amplitude_pixels: float
    """Amplitude in pixels."""
    amplitude_angle_deg: float
    """Amplitude in degrees."""
    mean_velocity: float
    """Mean velocity in pixels per degree."""
    max_velocity: float
    """Maximum velocity in pixels per degree."""
    rtp_ts_unix_seconds: float
    """RTP timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "FixationEventData":
        """Create a FixationEventData instance from raw RTSP data."""
        (
            event_type,
            start_time_ns,
            end_time_ns,
            start_gaze_x,
            start_gaze_y,
            end_gaze_x,
            end_gaze_y,
            mean_gaze_x,
            mean_gaze_y,
            amplitude_pixels,
            amplitude_angle_deg,
            mean_velocity,
            max_velocity,
        ) = struct.unpack("!iqqffffffffff", data.raw)
        return cls(
            event_type,
            start_time_ns,
            end_time_ns,
            start_gaze_x,
            start_gaze_y,
            end_gaze_x,
            end_gaze_y,
            mean_gaze_x,
            mean_gaze_y,
            amplitude_pixels,
            amplitude_angle_deg,
            mean_velocity,
            max_velocity,
            data.timestamp_unix_seconds,
        )

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.rtp_ts_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since the Unix epoch."""
        return int(self.rtp_ts_unix_seconds * 1e9)


class FixationOnsetEventData(NamedTuple):
    """Data for a fixation or saccade onset event.

    Represents the beginning of a fixation or saccade event.
    """

    event_type: int
    """Type of event (2 for saccade onset, 3 for fixation onset)."""
    start_time_ns: int
    """Start time of the event in nanoseconds."""
    rtp_ts_unix_seconds: float
    """RTP timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "FixationOnsetEventData":
        (
            event_type,
            start_time_ns,
        ) = struct.unpack("!iq", data.raw)
        """Create a FixationOnsetEventData instance from raw RTSP data."""
        return cls(event_type, start_time_ns, data.timestamp_unix_seconds)

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.rtp_ts_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since the Unix epoch."""
        return int(self.rtp_ts_unix_seconds * 1e9)


async def receive_eye_events_data(
    url: str, *args: Any, **kwargs: Any
) -> AsyncIterator[FixationEventData | FixationOnsetEventData | BlinkEventData]:
    """Receive eye events data from an RTSP stream.

    This is a convenience function that creates an RTSPEyeEventStreamer and yields
    parsed eye event data.

    Args:
        url: RTSP URL to connect to.
        *args: Additional positional arguments passed to RTSPEyeEventStreamer.
        **kwargs: Additional keyword arguments passed to RTSPEyeEventStreamer.

    Yields:
        FixationEventData: Parsed fixation event data.

    """
    async with RTSPEyeEventStreamer(url, *args, **kwargs) as streamer:
        async for datum in streamer.receive():
            yield cast(
                FixationEventData | FixationOnsetEventData | BlinkEventData, datum
            )


class RTSPEyeEventStreamer(RTSPRawStreamer):
    """Stream and parse eye events from an RTSP source.

    This class extends RTSPRawStreamer to parse raw RTSP data into structured
    eye event data objects.
    """

    async def receive(  # type: ignore[override]
        self,
    ) -> AsyncIterator[FixationEventData | FixationOnsetEventData | BlinkEventData]:
        """Receive and parse eye events from the RTSP stream.

        Yields:
            FixationEventData | FixationOnsetEventData | BlinkEventData: Parsed eye
                event data.

        Raises:
            KeyError: If the event type is not recognized.
            Exception: If there is an error parsing the event data.

        """
        data_class_by_type = {
            0: FixationEventData,
            1: FixationEventData,
            2: FixationOnsetEventData,
            3: FixationOnsetEventData,
            4: BlinkEventData,
            5: None,  # KEEPALIVE MSG, SKIP
        }
        async for data in super().receive():
            try:
                event_type = struct.unpack_from("!i", data.raw)[0]
                cls = data_class_by_type[event_type]
                if cls is not None:
                    yield cls.from_raw(data)
            except KeyError:
                logger.exception(f"Raw eye event data has unexpected type: {data}")
                raise
            except Exception:
                logger.exception(f"Unable to parse eye event data {data}")
                raise
