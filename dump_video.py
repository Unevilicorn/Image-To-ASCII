from cv2 import cv2

file_name = "badapple"
file_ext = ".mp4"
output_dir = "video_dump"

vidcap = cv2.VideoCapture(file_name + file_ext)
success, image = vidcap.read()
count = 0
while success:
    cv2.imwrite(output_dir + "/" + str(count) + ".jpg", image)
    success, image = vidcap.read()
    print('Read a new frame: ' + str(count))
    count += 1
