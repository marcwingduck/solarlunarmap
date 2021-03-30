import utime
import random

colors = {
    'red': [255, 0, 0, 0],
    'orange': [255, 127, 0, 0],
    'yellow': [255, 255, 0, 0],
    'grass': [127, 255, 0, 0],
    'green': [0, 255, 0, 0],
    'mermaid': [0, 255, 127, 0],
    'cyan': [0, 255, 255, 0],
    'sky': [0, 127, 255, 0],
    'blue': [0, 0, 255, 0],
    'purple': [127, 0, 255, 0],
    'magenta': [255, 0, 255, 0],
    'rose': [255, 0, 127, 0]
}

# change rgba to grba format
for key in colors.keys():
    colors[key] = [colors[key][i] for i in [1, 0, 2, 3]]

gamma = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
         1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2,
         2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5,
         5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10,
         10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
         17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
         25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
         37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
         51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
         69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
         90, 92, 93, 95, 96, 98, 99, 101, 102, 104, 105, 107, 109, 110, 112, 114,
         115, 117, 119, 120, 122, 124, 126, 127, 129, 131, 133, 135, 137, 138, 140, 142,
         144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 167, 169, 171, 173, 175,
         177, 180, 182, 184, 186, 189, 191, 193, 196, 198, 200, 203, 205, 208, 210, 213,
         215, 218, 220, 223, 225, 228, 231, 233, 236, 239, 241, 244, 247, 249, 252, 255]


h, m, s = utime.localtime()[3:6]
random.seed(int(str(h) + str(m) + str(s)))


def random_choice():
    x = int(random.getrandbits(5) / (2 ** 5 - 1) * (len(colors) - 1))
    return list(colors.values())[x]


def random_choice_2(color_1):
    color_2 = random_choice()
    for i in range(3):  # make sure to terminate
        dist = sum([abs(a-b) for a, b in zip(color_1, color_2)])
        # i know this is very primitive and does not incorporate human color
        # perception but it prevents sequencing of colors that are too similar
        # (e.g. yellow/orange).
        if dist < 255+127:
            color_2 = random_choice()
    return color_2


def complement(rgbw, keep_w=True):
    c = bytearray([255 - x for x in rgbw])
    if keep_w:
        c[3] = rgbw[3]
    return c
