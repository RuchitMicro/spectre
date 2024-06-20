import os
from PIL import Image

def resize_images(input_folder, output_folder, max_width, max_height):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for root, dirs, files in os.walk(input_folder):
        # Create corresponding directories in the output folder
        relative_path = os.path.relpath(root, input_folder)
        output_dir = os.path.join(output_folder, relative_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for filename in files:
            if filename.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif')):
                input_file_path = os.path.join(root, filename)
                output_file_path = os.path.join(output_dir, filename)
                
                with Image.open(input_file_path) as img:
                    width, height = img.size
                    if width >= max_width or height >= max_height:
                        img.thumbnail((max_width, max_height))
                        img.save(output_file_path, quality=95)
                        print(f"Resized and saved {input_file_path} to {output_file_path}")
                    else:
                        print(f"Skipped {input_file_path}, already below threshold")

input_folder = './media'
output_folder = './media'
max_width = 1920
max_height = 1080

resize_images(input_folder, output_folder, max_width, max_height)
