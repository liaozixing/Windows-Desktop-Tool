import os
from PIL import Image

def convert_png_to_ico(png_path, ico_path):
    if not os.path.exists(png_path):
        print(f"Error: {png_path} does not exist.")
        return
    
    img = Image.open(png_path)
    # Ensure image is in RGBA mode to preserve transparency
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
        
    # Sizes common for Windows icons
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=sizes)
    print(f"Successfully converted {png_path} to {ico_path} with transparency support.")

if __name__ == "__main__":
    convert_png_to_ico("ico.png", "app.ico")
