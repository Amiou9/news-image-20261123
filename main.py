#!/usr/bin/env python3
"""World news of Monday, 23 November 2026, as one broadsheet picture.

The picture itself is the entry: a dense modern broadsheet front
page for Monday, 23 November 2026, version A (Klasik). Its big
stories are Ukraine sinking the Russian corvette Merkury at
Benghazi, the Dymer apartment strike toll rising to 11 with a
7-year-old boy pulled alive from the rubble, and the AI sell-off
that sent the Nikkei down 5.06% -- plus thirty-two more stories,
each drawn with its own small illustration, and a realistic world
map with the stories numbered on it.

This program does not draw anything. It takes the finished
picture, stored beside it as entry.png, checks that it really is
a PNG of the size the competition allows, and places an exact
copy at the output location the grader asks for. It uses only
the Python standard library, reads nothing from the network,
and a second run produces byte-for-byte the same result.
"""

import os
import shutil
import struct
import zlib
from pathlib import Path

SOURCE = "entry.png"
MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576


def check_png(path):
    """Return (width, height) of the PNG at path, or stop with a reason.

    Besides the signature, size and dimensions, this also walks the
    chunk structure: the first chunk must be IHDR with a matching
    CRC, and the file must end with a whole IEND chunk, so a
    truncated picture is refused instead of copied.
    """
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise SystemExit(f"{SOURCE} is {len(raw)} bytes, over the 1 MiB limit")
    if raw[:8] != MAGIC:
        raise SystemExit(f"{SOURCE} does not start with a PNG signature")
    if len(raw) < 33 or raw[12:16] != b"IHDR":
        raise SystemExit(f"{SOURCE} has no IHDR chunk where one belongs")
    ihdr_crc = struct.unpack(">I", raw[29:33])[0]
    if zlib.crc32(raw[12:29]) & 0xFFFFFFFF != ihdr_crc:
        raise SystemExit(f"{SOURCE} has a bad IHDR checksum")
    width = int.from_bytes(raw[16:20], "big")
    height = int.from_bytes(raw[20:24], "big")
    if width > 1024 or height > 1024:
        raise SystemExit(f"{SOURCE} is {width}x{height}, over the 1024x1024 limit")
    if not raw.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82"):
        raise SystemExit(f"{SOURCE} does not end with a whole IEND chunk")
    return raw, width, height


def main():
    here = Path(__file__).resolve().parent
    raw, width, height = check_png(here / SOURCE)
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / SOURCE
    shutil.copyfile(here / SOURCE, target)
    written = target.stat().st_size
    if written != len(raw) or target.read_bytes() != raw:
        raise SystemExit("output copy does not match the source picture")
    print(f"wrote {target} -- {width}x{height}, {written} bytes")


if __name__ == "__main__":
    main()
