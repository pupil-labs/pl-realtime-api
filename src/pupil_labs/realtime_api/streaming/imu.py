import datetime
import logging
from collections.abc import AsyncIterator
from typing import Any, NamedTuple, cast

from deprecated import deprecated
from pupil_labs.neon_recording.stream.imu.imu_pb2 import ImuPacket  # type: ignore

from .base import RTSPRawStreamer

logger = logging.getLogger(__name__)


class Data3D(NamedTuple):
    """3D data point with x, y, z coordinates."""

    x: float
    y: float
    z: float


class Quaternion(NamedTuple):
    """Quaternion data point with x, y, z, w coordinates."""

    x: float
    y: float
    z: float
    w: float


class IMUData(NamedTuple):
    """Data from the Inertial Measurement Unit (IMU).

    Contains gyroscope, accelerometer, and rotation data from the IMU sensor.
    """

    gyro_data: Data3D
    """Gyroscope data in deg/s."""
    accel_data: Data3D
    """Accelerometer data in m/s²."""
    quaternion: Quaternion
    """ Rotation represented as a quaternion."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since Unix epoch."""

    @property
    def datetime(self) -> datetime.datetime:
        """Get timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)

    # For backward compatibility
    @property
    @deprecated(version="1.5.1", reason="Use timestamp_unix_ns() instead.")
    def timestamp_unix_nanoseconds(self) -> int:
        """Get timestamp in nanoseconds since Unix epoch.

        Warning: Deprecated
            This class property is deprecated and will be removed in future versions.
            Use timestamp_unix_ns() instead.
        """
        return self.timestamp_unix_ns


def IMUPacket_to_IMUData(imu_packet: "ImuPacket") -> IMUData:  # type: ignore[no-any-unimported]
    """Create an IMUData instance from a protobuf IMU packet.

    Args:
        imu_packet: Protobuf IMU packet.

    Returns:
        IMUData: Converted IMU data.

    """
    gyro_data = Data3D(
        x=imu_packet.gyroData.x,
        y=imu_packet.gyroData.y,
        z=imu_packet.gyroData.z,
    )
    accel_data = Data3D(
        x=imu_packet.accelData.x,
        y=imu_packet.accelData.y,
        z=imu_packet.accelData.z,
    )
    quaternion = Quaternion(
        x=imu_packet.rotVecData.x,
        y=imu_packet.rotVecData.y,
        z=imu_packet.rotVecData.z,
        w=imu_packet.rotVecData.w,
    )
    imu_data = IMUData(
        gyro_data=gyro_data,
        accel_data=accel_data,
        quaternion=quaternion,
        timestamp_unix_seconds=imu_packet.tsNs / 1e9,
    )
    return imu_data


async def receive_imu_data(
    url: str, *args: Any, **kwargs: Any
) -> AsyncIterator[IMUData]:
    """Receive IMU data from a given RTSP URL.

    Args:
        url: RTSP URL to connect to.
        *args: Additional arguments for the streamer.
        **kwargs: Additional keyword arguments for the streamer.

    Yields:
        IMUData: Parsed IMU data from the RTSP stream.

    """
    async with RTSPImuStreamer(url, *args, **kwargs) as streamer:
        assert isinstance(streamer, RTSPImuStreamer)
        async for datum in streamer.receive():
            yield cast(IMUData, datum)


class RTSPImuStreamer(RTSPRawStreamer):
    """Stream and parse IMU data from an RTSP source.

    This class extends RTSPRawStreamer to parse raw RTSP data into structured
    IMU data objects.
    """

    async def receive(  # type: ignore[override]
        self,
    ) -> AsyncIterator[IMUData]:
        """Receive and parse IMU data from the RTSP stream.

        This method parses the raw binary data into IMUData objects by using
        the protobuf deserializer.

        Yields:
            IMUData: Parsed IMU data.

        Raises:
            Exception: If there is an error parsing the IMU data.

        """
        async for data in super().receive():
            try:
                imu_packet = ImuPacket()
                imu_packet.ParseFromString(data.raw)
                imu_data = IMUPacket_to_IMUData(imu_packet)
                yield imu_data
            except Exception:
                logger.exception(f"Unable to parse imu data {data}")
                raise
