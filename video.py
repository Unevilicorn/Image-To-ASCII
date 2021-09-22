from main import extract_fonts, image_to_tiles, create_ascii_image
import os
from natsort import natsorted
from multiprocessing import Process


thread_count = 8
start_num = 0

input_dir = "./video_dump/"
output_dir = "./ascii_dump/"

scale = 1
(glyphs, codes) = extract_fonts()

files = natsorted(os.listdir(input_dir))

files.remove(".gitignore")

file_count = len(files)


def main(thread_id):
    counter = start_num + thread_id
    while counter < file_count:
        filename = files[counter]
        input_path = input_dir + filename
        output_path = output_dir + os.path.splitext(filename)[0] + ".png"
        image_tiles = image_to_tiles(input_path, scale)
        create_ascii_image(glyphs, codes, image_tiles, output_path)

        counter += thread_count

        if(counter % 24 == thread_id):
            print(filename + " : " + str(thread_id))


if __name__ == '__main__':
    processes = []

    for i in range(thread_count):
        p = Process(target=main, args=(i,))
        p.start()
        processes.append(p)

    for i in range(thread_count):
        processes[i].join()
