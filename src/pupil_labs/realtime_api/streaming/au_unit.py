import struct
from collections.abc import ByteString


def extract_frames_from_au_packet(rtp_payload: ByteString) -> list[ByteString]:
    """Extract one or more AAC frames from an RTP payload formatted as RFC3640.

    This function parses the Access Unit (AU) header section to determine the
    size of each AAC frame contained in the payload, and then extracts them.

    Args:
        rtp_payload: The raw RTP payload for an AAC stream, with the 12-byte
        RTP header already removed.

    Returns:
        A list of ByteStrings, where each element is a complete, raw AAC frame.
        Returns an empty list if the payload is malformed or empty.

    References:
        See RFC 3640 (https://www.ietf.org/rfc/rfc3640.txt) for detailed AAC
        payload format specifications.

    """
    if not rtp_payload or len(rtp_payload) < 2:
        return []

    try:
        # First 2 bytes contain the AU-headers-length in bits (big-endian).
        au_headers_length_bits = struct.unpack("!H", rtp_payload[:2])[0]
        au_headers_length_bytes = (au_headers_length_bits + 7) // 8

        # The actual AAC data starts after the 2-byte length field and the headers.
        data_start_offset = 2 + au_headers_length_bytes
        if len(rtp_payload) < data_start_offset:
            return []  # Malformed packet

        # The AU Header section contains the size information for each frame.
        # It's located right after the 2-byte length field.
        header_section = rtp_payload[2:data_start_offset]

        frame_sizes: list[int] = []
        # Each AU-header is 16 bits (2 bytes). The first 13 bits are the frame size.
        for i in range(0, au_headers_length_bytes, 2):
            au_header = struct.unpack("!H", header_section[i : i + 2])[0]
            # Right-shift by 3 to discard the 3-bit AU-index and get the frame size.
            frame_size = au_header >> 3
            frame_sizes.append(frame_size)

        # Extract each AAC frame from the data section using the collected sizes.
        frames: list[ByteString] = []
        current_offset = data_start_offset
        for size in frame_sizes:
            if current_offset + size > len(rtp_payload):
                break
            frame = rtp_payload[current_offset : current_offset + size]
            frames.append(frame)
            current_offset += size

    except (struct.error, IndexError):
        # Return an empty list if the packet is malformed and causes parsing errors.
        return []
    else:
        return frames
