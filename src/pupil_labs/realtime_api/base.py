import abc
import logging
from typing import TypeVar

from .models import APIPath, DiscoveredDeviceInfo

DeviceType = TypeVar("DeviceType", bound="DeviceBase")
"""
Type annotation for concrete sub-classes of :class:`DeviceBase
<pupil_labs.realtime_api.base.DeviceBase>`.
"""
T = TypeVar("T", bound="DeviceBase")


class DeviceBase(abc.ABC):  # noqa: B024
    """Abstract base class representing Realtime API host devices.

    This class provides the foundation for device implementations that connect
    to the Realtime API.

    Attributes:
        address (str): REST API server address.
        port (int): REST API server port.
        full_name (str | None): Full service discovery name.
        dns_name (str | None): REST API server DNS name, e.g.``neon.local / pi.local.``.

    """

    def __init__(
        self,
        address: str,
        port: int,
        full_name: str | None = None,
        dns_name: str | None = None,
        suppress_decoding_warnings: bool = True,
    ):
        """Initialize the DeviceBase instance.

        Args:
            address (str): REST API server address.
            port (int): REST API server port.
            full_name (str | None): Full service discovery name.
            dns_name (str | None): REST API server DNS name,
                e.g.``neon.local / pi.local.``.
            suppress_decoding_warnings: Whether to suppress libav decoding warnings.

        """
        self.address: str = address
        """REST API server address."""

        self.port: int = port
        """REST API server port."""

        self.full_name: str | None = full_name
        """Full service discovery name."""

        self.dns_name: str | None = dns_name
        """REST API server DNS name, e.g.``neon.local / pi.local.``."""

        if suppress_decoding_warnings:
            # suppress decoding warnings due to incomplete data transmissions
            logging.getLogger("libav.h264").setLevel(logging.CRITICAL)
            logging.getLogger("libav.swscaler").setLevel(logging.ERROR)

    def api_url(
        self, path: APIPath, protocol: str = "http", prefix: str = "/api"
    ) -> str:
        """Construct a full API URL for the given path.

        Args:
            path: API path to access.
            protocol: Protocol to use (http).
            prefix: API URL prefix.

        Returns:
            Complete URL for the API endpoint.

        """
        return path.full_address(
            self.address, self.port, protocol=protocol, prefix=prefix
        )

    def __repr__(self) -> str:
        """Get string representation of the device.

        Returns:
            String representation with address, port and DNS name.

        """
        return f"Device(ip={self.address}, port={self.port}, dns={self.dns_name})"

    @classmethod
    def from_discovered_device(
        cls: type[DeviceType], device: DiscoveredDeviceInfo
    ) -> DeviceType:
        """Create a device instance from discovery information.

        Args:
            device: Discovered device information.

        Returns:
            Device instance

        """
        return cls(
            device.addresses[0],
            device.port,
            full_name=device.name,
            dns_name=device.server,
        )

    @classmethod
    def convert_from(cls: type[DeviceType], other: T) -> DeviceType:
        """Convert another device instance to this type.

        Args:
            other: Device instance to convert.

        Returns:
            Converted device instance.

        """
        return cls(
            other.address,
            other.port,
            full_name=other.full_name,
            dns_name=other.dns_name,
        )
