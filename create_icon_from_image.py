"""
Convert the uploaded CALIBRA image to an .ico file for Windows application icon
"""

from PIL import Image
import os

def create_ico_from_image():
    """Convert PNG to ICO file for Windows application."""
    try:
        # Open the uploaded CALIBRA image
        img_path = "assets/calibra_icon.png"
        if not os.path.exists(img_path):
            print(f"Error: {img_path} not found. Please ensure the CALIBRA icon image is saved as assets/calibra_icon.png")
            return False
        
        img = Image.open(img_path)
        
        # Convert to ICO format (Windows requires specific icon format)
        # Resize to standard icon sizes
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save("assets/calibra_icon.ico", format="ICO", sizes=sizes)
        
        print("Successfully created calibra_icon.ico from uploaded image")
        return True
        
    except Exception as e:
        print(f"Error creating icon: {e}")
        return False

if __name__ == "__main__":
    create_ico_from_image()