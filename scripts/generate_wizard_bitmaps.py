"""
generate_wizard_bitmaps.py
Creates the two BMP images required by setup_calibra.iss:
  - assets/wizard_sidebar.bmp   164 x 314 px  (Inno Setup WizardImageFile)
  - assets/wizard_header.bmp     55 x  55 px  (Inno Setup WizardSmallImageFile)

Uses only stdlib (no Pillow) via ctypes GDI+ on Windows,
but falls back to a pure-Python PPM -> BMP writer if needed.

Run once before compiling the installer:
    python scripts/generate_wizard_bitmaps.py
"""

import struct
import os
from pathlib import Path

ASSETS = Path(__file__).parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)


# ─── Palette ──────────────────────────────────────────────────────────────────
NAVY       = (6,   9,  15)    # #06090F  body
GOLD       = (197, 168, 86)   # #C5A856  accent
GOLD_DARK  = (163, 134, 62)   # #A3863E
WHITE      = (255, 255, 255)
MUTED      = (100, 116, 139)  # slate-500
ACCENT_LT  = (212, 175, 92)   # lighter gold


# ─── BMP writer (no external deps) ───────────────────────────────────────────
def write_bmp(path: Path, pixels: list, width: int, height: int):
    """Write a 24-bit BMP file from a flat list of (R,G,B) tuples (top-to-bottom)."""
    row_size = (width * 3 + 3) & ~3   # padded to 4-byte boundary
    pixel_data_size = row_size * height
    file_size = 54 + pixel_data_size

    bmp_header = struct.pack(
        "<2sIHHI",
        b"BM",           # Signature
        file_size,       # File size
        0, 0,            # Reserved
        54               # Pixel data offset
    )
    dib_header = struct.pack(
        "<IiiHHIIiiII",
        40,              # DIB header size
        width, -height,  # Width, negative height = top-down
        1, 24,           # Color planes, bits per pixel
        0,               # No compression (BI_RGB)
        pixel_data_size,
        2835, 2835,      # 72 DPI
        0, 0             # Colors in palette, important colors
    )

    row_bytes = bytearray()
    for y in range(height):
        row = bytearray()
        for x in range(width):
            r, g, b = pixels[y * width + x]
            row += bytes([b, g, r])   # BMP stores BGR
        # Pad to 4-byte boundary
        row += bytes((-len(row)) % 4)
        row_bytes += row

    path.write_bytes(bmp_header + dib_header + bytes(row_bytes))
    print(f"  Written: {path}  ({width}x{height})")


# ─── Sidebar (164 x 314) ─────────────────────────────────────────────────────
def make_sidebar():
    W, H = 164, 314
    px = [NAVY] * (W * H)

    def set_px(x, y, color):
        if 0 <= x < W and 0 <= y < H:
            px[y * W + x] = color

    def h_line(y, x0, x1, color):
        for x in range(x0, x1 + 1):
            set_px(x, y, color)

    def v_line(x, y0, y1, color):
        for y in range(y0, y1 + 1):
            set_px(x, y, color)

    def fill_rect(x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                set_px(x, y, color)

    # ── Left gold accent bar (3px)
    for y in range(H):
        t = y / H
        r = int(GOLD[0] * (1 - t) + GOLD_DARK[0] * t)
        g = int(GOLD[1] * (1 - t) + GOLD_DARK[1] * t)
        b = int(GOLD[2] * (1 - t) + GOLD_DARK[2] * t)
        fill_rect(0, y, 2, y, (r, g, b))

    # ── Background gradient (subtle): navy -> slightly lighter navy
    for y in range(H):
        t = y / H
        r = int(NAVY[0] + 8 * (1 - t))
        g = int(NAVY[1] + 10 * (1 - t))
        b = int(NAVY[2] + 18 * (1 - t))
        for x in range(3, W):
            set_px(x, y, (r, g, b))

    # ── "CALIBRA" text — rendered as pixel blocks (bitmap font, uppercase)
    # Simple 5×7 pixel font for "CALIBRA"
    # Instead of a full font, we draw gold rectangles as stylized text blocks
    # Row 1: "CALIBRA" as a wide gold bar with letter shadows
    bar_y = 28
    fill_rect(16, bar_y, W - 16, bar_y + 18, (20, 25, 38))      # dark backing
    fill_rect(16, bar_y + 1, W - 16, bar_y + 2, GOLD)            # top gold line

    # "CALIBRA" label area — text we can't draw pixel-perfectly without a font renderer,
    # so we draw a stylised gold underline + spacer instead
    fill_rect(16, bar_y + 16, W - 16, bar_y + 17, GOLD)          # bottom gold line

    # ── Horizontal gold separator
    h_line(60, 16, W - 16, GOLD)
    h_line(61, 16, W - 16, GOLD_DARK)

    # ── "PROFESSIONAL EDITION" tag area — small rect
    fill_rect(22, 70, W - 22, 84, (20, 16, 8))                   # dark gold tint bg
    h_line(70, 22, W - 22, GOLD_DARK)
    h_line(84, 22, W - 22, GOLD_DARK)
    v_line(22, 70, 84, GOLD_DARK)
    v_line(W - 23, 70, 84, GOLD_DARK)

    # ── Precision grid pattern (subtle, lower 2/3 of sidebar)
    grid_start_y = 100
    grid_step    = 18
    grid_color   = (12, 18, 32)   # very slightly lighter than navy

    # Horizontal grid lines
    for gy in range(grid_start_y, H - 20, grid_step):
        h_line(gy, 12, W - 12, grid_color)

    # Vertical grid lines (sparse)
    for gx in range(12, W - 12, 30):
        v_line(gx, grid_start_y, H - 20, grid_color)

    # ── Gold crosshair/target symbol (centered, bottom third)
    cx, cy = W // 2, 210
    r = 20

    # Outer circle (approximated with diamond points)
    for angle_step in range(64):
        import math
        a = 2 * math.pi * angle_step / 64
        xi = cx + int(r * math.cos(a))
        yi = cy + int(r * math.sin(a))
        set_px(xi, yi, GOLD_DARK)

    # Inner circle
    ri = 10
    for angle_step in range(64):
        import math
        a = 2 * math.pi * angle_step / 64
        xi = cx + int(ri * math.cos(a))
        yi = cy + int(ri * math.sin(a))
        set_px(xi, yi, GOLD)

    # Crosshair lines
    h_line(cy, cx - r - 8, cx - ri - 2, GOLD)
    h_line(cy, cx + ri + 2, cx + r + 8, GOLD)
    v_line(cx, cy - r - 8, cy - ri - 2, GOLD)
    v_line(cx, cy + ri + 2, cy + r + 8, GOLD)

    # Center dot
    fill_rect(cx - 2, cy - 2, cx + 2, cy + 2, GOLD)

    # ── Bottom: "NOVYRAX" indicator dots (3 small gold squares)
    dy = H - 30
    for i in range(3):
        bx = W // 2 - 16 + i * 16
        fill_rect(bx, dy, bx + 6, dy + 6, GOLD_DARK if i != 1 else GOLD)

    # ── Bottom gold line
    h_line(H - 6, 0, W - 1, GOLD_DARK)
    h_line(H - 5, 0, W - 1, GOLD)

    write_bmp(ASSETS / "wizard_sidebar.bmp", px, W, H)


# ─── Header icon (55 x 55) ───────────────────────────────────────────────────
def make_header():
    import math
    W, H = 55, 55
    px = [NAVY] * (W * H)

    def set_px(x, y, color):
        if 0 <= x < W and 0 <= y < H:
            px[y * W + x] = color

    def fill_rect(x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                set_px(x, y, color)

    # Background
    for y in range(H):
        for x in range(W):
            set_px(x, y, NAVY)

    cx, cy = W // 2, H // 2

    # Outer ring
    r_outer = 23
    r_inner = 15
    for step in range(128):
        a = 2 * math.pi * step / 128
        xi = cx + int(r_outer * math.cos(a))
        yi = cy + int(r_outer * math.sin(a))
        set_px(xi, yi, GOLD_DARK)
        set_px(xi + 1, yi, GOLD_DARK)

    # Inner ring
    for step in range(128):
        a = 2 * math.pi * step / 128
        xi = cx + int(r_inner * math.cos(a))
        yi = cy + int(r_inner * math.sin(a))
        set_px(xi, yi, GOLD)

    # Crosshair
    for x in range(cx - r_outer - 2, cx + r_outer + 3):
        if abs(x - cx) > r_inner:
            set_px(x, cy, GOLD)
    for y in range(cy - r_outer - 2, cy + r_outer + 3):
        if abs(y - cy) > r_inner:
            set_px(cx, y, GOLD)

    # Center dot (3x3)
    fill_rect(cx - 2, cy - 2, cx + 2, cy + 2, GOLD)

    # Border
    for x in range(W):
        set_px(x, 0, GOLD_DARK)
        set_px(x, H - 1, GOLD_DARK)
    for y in range(H):
        set_px(0, y, GOLD_DARK)
        set_px(W - 1, y, GOLD_DARK)

    write_bmp(ASSETS / "wizard_header.bmp", px, W, H)


if __name__ == "__main__":
    print("Generating CALIBRA Pro wizard bitmap assets…")
    make_sidebar()
    make_header()
    print("Done. BMP files written to:", ASSETS)
