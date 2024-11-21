#                          The MIT License (MIT)
#
#                     Copyright (c) 2016 Nicco Kunzmann
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""The crc8 module.
The crc8 module provides the same interface as the hashlib module.
    https://docs.python.org/2/library/hashlib.html
Some code was copied from here:
    https://dzone.com/articles/crc8py
and gave credit "From the PyPy project" and the link
    http://snippets.dzone.com/posts/show/3543
"""
import sys
from typing import Union

__author__="Nicco Kunzmann"
__version__="0.0.4"

PY2 = sys.version_info[0] == 2


class crc:

    digest_size = 1
    block_size  = 1

    _table = [	0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15,
                0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d,
                0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
                0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d,
                0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5,
                0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
                0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85,
                0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,
                0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
                0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea,
                0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2,
                0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
                0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32,
                0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a,
                0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
                0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a,
                0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c,
                0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
                0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec,
                0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4,
                0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
                0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44,
                0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c,
                0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
                0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b,
                0x76, 0x71, 0x78, 0x7f, 0x6a, 0x6d, 0x64, 0x63,
                0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
                0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13,
                0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb,
                0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
                0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb,
                0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3]

    def __init__(self, initial_string: Union[bytes, bytearray, str] = b'') -> None:
        """Create a new crc8 hash instance."""
        self._sum = 0x00
        if isinstance(initial_string, str):
            initial_string = initial_string.encode('utf-8')
        self._update(initial_string)

    def update(self, bytes_: Union[bytes, bytearray, str]) -> None:
        """Update the hash object with the bytes-like object.

        Args:
            bytes_: The bytes-like object to update the hash with.

        Raises:
            TypeError: If the input is not a bytes-like object or string
        """
        if isinstance(bytes_, str):
            bytes_ = bytes_.encode('utf-8')
        self._update(bytes_)

    def digest(self) -> bytes:
        """Return the digest of the bytes passed to the update() method.

        Returns:
            bytes: A bytes object of digest_size bytes (1 byte for crc8)
        """
        return bytes([self._sum])

    def hexdigest(self) -> str:
        """Return digest as hexadecimal string.

        Returns:
            str: A string of hexadecimal digits
        """
        return hex(self._sum)[2:].zfill(2)

    def _update(self, bytes_: Union[bytes, bytearray]) -> None:
        """Internal update method.

        Args:
            bytes_: Bytes-like object to process

        Raises:
            TypeError: If input is not a bytes-like object
        """
        if not isinstance(bytes_, (bytes, bytearray)):
            raise TypeError("object supporting the buffer API required")

        table = self._table
        _sum = self._sum
        for byte in bytes_:
            _sum = table[_sum ^ byte]
        self._sum = _sum

    def copy(self) -> 'crc':
        """Return a copy ("clone") of the hash object.

        This can be used to efficiently compute the digests of byte strings that
        share a common initial substring.

        Returns:
            crc: A new crc object with the same state
        """
        new = crc()
        new._sum = self._sum
        return new


# Backwards compatibility
class crc8(crc):
    """Backwards compatibility class name"""
    pass


__all__ = ['crc', 'crc8']
