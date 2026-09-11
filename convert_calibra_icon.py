"""
Convert existing CALIBRA icon to .ico format for Windows application
"""

from PIL import Image
import os

def convert_calibra_icon():
    """Convert the existing calibra_icon.png to .ico format."""
    
    calibra_png = "assets/calibra_icon.png"
    
    if not os.path.exists(calibra_png):
        print(f"Error: {calibra_png} not found")
        return False
    
    try:
        img = Image.open(calibra_png)
        
        # Create different sizes for Windows icon
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as ICO with multiple sizes
        img.save("assets/calibra_icon.ico", format="ICO", sizes=sizes)
        
        print("✓ Successfully created calibra_icon.ico from existing CALIBRA image")
        print("  Icon sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256")
        return True
        
    except Exception as e:
        print(f"✗ Error converting icon: {e}")
        return False

if __name__ == "__main__":
    convert_calibra_icon()