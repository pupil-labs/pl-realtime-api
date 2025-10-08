import base64
import datetime
import logging
from collections.abc import AsyncIterator, ByteString
from typing import Any, NamedTuple, cast

import av
import numpy as np
import numpy.typing as npt

from .base import RTSPRawStreamer, SDPDataNotAvailableError
from .nal_unit import extract_payload_from_nal_unit

logger = logging.getLogger(__name__)

BGRBuffer = npt.NDArray[np.uint8]
"""Type annotation for raw BGR image buffers of the scene camera"""


class VideoFrame(NamedTuple):
    """A video frame with timestamp information.

    This class represents a video frame from the scene camera with associated
    timestamp information. The Class inherits VideoFrame from py.av library.
    """

    av_frame: av.VideoFrame
    """The video frame."""
    timestamp_unix_seconds: float
    """ Timestamp in seconds since Unix epoch."""

    @property
    def datetime(self) -> datetime.datetime:
        """Get timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)

    def to_ndarray(self, *args: Any, **kwargs: Any) -> npt.NDArray:
        """Convert the video frame to a NumPy array."""
        return self.av_frame.to_ndarray(*args, **kwargs)

    def bgr_buffer(self) -> BGRBuffer:
        """Convert the video frame to a BGR buffer.

        This method converts the video frame to a BGR buffer, which is a
        NumPy array with the shape (height, width, 3) and dtype uint8.
        The BGR format is commonly used in computer vision applications.

        Returns:
            BGRBuffer: The BGR buffer as a NumPy array.

        """
        return self.to_ndarray(format="bgr24")


async def receive_video_frames(
    url: str, *args: Any, **kwargs: Any
) -> AsyncIterator[VideoFrame]:
    """Receive video frames from an RTSP stream.

    This is a convenience function that creates an RTSPVideoFrameStreamer and yields
    video frames.

    Args:
        url: RTSP URL to connect to.
        *args: Additional positional arguments passed to RTSPVideoFrameStreamer.
        **kwargs: Additional keyword arguments passed to RTSPVideoFrameStreamer.

    Yields:
        VideoFrame: Parsed video frames.

    """
    async with RTSPVideoFrameStreamer(url, *args, **kwargs) as streamer:
        async for datum in streamer.receive():
            yield cast(VideoFrame, datum)


class RTSPVideoFrameStreamer(RTSPRawStreamer):
    """Stream and decode video frames from an RTSP source.

    This class extends RTSPRawStreamer to parse raw RTSP data into video frames
    using the pupil_labs.video and pyav library for decoding.

    Attributes:
        _sprop_parameter_set_payloads: Cached SPS/PPS parameters for the H.264 codec.

    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["media_type"] = "video"
        super().__init__(*args, **kwargs)
        self._sprop_parameter_set_payloads: list[ByteString] | None = None

    async def receive(self) -> AsyncIterator[VideoFrame]:  # type: ignore[override]
        """Receive and decode video frames from the RTSP stream."""
        codec = None
        frame_timestamp = None

        async for data in super().receive():
            if not codec:
                try:
                    codec = av.CodecContext.create(self.encoding, "r")
                    if self.sprop_parameter_set_payloads:
                        for param in self.sprop_parameter_set_payloads:
                            codec.parse(param)
                except SDPDataNotAvailableError as err:
                    logger.debug(
                        f"Session description protocol data not available yet: {err}"
                    )
                    continue
                except av.codec.codec.UnknownCodecError:
                    logger.exception(
                        "Unknown codec error: "
                        "Please try clearing the app's storage and cache."
                    )
                    raise
            # if pkt is the start of a new fragmented frame, parse will return a packet
            # containing the data from the previous fragments
            for packet in codec.parse(extract_payload_from_nal_unit(data.raw)):
                # use timestamp of previous packets
                for av_frame in codec.decode(packet):  # type: ignore[attr-defined]
                    if frame_timestamp is None:
                        raise ValueError("No timestamp available for the video frame.")
                    yield VideoFrame(av_frame, frame_timestamp)

            frame_timestamp = data.timestamp_unix_seconds

    @property
    def sprop_parameter_set_payloads(self) -> list[ByteString] | None:
        """Get the SPS/PPS parameter set payloads for the H.264 codec.

        These parameters are extracted from the SDP data and are required
        for initializing the H.264 decoder.

        Returns:
            list[ByteString]: List of parameter set payloads.

        Raises:
            SDPDataNotAvailableError: If SDP data is missing required fields.

        """
        if self._sprop_parameter_set_payloads is None:
            try:
                attributes = self.reader.get_primary_media()["attributes"]
                sprop_parameter_sets = attributes["fmtp"]["sprop-parameter-sets"]
                params = (
                    base64.b64decode(param) for param in sprop_parameter_sets.split(",")
                )
                self._sprop_parameter_set_payloads = [
                    extract_payload_from_nal_unit(param) for param in params
                ]
            except (IndexError, KeyError) as err:
                raise SDPDataNotAvailableError(
                    f"SDP data is missing {err} field"
                ) from err

        return self._sprop_parameter_set_payloads
