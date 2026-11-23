#!/usr/bin/env python3
"""Monday 23 November 2026, in one picture.

The entry is the picture beside this program: entry.png, a
Klasik-style broadsheet front page summing up the world's news of
Monday, 23 November 2026. The leads are the sinking of the Russian
corvette Merkury off Benghazi, the Dymer strike toll reaching 11
with a boy of seven rescued alive, and the AI sell-off that cut
the Nikkei 5.06%. Thirty-two further stories, each with its own
drawn illustration, and a world map with every story numbered on
it, fill the rest of the page.

All this program does is hand that picture over. It reads the
file, walks its PNG chunks one by one to prove the picture is
whole, and writes an exact copy where the grader asks for it.
Only the standard library is used, nothing touches the network,
and running it twice writes the same bytes twice.
"""

import struct
import sys
import zlib
from pathlib import Path

ENTRY = "entry.png"
SIGNATURE = b"\x89PNG\r\n\x1a\n"
LIMIT = 1_048_576
WANTED_IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"


def fail(reason):
    sys.exit(f"{ENTRY}: {reason}")


def walk_chunks(data):
    """Yield (kind, body) for every chunk; refuse a broken file."""
    pos = 8
    seen_header = False
    seen_end = False
    while pos < len(data):
        if pos + 8 > len(data):
            fail("a chunk header is cut short")
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + size
        if end > len(data):
            fail(f"the {kind.decode('latin-1')} chunk runs past the end of the file")
        body = data[pos + 8:pos + 8 + size]
        stored = struct.unpack(">I", data[pos + 8 + size:end])[0]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != stored:
            fail(f"the {kind.decode('latin-1')} chunk fails its checksum")
        if not seen_header and kind != b"IHDR":
            fail("the first chunk is not IHDR")
        seen_header = True
        if kind == b"IEND":
            seen_end = True
            if end != len(data):
                fail("bytes follow the IEND chunk")
        yield kind, body
        pos = end
    if not seen_header or not seen_end:
        fail("the picture has no IHDR or no IEND chunk")


def measure(data):
    """Check the picture and return its width and height in pixels."""
    if len(data) > LIMIT:
        fail(f"is {len(data)} bytes, over the 1 MiB limit")
    if data[:8] != SIGNATURE:
        fail("does not start with a PNG signature")
    width = height = None
    for kind, body in walk_chunks(data):
        if kind == b"IHDR":
            width, height = struct.unpack(">II", body[:8])
    if width is None:
        fail("has no IHDR chunk")
    if width > 1024 or height > 1024:
        fail(f"is {width}x{height}, over the 1024x1024 limit")
    if not data.endswith(WANTED_IEND):
        fail("does not end with a whole IEND chunk")
    return width, height


def place_copy(source, data, width, height):
    import os

    folder = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / ENTRY
    target.write_bytes(data)
    again = target.read_bytes()
    if again != data:
        fail("the output copy does not match the source picture")
    print(f"wrote {target} -- {width}x{height}, {len(data)} bytes")


def run():
    here = Path(__file__).resolve().parent
    data = (here / ENTRY).read_bytes()
    width, height = measure(data)
    place_copy(here / ENTRY, data, width, height)


if __name__ == "__main__":
    run()
