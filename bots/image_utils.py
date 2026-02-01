"""Image processing utilities for bot"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Paths
IMAGES_DIR = Path(__file__).parent / "images"
FONTS_DIR = Path(__file__).parent / "fonts"
MAMONT_BASE_IMAGE = IMAGES_DIR / "mamont.jpg"

def create_mamont_image(mamont_name: str, mamont_id: str) -> BytesIO:
    """
    Create a mamont image with name overlay at position 790x110.
    
    Args:
        mamont_name: Name to display (first_name last_name or mamont_id)
        mamont_id: Mamont ID for filename uniqueness
    
    Returns:
        BytesIO: Image bytes ready for sending
    """
    
    if not MAMONT_BASE_IMAGE.exists():
        raise FileNotFoundError(f"Base mamont image not found: {MAMONT_BASE_IMAGE}")
    
    # Open base image
    with Image.open(MAMONT_BASE_IMAGE) as base_img:
        # Convert to RGB if needed
        if base_img.mode != 'RGB':
            base_img = base_img.convert('RGB')
        
        # Create a copy to work with
        img = base_img.copy()
        draw = ImageDraw.Draw(img)
        
        # Get image dimensions
        width, height = img.size
        
        # Try to load a font from fonts directory first, then fallback to system fonts
        font = None
        font_size = 150  # Increased font size
        
        try:
            # First try fonts from local fonts directory
            if FONTS_DIR.exists():
                font_files = list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.otf"))
                if font_files:
                    # Use the first available font file
                    font = ImageFont.truetype(str(font_files[0]), font_size)
                    print(f"Using local font: {font_files[0].name}")
            
            # If no local font found, try system fonts
            if font is None:
                if os.name == 'nt':  # Windows
                    font_paths = [
                        "C:/Windows/Fonts/arial.ttf",
                        "C:/Windows/Fonts/calibri.ttf",
                        "C:/Windows/Fonts/tahoma.ttf"
                    ]
                else:  # Linux/Mac
                    font_paths = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                        "/System/Library/Fonts/Arial.ttf"
                    ]
                
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, font_size)
                        print(f"Using system font: {font_path}")
                        break
            
            if font is None:
                font = ImageFont.load_default()
                print("Using default font")
        except Exception as e:
            print(f"Font loading error: {e}")
            font = ImageFont.load_default()
        
        # Convert full name to "Имя Ф." format for image display
        display_text = mamont_name
        if " " in mamont_name and not mamont_name.startswith("#"):
            # Split name and convert to "Имя Ф." format
            parts = mamont_name.split(" ", 1)  # Split only on first space
            if len(parts) == 2:
                first_name, last_name = parts
                display_text = f"{first_name} {last_name[0]}."
        
        # Text settings
        text_color = (255, 255, 255)  # White
        outline_color = (0, 0, 0)     # Black outline
        
        # Position text at coordinates 690x110 (moved 100px left from 790x110)
        text_x = 690
        text_y = 110
        
        # Ensure text doesn't go outside image bounds
        text_bbox = draw.textbbox((0, 0), display_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Adjust position if text would go outside image
        if text_x + text_width > width:
            text_x = width - text_width - 20  # 20px margin from right edge
        if text_y + text_height > height:
            text_y = height - text_height - 20  # 20px margin from bottom edge
        
        # Ensure minimum margins
        text_x = max(20, text_x)  # At least 20px from left edge
        text_y = max(20, text_y)  # At least 20px from top edge
        
        print(f"Text position: {text_x}x{text_y}, size: {text_width}x{text_height}, image: {width}x{height}")
        print(f"Original name: '{mamont_name}' -> Display text: '{display_text}'")
        
        # Draw text with outline for better visibility
        outline_width = 3  # Increased outline for larger text
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((text_x + dx, text_y + dy), display_text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((text_x, text_y), display_text, font=font, fill=text_color)
        
        # Save to BytesIO
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=95)
        img_bytes.seek(0)
        
        return img_bytes

def get_mamont_display_name(mamont: dict) -> str:
    """
    Get display name for mamont (full name for bot display).
    
    Args:
        mamont: Mamont data dict
        
    Returns:
        str: Display name (first_name last_name or mamont_id)
    """
    first_name = mamont.get('first_name', '').strip() if mamont.get('first_name') else ''
    last_name = mamont.get('last_name', '').strip() if mamont.get('last_name') else ''
    
    if first_name and last_name:
        # Return full name for bot display
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    else:
        return f"#{mamont['mamont_id']}"