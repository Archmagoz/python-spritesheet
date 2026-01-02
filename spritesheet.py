from PIL import Image
import numpy as np
import argparse
import sys
import os

# Terminal color codes
GREEN = '\033[92m'
RED = '\033[91m'
ENDC = '\033[0m'


# Custom ArgumentParser
class Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"{RED}Error: {message}{ENDC}\n\n")
        sys.exit(1)


def get_args():
    parser = Parser(
        description="Generate a single-row spritesheet from an irregular spritesheet image",
        epilog="Usage example:\n"
               "  spritesheet input.png output.png",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("input", help="input spritesheet image")
    parser.add_argument("output", help="output spritesheet image")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        parser.error(f"Input file '{args.input}' does not exist.")

    return args


def flood_fill(mask, visited, start_x, start_y):
    h, w = mask.shape
    stack = [(start_x, start_y)]

    minx = maxx = start_x
    miny = maxy = start_y

    while stack:
        x, y = stack.pop()

        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        if visited[y, x] or not mask[y, x]:
            continue

        visited[y, x] = True

        minx = min(minx, x)
        maxx = max(maxx, x)
        miny = min(miny, y)
        maxy = max(maxy, y)

        stack.extend([
            (x + 1, y), (x - 1, y),
            (x, y + 1), (x, y - 1)
        ])

    return (minx, miny, maxx + 1, maxy + 1)


def find_sprite_boxes(mask, min_area=50):
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    boxes = []

    for y in range(h):
        for x in range(w):
            if mask[y, x] and not visited[y, x]:
                box = flood_fill(mask, visited, x, y)
                minx, miny, maxx, maxy = box
                area = (maxx - minx) * (maxy - miny)

                if area >= min_area:
                    boxes.append(box)

    print(f"Found {len(boxes)} sprites")
    return sorted(boxes, key=lambda b: (b[1], b[0]))


def extract_frames(image, boxes):
    return [image.crop(box) for box in boxes]


def build_spritesheet(frames):
    max_w = max(f.width for f in frames)
    max_h = max(f.height for f in frames)

    columns = len(frames)
    sheet = Image.new("RGBA", (columns * max_w, max_h), (0, 0, 0, 0))

    for i, frame in enumerate(frames):
        x = i * max_w
        offset_x = (max_w - frame.width) // 2
        offset_y = max_h - frame.height

        sheet.paste(frame, (x + offset_x, offset_y))

    return sheet


def extract_sprites(input_file, output_file):
    img = Image.open(input_file).convert("RGBA")
    data = np.array(img)

    alpha = data[:, :, 3]
    mask = alpha > 0

    boxes = find_sprite_boxes(mask)
    frames = extract_frames(img, boxes)
    sheet = build_spritesheet(frames)

    sheet.save(output_file)
    print(f"{GREEN}Spritesheet generated successfully!{ENDC}")


if __name__ == "__main__":
    args = get_args()
    extract_sprites(args.input, args.output)
