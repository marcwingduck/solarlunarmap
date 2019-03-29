import utime
import random

colors = {
    'red': [255, 0, 0, 0],
    'orange': [255, 128, 0, 0],
    'yellow': [255, 255, 0, 0],
    'grass': [128, 255, 0, 0],
    'green': [0, 255, 0, 0],
    'mermaid': [0, 255, 128, 0],
    'cyan': [0, 255, 255, 0],
    'sky': [0, 128, 255, 0],
    'blue': [0, 0, 255, 0],
    'purple': [127, 0, 255, 0],
    'magenta': [255, 0, 255, 0],
    'rose': [255, 0, 127, 0]
}

# change rgba to grba format
for key in colors.keys():
    colors[key] = bytearray([colors[key][i] for i in [1, 0, 2, 3]])

h, m, s = utime.localtime()[3:6]
random.seed(int(str(h) + str(m) + str(s)))


def random_color():
    x = int(random.getrandbits(5) / (2 ** 5 - 1) * (len(colors) - 1))
    return list(colors.values())[x]


def random_color_2(color_1):
    color_2 = random_color()
    while color_2 == color_1:
        color_2 = random_color()
    return color_2


def complement(rgbw, keep_w=True):
    c = bytearray([255 - x for x in rgbw])
    if keep_w:
        c[3] = rgbw[3]
    return c
