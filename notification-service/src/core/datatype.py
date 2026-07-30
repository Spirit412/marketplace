import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Generate a time-sortable UUID version 7 (RFC 9562).

    Layout is 48 bits of big-endian Unix time in milliseconds, a 4-bit
    version field, 12 random bits, a 2-bit variant field, then 62 random
    bits. Because the timestamp occupies the most significant bytes, the
    values sort chronologically as both UUIDs and strings, which keeps
    B-tree index inserts append-mostly instead of scattering them.

    Returns:
        A UUID with version 7 and the RFC 4122 variant.
    """
    timestamp_ms = int(time.time() * 1000) & 0xFFFF_FFFF_FFFF
    data = bytearray(timestamp_ms.to_bytes(6, "big") + os.urandom(10))
    data[6] = 0x70 | (data[6] & 0x0F)
    data[8] = 0x80 | (data[8] & 0x3F)
    return uuid.UUID(bytes=bytes(data))
