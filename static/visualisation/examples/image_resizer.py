#!/usr/bin/env python3
import os
import argparse
from PIL import Image


def compress_and_resize_images(
    input_dir, output_dir, max_width=1920, max_height=1080, quality=85
):
    os.makedirs(output_dir, exist_ok=True)
    supported_ext = (".jpg", ".jpeg", ".png", ".webp")

    for root, _, files in os.walk(input_dir):
        for filename in files:
            if not filename.lower().endswith(supported_ext):
                continue

            input_path = os.path.join(root, filename)
            rel_path = os.path.relpath(root, input_dir)
            save_dir = os.path.join(output_dir, rel_path)
            os.makedirs(save_dir, exist_ok=True)
            output_path = os.path.join(save_dir, filename)

            try:
                img = Image.open(input_path)

                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                if max_width or max_height:
                    img.thumbnail((max_width or img.width, max_height or img.height))

                img.save(output_path, optimize=True, quality=quality)
                print(f"{filename} compressed -> {output_path}")
            except Exception as e:
                print(f"Skipping {filename}: {e}")

    print("Done compressing all images.")


def main():
    parser = argparse.ArgumentParser(
        description="Compress and optionally resize all images in a directory."
    )
    parser.add_argument("-i", "--input", required=True, help="Input directory path")
    parser.add_argument("-o", "--output", required=True, help="Output directory path")
    args = parser.parse_args()

    compress_and_resize_images(
        input_dir=args.input,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
