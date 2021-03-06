import os
import sys
import numba
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageFont, ImageDraw, ImageFilter

FONT_DIR = "fonts/"
FONT_FILE = "UbuntuMono.ttf"
GLYPH_DIR = os.path.join(FONT_DIR, "png")
FULL_PATH = os.path.join(FONT_DIR, FONT_FILE)

FONTSIZE = 16


image_font = ImageFont.truetype(FULL_PATH, FONTSIZE)
(CHAR_WIDTH, CHAR_HEIGHT) = image_font.getsize("j")


@numba.jit(cache=True, nopython=True, nogil=True)
def loss_jit(a, b):
    out = []
    for i in range(a.shape[0]):
        loss = np.square((a[i] - b[i])).mean()
        out.append(loss)
    return np.array(out)


def extract_fonts():
    _glyphs = []
    _codes = []

    def get_char_codes():
        ttf = TTFont(FULL_PATH)
        chars = []
        for x in ttf["cmap"].tables:
            for (code, _) in x.cmap.items():
                chars.append(code)
        return chars

    def get_text_arr(char):
        canvas = Image.new('L', (CHAR_WIDTH, CHAR_HEIGHT), "black")
        draw = ImageDraw.Draw(canvas)
        draw.text((0, 0), char, 'white', image_font)
        return np.array(canvas)

    codes = get_char_codes()

    for i in range(0, 256):
        cchar = chr(i)
        if i in codes and cchar.isprintable():
            _glyphs.append(get_text_arr(cchar))
            _codes.append(i)

    _glyphs = np.ascontiguousarray(_glyphs)
    _codes = np.ascontiguousarray(_codes)

    return (_glyphs, _codes)


def image_to_tiles(path, scale):
    def get_image_outline():
        image = Image.open(path).convert('L')
        (w, h) = image.size
        image = image.filter(ImageFilter.FIND_EDGES)
        image = image.crop((1, 1, w - 1, h - 1))
        return image

    def resize_image(image, new_size):
        image = image.resize(new_size)
        return image

    def tile_image(image, hic, wic):
        new_shape = (hic, CHAR_HEIGHT, wic, CHAR_WIDTH)
        image_tiles = np.array(image).reshape(new_shape)
        image_tiles = image_tiles.swapaxes(1, 2)
        return image_tiles

    image = get_image_outline()
    (w, h) = image.size
    (wic, hic) = (round(w * scale / CHAR_WIDTH), round(h * scale / CHAR_HEIGHT))
    (nw, nh) = (wic * CHAR_WIDTH, hic * CHAR_HEIGHT)
    image = resize_image(image, (nw, nh))

    tiled_image = tile_image(image, hic, wic)

    return tiled_image


def create_ascii_image(glyphs, codes, image_tiles, output_path):
    im_size = image_tiles.shape
    nh = im_size[0] * im_size[2]
    nw = im_size[1] * im_size[3]

    code_len = len(codes)

    def create_string():
        sb = ""
        for i in range(im_size[0]):
            for j in range(im_size[1]):
                current_tiles = np.tile(image_tiles[i][j], (code_len, 1, 1))
                current_tiles = np.ascontiguousarray(current_tiles)
                scores = loss_jit(current_tiles, glyphs)
                best_index = np.argmin(scores)
                sb += chr(codes[best_index])
            sb += "\n"
        return sb

    def save_ascii_image(sb):
        canvas = Image.new('1', (nw, nh), "black")
        draw = ImageDraw.Draw(canvas)
        draw.text((0, 0), sb, 'white', image_font)
        canvas.save(output_path)
        return canvas

    sb = create_string()
    canvas = save_ascii_image(sb)
    return (sb, canvas)


def convert_image(input_path, output_path, scale):
    (glyphs, codes) = extract_fonts()
    image_tiles = image_to_tiles(input_path, scale)
    (sb, image) = create_ascii_image(glyphs, codes, image_tiles, output_path)
    return (sb, image)


if __name__ == "__main__":
    argv = sys.argv
    argc = len(argv)

    if(argc < 4):
        print("Usage: filename.py scale input_path, output_path")
        exit()

    scale = float(argv[1])
    input_path = argv[2]
    output_path = argv[3]

    convert_image(input_path, output_path, scale)
