import datetime
import logging
from collections.abc import AsyncIterator, ByteString
from typing import Any, NamedTuple, TypeAlias, cast

from aiortsp.rtcp.parser import SR, RTCPPacket
from aiortsp.rtsp.reader import RTSPReader

AiortspSR: TypeAlias = SR
AiortspRTCPPacket: TypeAlias = RTCPPacket
AiortspRTSPReader: TypeAlias = RTSPReader

logger = logging.getLogger(__name__)


class SDPDataNotAvailableError(Exception):
    """Exception raised when SDP data is not available or incomplete.

    This exception is raised when attempting to access SDP
    (Session Description Protocol) data that is not yet available or is missing required
    fields.
    """

    pass


class RTSPData(NamedTuple):
    """Container for RTSP data with timestamp information."""

    raw: ByteString
    """Raw binary data received from the RTSP stream."""
    timestamp_unix_seconds: float
    """Timestamp in seconds since the Unix epoch from RTCP SR packets."""

    @property
    def datetime(self) -> datetime.datetime:
        """Get the timestamp as a datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp_unix_seconds)

    @property
    def timestamp_unix_ns(self) -> int:
        """Get the timestamp in nanoseconds since the Unix epoch."""
        return int(self.timestamp_unix_seconds * 1e9)


async def receive_raw_rtsp_data(
    url: str, *args: Any, **kwargs: Any
) -> AsyncIterator[RTSPData]:
    """Receive raw data from an RTSP stream.

    This is a convenience function that creates an RTSPRawStreamer and yields
    timestamped data packets.

    Args:
        url: RTSP URL to connect to.
        *args: Additional positional arguments passed to RTSPRawStreamer.
        **kwargs: Additional keyword arguments passed to RTSPRawStreamer.

    Yields:
        RTSPData: Timestamped RTSP data packets.

    """
    async with RTSPRawStreamer(url, *args, **kwargs) as streamer:
        async for datum in streamer.receive():
            yield cast(RTSPData, datum)


class RTSPRawStreamer:
    """Stream raw data from an RTSP source.

    This class connects to an RTSP source and provides access to the raw data
    with timestamps synchronized to the device's clock.

    All constructor arguments are forwarded to the underlying
    [aiortsp.rtsp.reader.RTSPReader](https://github.com/marss/aiortsp/blob/master/aiortsp/rtsp/reader.py#L31-L32).
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._reader = _WallclockRTSPReader(*args, **kwargs)
        self._encoding = None

    async def receive(self) -> AsyncIterator[RTSPData]:
        """Receive raw data from the RTSP stream.

        This method yields RTSPData objects containing the raw data and
        corresponding timestamps.
        """
        async for pkt in self.reader.iter_packets():
            try:
                timestamp_seconds = self.reader.absolute_timestamp_from_packet(pkt)
            except _UnknownClockoffsetError:
                # The absolute timestamp is not known yet.
                # Waiting for the first RTCP SR packet...
                continue
            yield RTSPData(pkt.data, timestamp_seconds)

    @property
    def reader(self) -> "_WallclockRTSPReader":
        """Get the underlying RTSP reader."""
        return self._reader

    @property
    def encoding(self) -> str:
        """Get the encoding of the RTSP stream.

        Returns:
            str: The encoding name in lowercase.

        Raises:
            SDPDataNotAvailableError: If SDP data is missing or incomplete.

        """
        if self._encoding is None:
            try:
                rtpmap = self._reader.get_rtpmap()
                self._encoding = rtpmap["encoding"].lower()
            except (IndexError, KeyError) as err:
                raise SDPDataNotAvailableError(
                    f"SDP data is missing {err} field"
                ) from err
        return str(self._encoding)

    async def __aenter__(self, *args: Any, **kwargs: Any) -> "RTSPRawStreamer":
        """Enter the async context manager.

        Returns:
            RTSPRawStreamer: This instance.

        """
        await self.reader.__aenter__(*args, **kwargs)
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> Any:
        """Exit the async context manager."""
        return await self.reader.__aexit__(*args, **kwargs)


class _UnknownClockoffsetError(Exception):
    """Exception raised when the clock offset is not yet known.

    This internal exception is raised when attempting to get an absolute timestamp
    before receiving the first RTCP SR packet that provides the necessary clock
    synchronization information.
    """

    pass


class _WallclockRTSPReader(AiortspRTSPReader):
    """Extended RTSPReader that provides wallclock (absolute) timestamps.

    This class extends the standard RTSPReader to add functionality for converting
    relative RTP timestamps to absolute Unix epoch timestamps using RTCP SR packets.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._relative_to_ntp_clock_offset = None
        self._media_type = kwargs.get("media_type")

    def handle_rtcp(self, rtcp: Any) -> None:
        """Handle RTCP packets to extract clock synchronization information.

        This method processes RTCP packets, looking for SR (Sender Report) packets
        that contain the information needed to synchronize the RTP timestamps with
        the NTP clock.

        Args:
            rtcp: RTCP packet to handle.

        """
        for pkt in rtcp.packets:
            if isinstance(pkt, SR):
                self._calculate_clock_offset(pkt)

    def absolute_timestamp_from_packet(self, packet: Any) -> float:
        """Get the Unix epoch timestamp for the input packet

        Uses the cached clock offset between the NTP and relative timestamp provided
        by the RTCP packets.

        Args:
            packet: RTP packet.

        Returns:
            float: Absolute timestamp in seconds since the Unix epoch.

        Raises:
            _UnknownClockoffsetError: If the clock offset is not yet known.

        """
        if self._relative_to_ntp_clock_offset is None:
            raise _UnknownClockoffsetError(
                "Clock offset between relative and NTP clock is still unknown. "
                "Waiting for first RTCP SR packet..."
            )
        try:
            return (
                self.relative_timestamp_from_packet(packet)
                + self._relative_to_ntp_clock_offset
            )
        except TypeError:
            # self._relative_to_ntp_clock_offset is still None
            raise _UnknownClockoffsetError(
                "Clock offset between relative and NTP clock is still unknown. "
                "Waiting for first RTCP SR packet..."
            ) from None

    def relative_timestamp_from_packet(self, packet: Any) -> float:
        """Get the relative timestamp for an RTP packet.

        This method converts the RTP timestamp to seconds based on the media's
        clock rate.

        Args:
            packet: RTP packet.

        Returns:
            float: Relative timestamp in seconds.

        """
        rtpmap = self.get_rtpmap()
        clock_rate = rtpmap["clockRate"]
        return cast(float, packet.ts / clock_rate)

    def _calculate_clock_offset(self, sr_pkt: Any) -> None:
        """Calculate the offset between RTP and NTP clocks from an SR packet.

        This method calculates and stores the offset between the relative RTP
        timestamp and the NTP timestamp from a Sender Report packet.

        The NTP timestamp in SR packets is in seconds since 1900, but the aiortsp
        library converts it to seconds since 1970 (Unix epoch).

        Args:
            sr_pkt (aiortsp.rtcp.parser.SR):  packet which converts the raw NTP
                timestamp [1] from seconds since 1900 to seconds since 1970 (unix epoch)
                [1] see https://datatracker.ietf.org/doc/html/rfc3550#section-6.4.1

        """
        self._relative_to_ntp_clock_offset = (
            sr_pkt.ntp - self.relative_timestamp_from_packet(sr_pkt)
        )

    def get_rtpmap(self) -> dict[str, Any]:
        """Get the RTP map from the SDP data.

        Returns:
            dict: RTP map containing encoding and clock rate information.

        """
        media: dict[str, Any] = self.get_primary_media()
        return media["attributes"]["rtpmap"]  # type: ignore[no-any-return]

    def get_primary_media(self) -> Any:
        """Get the primary media description from the SDP data.

        This method returns the first media description of the specified type
        from the SDP data.

        Returns:
            dict: Media description.

        """
        if self.session is None:
            raise SDPDataNotAvailableError("RTSP session not initialized")
        if self.session.sdp is None:
            raise SDPDataNotAvailableError("SDP data not available in session")
        medias = self.session.sdp.get("medias")
        if not medias:
            raise SDPDataNotAvailableError("No 'medias' found in SDP data")

        for media in medias:
            if media and media.get("type") in ["video", "audio", "application"]:  # noqa: SIM102
                if self._media_type is None or media.get("type") == self._media_type:
                    return media

        raise SDPDataNotAvailableError(
            f"No suitable {self.media_type} media found in SDP"
        )
