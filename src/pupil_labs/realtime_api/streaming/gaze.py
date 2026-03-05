import datetime
import logging
import struct
from collections.abc import AsyncIterator
from typing import Any, NamedTuple, cast

from .base import RTSPData, RTSPRawStreamer

logger = logging.getLogger(__name__)


class Point(NamedTuple):
    """A point in 2D space, represented by x and y coordinates."""

    x: float
    y: float


class GazeData(NamedTuple):
    """Basic gaze data with position, timestamp and indicator of glasses worn status.

    Represents the 2D gaze point on the scene camera coordinates with a timestamp in
    nanoseconds unix epoch and an indicator of whether the glasses are being worn.
    """

    x: float
    """"X coordinate of the gaze point"""
    y: float
    """Y coordinate of the gaze point."""
    worn: bool
    """Whether the glasses are being worn."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "GazeData":
        """Create a GazeData instance from raw data.

        Args:
            data (RTSPData): The raw data received from the RTSP stream.

        Returns:
            GazeData: An instance of GazeData with the parsed values.

        """
        x, y, worn = struct.unpack("!ffB", data.raw)
        return cls(x, y, worn == 255, data.timestamp_unix_seconds)

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)


class DualMonocularGazeData(NamedTuple):
    """Experimental class for dual monocular gaze data.

    Contains separate gaze points for left and right eyes.
    """

    left: Point
    """Gaze point for the left eye."""
    right: Point
    """Gaze point for the right eye."""
    worn: bool
    """Whether the glasses are being worn."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "DualMonocularGazeData":
        """Create a DualMonocularGazeData instance from raw data.

        Args:
            data (RTSPData): The raw data received from the RTSP stream.

        Returns:
            DualMonocularGazeData: An instance of DualMonocularGazeData with the parsed
                values.

        """
        x1, y1, worn, x2, y2 = struct.unpack("!ffBff", data.raw)
        return cls(
            Point(x1, y1), Point(x2, y2), worn == 255, data.timestamp_unix_seconds
        )

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)


class EyestateGazeData(NamedTuple):
    """Gaze data with additional eye state information.

    Contains gaze point, pupil diameter, eyeball center coordinates, and optical axis
    coordinates for both left and right eyes.
    """

    x: float
    """X coordinate of the gaze point."""
    y: float
    """Y coordinate of the gaze point."""
    worn: bool
    """Whether the glasses are being worn."""
    pupil_diameter_left: float
    """Pupil diameter for the left eye."""
    eyeball_center_left_x: float
    """X coordinate of the eyeball center for the left eye."""
    eyeball_center_left_y: float
    """Y coordinate of the eyeball center for the left eye."""
    eyeball_center_left_z: float
    """Z coordinate of the eyeball center for the left eye."""
    optical_axis_left_x: float
    """X coordinate of the optical axis for the left eye."""
    optical_axis_left_y: float
    """Y coordinate of the optical axis for the left eye."""
    optical_axis_left_z: float
    """Z coordinate of the optical axis for the left eye."""
    pupil_diameter_right: float
    """Pupil diameter for the right eye."""
    eyeball_center_right_x: float
    """X coordinate of the eyeball center for the right eye."""
    eyeball_center_right_y: float
    """Y coordinate of the eyeball center for the right eye."""
    eyeball_center_right_z: float
    """Z coordinate of the eyeball center for the right eye."""
    optical_axis_right_x: float
    """X coordinate of the optical axis for the right eye."""
    optical_axis_right_y: float
    """Y coordinate of the optical axis for the right eye."""
    optical_axis_right_z: float
    """Z coordinate of the optical axis for the right eye."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "EyestateGazeData":
        """Create an EyestateGazeData instance from raw data.

        Args:
            data (RTSPData): The raw data received from the RTSP stream.

        Returns:
            EyestateGazeData: An instance of EyestateGazeData with the parsed values.

        """
        (
            x,
            y,
            worn,
            pupil_diameter_left,
            eyeball_center_left_x,
            eyeball_center_left_y,
            eyeball_center_left_z,
            optical_axis_left_x,
            optical_axis_left_y,
            optical_axis_left_z,
            pupil_diam_right,
            eyeball_center_right_x,
            eyeball_center_right_y,
            eyeball_center_right_z,
            optical_axis_right_x,
            optical_axis_right_y,
            optical_axis_right_z,
        ) = struct.unpack("!ffBffffffffffffff", data.raw)
        return cls(
            x,
            y,
            worn == 255,
            pupil_diameter_left,
            eyeball_center_left_x,
            eyeball_center_left_y,
            eyeball_center_left_z,
            optical_axis_left_x,
            optical_axis_left_y,
            optical_axis_left_z,
            pupil_diam_right,
            eyeball_center_right_x,
            eyeball_center_right_y,
            eyeball_center_right_z,
            optical_axis_right_x,
            optical_axis_right_y,
            optical_axis_right_z,
            data.timestamp_unix_seconds,
        )

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)


class EyestateEyelidGazeData(NamedTuple):
    """Gaze data with additional eyelid state information.

    Contains gaze point, pupil diameter, eyeball center coordinates, optical axis
    coordinates, as well as eyelid angles and aperture for both left and right eyes.
    """

    x: float
    """X coordinate of the gaze point."""
    y: float
    """Y coordinate of the gaze point."""
    worn: bool
    """Whether the glasses are being worn."""
    pupil_diameter_left: float
    """Pupil diameter for the left eye."""
    eyeball_center_left_x: float
    """X coordinate of the eyeball center for the left eye."""
    eyeball_center_left_y: float
    """Y coordinate of the eyeball center for the left eye."""
    eyeball_center_left_z: float
    """Z coordinate of the eyeball center for the left eye."""
    optical_axis_left_x: float
    """X coordinate of the optical axis for the left eye."""
    optical_axis_left_y: float
    """Y coordinate of the optical axis for the left eye."""
    optical_axis_left_z: float
    """Z coordinate of the optical axis for the left eye."""
    pupil_diameter_right: float
    """Pupil diameter for the right eye."""
    eyeball_center_right_x: float
    """X coordinate of the eyeball center for the right eye."""
    eyeball_center_right_y: float
    """Y coordinate of the eyeball center for the right eye."""
    eyeball_center_right_z: float
    """Z coordinate of the eyeball center for the right eye."""
    optical_axis_right_x: float
    """X coordinate of the optical axis for the right eye."""
    optical_axis_right_y: float
    """Y coordinate of the optical axis for the right eye."""
    optical_axis_right_z: float
    """Z coordinate of the optical axis for the right eye."""
    eyelid_angle_top_left: float
    """Angle of the top eyelid for the left eye(rad)."""
    eyelid_angle_bottom_left: float
    """Angle of the bottom eyelid for the left eye(rad)."""
    eyelid_aperture_left: float
    """Aperture of the eyelid for the left eye (mm)."""
    eyelid_angle_top_right: float
    """Angle of the top eyelid for the right eye (rad)."""
    eyelid_angle_bottom_right: float
    """Angle of the bottom eyelid for the right eye (rad)."""
    eyelid_aperture_right: float
    """Aperture of the eyelid for the right eye (mm)."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "EyestateEyelidGazeData":
        """Create an EyestateEyelidGazeData instance from raw data.

        Args:
            data (RTSPData): The raw data received from the RTSP stream.

        Returns:
            EyestateEyelidGazeData: An instance of EyestateEyelidGazeData with the
                parsed values.

        """
        (
            x,
            y,
            worn,
            pupil_diameter_left,
            eyeball_center_left_x,
            eyeball_center_left_y,
            eyeball_center_left_z,
            optical_axis_left_x,
            optical_axis_left_y,
            optical_axis_left_z,
            pupil_diam_right,
            eyeball_center_right_x,
            eyeball_center_right_y,
            eyeball_center_right_z,
            optical_axis_right_x,
            optical_axis_right_y,
            optical_axis_right_z,
            eyelid_angle_top_left,
            eyelid_angle_bottom_left,
            eyelid_aperture_left,
            eyelid_angle_top_right,
            eyelid_angle_bottom_right,
            eyelid_aperture_right,
        ) = struct.unpack("!ffBffffffffffffffffffff", data.raw)
        return cls(
            x,
            y,
            worn == 255,
            pupil_diameter_left,
            eyeball_center_left_x,
            eyeball_center_left_y,
            eyeball_center_left_z,
            optical_axis_left_x,
            optical_axis_left_y,
            optical_axis_left_z,
            pupil_diam_right,
            eyeball_center_right_x,
            eyeball_center_right_y,
            eyeball_center_right_z,
            optical_axis_right_x,
            optical_axis_right_y,
            optical_axis_right_z,
            eyelid_angle_top_left,
            eyelid_angle_bottom_left,
            eyelid_aperture_left,
            eyelid_angle_top_right,
            eyelid_angle_bottom_right,
            eyelid_aperture_right,
            data.timestamp_unix_seconds,
        )

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)


class EyestateEyelidDualMonoGazeData(NamedTuple):
    """Gaze data with additional eyelid state information.

    Contains binocular gaze point, left and right monocular gaze points,
    pupil diameter, eyeball center coordinates, optical axis coordinates, as well as
    eyelid angles and aperture for both left and right eyes.
    """

    x: float
    """X coordinate of the gaze point."""
    y: float
    """Y coordinate of the gaze point."""
    worn: bool
    """Whether the glasses are being worn."""
    pupil_diameter_left: float
    """Pupil diameter for the left eye."""
    eyeball_center_left_x: float
    """X coordinate of the eyeball center for the left eye."""
    eyeball_center_left_y: float
    """Y coordinate of the eyeball center for the left eye."""
    eyeball_center_left_z: float
    """Z coordinate of the eyeball center for the left eye."""
    optical_axis_left_x: float
    """X coordinate of the optical axis for the left eye."""
    optical_axis_left_y: float
    """Y coordinate of the optical axis for the left eye."""
    optical_axis_left_z: float
    """Z coordinate of the optical axis for the left eye."""
    pupil_diameter_right: float
    """Pupil diameter for the right eye."""
    eyeball_center_right_x: float
    """X coordinate of the eyeball center for the right eye."""
    eyeball_center_right_y: float
    """Y coordinate of the eyeball center for the right eye."""
    eyeball_center_right_z: float
    """Z coordinate of the eyeball center for the right eye."""
    optical_axis_right_x: float
    """X coordinate of the optical axis for the right eye."""
    optical_axis_right_y: float
    """Y coordinate of the optical axis for the right eye."""
    optical_axis_right_z: float
    """Z coordinate of the optical axis for the right eye."""
    eyelid_angle_top_left: float
    """Angle of the top eyelid for the left eye(rad)."""
    eyelid_angle_bottom_left: float
    """Angle of the bottom eyelid for the left eye(rad)."""
    eyelid_aperture_left: float
    """Aperture of the eyelid for the left eye (mm)."""
    eyelid_angle_top_right: float
    """Angle of the top eyelid for the right eye (rad)."""
    eyelid_angle_bottom_right: float
    """Angle of the bottom eyelid for the right eye (rad)."""
    eyelid_aperture_right: float
    """Aperture of the eyelid for the right eye (mm)."""
    mono_left_x: float
    """X coordinate of the left monocular gaze point."""
    mono_left_y: float
    """Y coordinate of the left monocular gaze point."""
    mono_right_x: float
    """X coordinate of the right monocular gaze point."""
    mono_right_y: float
    """Y coordinate of the right monocular gaze point."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since Unix epoch."""

    @classmethod
    def from_raw(cls, data: RTSPData) -> "EyestateEyelidDualMonoGazeData":
        """Create an EyestateEyelidDualMonoGazeData instance from raw data.

        Args:
            data (RTSPData): The raw data received from the RTSP stream.

        Returns:
            EyestateEyelidDualMonoGazeData:An instance of EyestateEyelidDualMonoGazeData
            with the parsed values.

        """
        (
            x,
            y,
            worn,
            pupil_diameter_left,
            eyeball_center_left_x,
            eyeball_center_left_y,
            eyeball_center_left_z,
            optical_axis_left_x,
            optical_axis_left_y,
            optical_axis_left_z,
            pupil_diam_right,
            eyeball_center_right_x,
            eyeball_center_right_y,
            eyeball_center_right_z,
            optical_axis_right_x,
            optical_axis_right_y,
            optical_axis_right_z,
            eyelid_angle_top_left,
            eyelid_angle_bottom_left,
            eyelid_aperture_left,
            eyelid_angle_top_right,
            eyelid_angle_bottom_right,
            eyelid_aperture_right,
            mono_left_x,
            mono_left_y,
            mono_right_x,
            mono_right_y,
        ) = struct.unpack("!ffBffffffffffffffffffffffff", data.raw)
        return cls(
            x,
            y,
            worn == 255,
            pupil_diameter_left,
            eyeball_center_left_x,
            eyeball_center_left_y,
            eyeball_center_left_z,
            optical_axis_left_x,
            optical_axis_left_y,
            optical_axis_left_z,
            pupil_diam_right,
            eyeball_center_right_x,
            eyeball_center_right_y,
            eyeball_center_right_z,
            optical_axis_right_x,
            optical_axis_right_y,
            optical_axis_right_z,
            eyelid_angle_top_left,
            eyelid_angle_bottom_left,
            eyelid_aperture_left,
            eyelid_angle_top_right,
            eyelid_angle_bottom_right,
            eyelid_aperture_right,
            mono_left_x,
            mono_left_y,
            mono_right_x,
            mono_right_y,
            data.timestamp_unix_seconds,
        )

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        return int(self.timestamp_unix_seconds * 1e9)


class BinoAndDualMonoGazeData(NamedTuple):
    """Binocular and dual monocular gaze data

    Represents the binocular 2D gaze point, the left and right dual monocular gaze
    points, on the scene camera coordinates with a timestamp in seconds unix epoch and
    an indicator of whether the glasses are being worn.

    """

    x: float
    """X coordinate of the gaze point."""
    y: float
    """Y coordinate of the gaze point."""
    worn: bool
    """Whether the glasses are being worn."""
    mono_left_x: float
    """X coordinate of the left monocular gaze point."""
    mono_left_y: float
    """Y coordinate of the left monocular gaze point."""
    mono_right_x: float
    """X coordinate of the right monocular gaze point."""
    mono_right_y: float
    """Y coordinate of the right monocular gaze point."""
    timestamp_unix_seconds: float

    @classmethod
    def from_raw(cls, data: RTSPData) -> "BinoAndDualMonoGazeData":
        """Create a BinoAndDualMonoGazeData instance from raw data.

        Args:
            data (RTSPData): The raw data received from the RTSP stream.

        Returns:
            BinoAndDualMonoGazeData: An instance of BinoAndDualMonoGazeData with the
            parsed values.

        """
        x, y, worn, mono_left_x, mono_left_y, mono_right_x, mono_right_y = (
            struct.unpack("!ffBffff", data.raw)
        )
        return cls(
            x,
            y,
            worn == 255,
            mono_left_x,
            mono_left_y,
            mono_right_x,
            mono_right_y,
            data.timestamp_unix_seconds,
        )

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)


GazeDataType = (
    GazeData
    | DualMonocularGazeData
    | EyestateGazeData
    | EyestateEyelidGazeData
    | EyestateEyelidDualMonoGazeData
    | BinoAndDualMonoGazeData
)
"""Type alias for various gaze data types."""


async def receive_gaze_data(
    url: str, *args: Any, **kwargs: Any
) -> AsyncIterator[GazeDataType]:
    """Receive gaze data from an RTSP stream.

    This is a convenience function that creates an RTSPGazeStreamer and yields
    parsed gaze data.

    Args:
        url: RTSP URL to connect to.
        *args: Additional positional arguments passed to RTSPGazeStreamer.
        **kwargs: Additional keyword arguments passed to RTSPGazeStreamer.

    Yields:
        GazeDataType: Parsed gaze data of various types.
        The type of gaze data object is determined by the length of the raw data packet:
        - 9 bytes: GazeData (basic gaze position)
        - 17 bytes: DualMonocularGazeData (left and right eye positions)
        - 65 bytes: EyestateGazeData (gaze with eye state)
        - 89 bytes: EyestateEyelidGazeData (gaze with eye state and eyelid info)
        - 105 bytes: EyestateEyelidDualMonoGazeData (binocular and dual monocular gaze
          with eyestate and eyelid info)
        - 25 bytes: BinoAndDualMonoGazeData (binocular and dual monocular gaze)

    """
    async with RTSPGazeStreamer(url, *args, **kwargs) as streamer:
        async for datum in streamer.receive():
            yield cast(GazeDataType, datum)


class RTSPGazeStreamer(RTSPRawStreamer):
    """Stream and parse gaze data from an RTSP source.

    This class extends RTSPRawStreamer to parse raw RTSP data into structured
    gaze data objects. The specific type of gaze data is determined by the
    length of the raw data packet.

    """

    async def receive(  # type: ignore[override]
        self,
    ) -> AsyncIterator[GazeDataType]:
        """Receive and parse gaze data from the RTSP stream.

        Yields:
            GazeDataType

            Parsed gaze data of various types. The type of gaze data object is
            determined by the length of the raw data packet:
        - 9 bytes: GazeData (basic gaze position)
        - 17 bytes: DualMonocularGazeData (left and right eye positions)
        - 65 bytes: EyestateGazeData (gaze with eye state)
        - 89 bytes: EyestateEyelidGazeData (gaze with eye state and eyelid info)
        - 105 bytes: EyestateEyelidDualMonoGazeData (binocular and dual monocular gaze
          with eyestate and eyelid info)
        - 25 bytes: BinoAndDualMonoGazeData (binocular and dual monocular gaze)


        Raises:
            KeyError: If the data length does not match any known format.
            Exception: If there is an error parsing the gaze data.

        """
        data_class_by_raw_len = {
            9: GazeData,
            17: DualMonocularGazeData,
            65: EyestateGazeData,
            89: EyestateEyelidGazeData,
            105: EyestateEyelidDualMonoGazeData,
            25: BinoAndDualMonoGazeData,
        }
        async for data in super().receive():
            try:
                cls = data_class_by_raw_len[len(data.raw)]
                yield cls.from_raw(data)  # type: ignore[attr-defined]
            except KeyError:
                logger.exception(f"Raw gaze data has unexpected length: {data}")
                raise
            except Exception:
                logger.exception(f"Unable to parse gaze data {data}")
                raise
