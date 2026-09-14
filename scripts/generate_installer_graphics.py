"""
Generates high-resolution 24-bit BMP graphics for NSIS Modern UI 2.
- Welcome/Finish Page Bitmap: 164 x 314 px
- Header Bitmap: 150 x 57 px
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
ASSETS_DIR = PROJECT_ROOT / "assets"
BUILD_GRAPHICS_DIR = PROJECT_ROOT / "build" / "installer_graphics"
BUILD_GRAPHICS_DIR.mkdir(parents=True, exist_ok=True)

def create_welcome_bitmap(output_path: Path, edition: str = "pro"):
    # Size for NSIS MUI2 welcome page: 164 x 314
    width, height = 164, 314
    img = Image.new("RGB", (width, height), (11, 14, 20)) # Dark navy
    draw = ImageDraw.Draw(img)

    # Accent color
    is_pro = (edition == "pro")
    accent_color = (223, 186, 115) if is_pro else (73, 215, 197) # Gold or Teal
    accent_dim = (60, 50, 30) if is_pro else (20, 55, 50)
    bg_gradient_start = (14, 18, 28)
    bg_gradient_end = (8, 10, 15)

    # Vertical gradient background
    for y in range(height):
        r = int(bg_gradient_start[0] + (bg_gradient_end[0] - bg_gradient_start[0]) * (y / height))
        g = int(bg_gradient_start[1] + (bg_gradient_end[1] - bg_gradient_start[1]) * (y / height))
        b = int(bg_gradient_start[2] + (bg_gradient_end[2] - bg_gradient_start[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Decorative tech grid / lines
    for x in range(0, width, 16):
        draw.line([(x, 0), (x, height)], fill=(20, 25, 38), width=1)
    for y in range(0, height, 16):
        draw.line([(0, y), (width, y)], fill=(20, 25, 38), width=1)

    # Diagonal accent banner band
    draw.polygon([(0, 40), (width, 0), (width, 8), (0, 48)], fill=accent_dim)
    draw.polygon([(0, 44), (width, 4), (width, 6), (0, 46)], fill=accent_color)
    draw.polygon([(0, 270), (width, 230), (width, 234), (0, 274)], fill=accent_color)

    # Try to load Segoe UI or default font
    try:
        font_large = ImageFont.truetype("segoeuib.ttf", 20)
        font_sub = ImageFont.truetype("segoeui.ttf", 10)
        font_badge = ImageFont.truetype("segoeuib.ttf", 9)
        font_footer = ImageFont.truetype("segoeui.ttf", 8)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    # Load and composite icon if present
    icon_path = ASSETS_DIR / "calibra_icon.png"
    if icon_path.exists():
        try:
            icon_img = Image.open(icon_path).convert("RGBA").resize((56, 56), Image.Resampling.LANCZOS)
            img.paste(icon_img, (width // 2 - 28, 70), icon_img)
        except Exception:
            pass

    # Title & Subtitle
    draw.text((width // 2, 140), "CALIBRA 7", fill=(255, 255, 255), font=font_large, anchor="mm")
    draw.text((width // 2, 162), "METROLOGY WORKSTATION", fill=accent_color, font=font_sub, anchor="mm")

    # Edition Badge
    badge_text = "PROFESSIONAL EDITION" if is_pro else "COMMUNITY DEMO"
    draw.rounded_rectangle([(14, 185), (width - 14, 206)], radius=4, fill=accent_dim, outline=accent_color, width=1)
    draw.text((width // 2, 195), badge_text, fill=accent_color, font=font_badge, anchor="mm")

    # Specification points
    specs = ["ISO/IEC 17025", "ANSI Z540.3", "50-Digit Precision"] if is_pro else ["Evaluation Edition", "GUM Uncertainty", "Sample Datasets"]
    for i, sp in enumerate(specs):
        draw.text((22, 222 + (i * 14)), f"•  {sp}", fill=(180, 190, 205), font=font_sub)

    # Footer branding
    draw.text((width // 2, 298), "NOVYRAX TECHNOLOGIES", fill=(100, 115, 135), font=font_footer, anchor="mm")

    img.save(output_path, "BMP")
    print(f"Generated Welcome Bitmap: {output_path} ({width}x{height})")

def create_header_bitmap(output_path: Path):
    # Size for NSIS MUI2 header: 150 x 57
    width, height = 150, 57
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw logo or icon on the right
    icon_path = ASSETS_DIR / "calibra_icon.png"
    if icon_path.exists():
        try:
            icon_img = Image.open(icon_path).convert("RGBA").resize((44, 44), Image.Resampling.LANCZOS)
            img.paste(icon_img, (width - 50, 6), icon_img)
        except Exception:
            pass

    img.save(output_path, "BMP")
    print(f"Generated Header Bitmap: {output_path} ({width}x{height})")

if __name__ == "__main__":
    create_welcome_bitmap(BUILD_GRAPHICS_DIR / "welcome_pro.bmp", "pro")
    create_welcome_bitmap(BUILD_GRAPHICS_DIR / "welcome_demo.bmp", "demo")
    create_header_bitmap(BUILD_GRAPHICS_DIR / "header.bmp")
