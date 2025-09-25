import binascii
import datetime
import logging
import ssl
from collections.abc import AsyncIterator, Iterator
from typing import Any, NamedTuple, cast
from urllib.parse import urlparse

import av
import numpy.typing as npt
from aiortsp.rtsp.connection import RTSPConnection
from aiortsp.rtsp.sdp import SDP

from .au_unit import extract_frames_from_au_packet
from .base import RTSPRawStreamer, SDPDataNotAvailableError

logger = logging.getLogger(__name__)


class AudioNotAvailableError(Exception):
    """Exception raised when SDP Audio data is not available.

    Could happen if the microphone is not enabled in the Companion App.
    """

    pass


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
        """Convert the audio frame to a resampled s16 NumPy array"""
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
        self._stream_available = True

    async def __aenter__(self) -> "RTSPAudioStreamer":
        reader = self.reader
        p_url = urlparse(reader.media_url)
        ssl_context = reader.ssl
        if p_url.scheme == "rtsps" and not ssl_context:
            ssl_context = ssl.create_default_context()
        port = p_url.port or (322 if p_url.scheme == "rtsps" else 554)

        try:
            async with RTSPConnection(
                host=p_url.hostname,
                port=port,
                username=p_url.username,
                password=p_url.password,
                logger=reader.logger,
                timeout=reader.timeout,
                ssl=ssl_context,
            ) as conn:
                resp = await conn.send_request(
                    "DESCRIBE",
                    url=reader.media_url,
                    headers={"Accept": "application/sdp"},
                )
                if resp.status != 200:
                    raise SDPDataNotAvailableError(  # noqa: TRY301
                        f"Failed to get SDP: {resp.status} {resp.msg}"
                    )
                sdp = SDP(resp.content)
                if not sdp.get("medias") or not any(
                    m.get("type") == "audio" for m in sdp.get("medias")
                ):
                    raise AudioNotAvailableError(f"No audio media found in SDP: {sdp}")  # noqa: TRY301
        except Exception:
            self._stream_available = False
            logger.warning(
                "RTSP audio stream not available.\n"
                "\n"
                "Check that the microphone is enabled in the Companion App."
            )
            return self

        await super().__aenter__()
        return self

    def _get_resampler(self, frame: av.AudioFrame) -> av.AudioResampler:
        """Create an AudioResampler needed for playback audio with SoundDevice.

        There is no fltp playback support in SoundDevice, so we need to resample
        to s16. We are creating the resampler on the first frame and reuse it for all
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
