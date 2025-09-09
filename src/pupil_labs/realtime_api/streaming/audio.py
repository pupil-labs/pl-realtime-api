import binascii
import datetime
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any, NamedTuple, cast

import av
import numpy.typing as npt

from .au_unit import extract_frames_from_au_packet
from .base import RTSPRawStreamer, SDPDataNotAvailableError

logger = logging.getLogger(__name__)


class AudioFrame(NamedTuple):
    """An audio frame with timestamp information.

    This class represents an audio frame from the audio stream with associated
    timestamp information. The Class inherits AudioFrame from py.av library.

    Note:
        Audio in Neon is streamed as fltp mono 8K, this class takes the decoded packets
        as av.AudioFrames.
    """

    av_frame: av.AudioFrame
    """The audio frame."""
    timestamp_unix_seconds: float
    """ Timestamp in seconds since Unix epoch."""
    resampler: av.AudioResampler
    """A reference to a shared AudioResampler instance."""

    @property
    def datetime(self) -> datetime.datetime:
        """Get timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get timestamp in nanoseconds since Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)

    def to_ndarray(self, *args: Any, **kwargs: Any) -> npt.NDArray:
        """Convert the audio frame to a NumPy array."""
        return self.av_frame.to_ndarray(*args, **kwargs)

    def to_resampled_ndarray(self, *args: Any, **kwargs: Any) -> Iterator[npt.NDArray]:
        """Converts the audio frame to a resampled s16 NumPy array"""
        for frame in self.resampler.resample(self.av_frame):
            yield frame.to_ndarray(*args, **kwargs)


async def receive_audio_frames(
    url: str, *args: Any, **kwargs: Any
) -> AsyncIterator[AudioFrame]:
    """Receive audio frames from an RTSP stream.

    This is a convenience function that creates an RTSPAudioStreamer and yields
    decoded audio frames.

    Args:
        url: RTSP URL to connect to.
        *args: Additional positional arguments passed to RTSPAudioStreamer.
        **kwargs: Additional keyword arguments passed to RTSPAudioStreamer.

    Yields:
        AudioFrame: Decoded audio frames with timestamp information.
    """
    async with RTSPAudioStreamer(url, *args, **kwargs) as streamer:
        async for datum in streamer.receive():
            yield cast(AudioFrame, datum)


class RTSPAudioStreamer(RTSPRawStreamer):
    """Stream and decode audio frames from an RTSP source."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["media_type"] = "audio"
        super().__init__(*args, **kwargs)
        self._codec_config: str | None = None
        self._resampler: av.AudioResampler | None = None

    def _get_resampler(self, frame: av.AudioFrame) -> av.AudioResampler:
        """Create an AudioResampler needed for playback audio with SoundDevice.

        There is no fltp playback support in SoundDevice, so we need to resample
        to s16. We create the resampler on the first frame and reuse it for all
        subsequent frames.
        """
        if self._resampler is None:
            self._resampler = av.AudioResampler(
                format="s16",
                layout=frame.layout.name,
                rate=frame.sample_rate,
            )
        return self._resampler

    async def receive(self) -> AsyncIterator[AudioFrame]:  # type: ignore[override]
        """Receive and decode audio frames from the RTSP stream."""
        codec = None
        frame_timestamp = None

        async for data in super().receive():
            if not codec:
                try:
                    codec = av.CodecContext.create("aac", "r")
                    if self.codec_config:
                        extradata = binascii.unhexlify(self.codec_config)
                        codec.extradata = extradata
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

            aac_frames = extract_frames_from_au_packet(data.raw)
            for aac_frame_data in aac_frames:
                for frame in codec.decode(av.Packet(aac_frame_data)):
                    if frame_timestamp is None:
                        logger.warning("No timestamp available for the audio frame.")
                        continue
                    resampler = self._get_resampler(frame)
                    yield AudioFrame(frame, frame_timestamp, resampler)
            frame_timestamp = data.timestamp_unix_seconds

    @property
    def codec_config(self) -> str | None:
        """Get the AAC codec config from the SDP data."""
        if self._codec_config is None:
            try:
                attributes = self.reader.get_primary_media()["attributes"]
                self._codec_config = attributes["fmtp"]["config"]
            except (IndexError, KeyError) as err:
                raise SDPDataNotAvailableError(
                    f"SDP data is missing {err} field"
                ) from err

        return self._codec_config
