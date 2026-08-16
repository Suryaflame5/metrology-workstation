"""
Automated Image Asset Generator for Microsoft Store Packaging.
Generates compliant PNG assets for Square150x150, Square44x44, StoreLogo, and Wide310x150.
"""

import os
import struct
import zlib

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "dist", "MetrologyWorkstation", "Assets")


def create_png(width: int, height: int, r: int, g: int, b: int) -> bytes:
    """Generate a valid raw uncompressed PNG image of given dimensions and solid background with center accent."""
    # PNG Signature
    png_sig = b"\x89PNG\r\n\x1a\n"

    # IHDR Chunk: width(4), height(4), bit_depth(1), color_type(1), compression(1), filter(1), interlace(1)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data)
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    # Raw pixel scanlines
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0) # Filter type 0 (None)
        for x in range(width):
            # Border or center mark
            if x < 4 or x >= width - 4 or y < 4 or y >= height - 4:
                raw_data.extend([15, 23, 42]) # Slate border
            elif abs(x - width//2) < width//4 and abs(y - height//2) < height//4:
                raw_data.extend([37, 99, 235]) # Metrology Blue #2563eb
            else:
                raw_data.extend([r, g, b])

    compressed = zlib.compress(bytes(raw_data))
    idat_crc = zlib.crc32(b"IDAT" + compressed)
    idat_chunk = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)

    # IEND Chunk
    iend_crc = zlib.crc32(b"IEND")
    iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    return png_sig + ihdr_chunk + idat_chunk + iend_chunk


def generate_store_assets():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    assets = {
        "StoreLogo.png": (50, 50),
        "Square44x44Logo.png": (44, 44),
        "Square150x150Logo.png": (150, 150),
        "Wide310x150Logo.png": (310, 150),
    }

    for name, (w, h) in assets.items():
        out_path = os.path.join(ASSETS_DIR, name)
        png_bytes = create_png(w, h, 30, 41, 59)
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        print(f" [OK] Generated asset {name} ({w}x{h} px, {len(png_bytes)} bytes)")


if __name__ == "__main__":
    generate_store_assets()
