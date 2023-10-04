import utime
import random

saturated_rgb = {
    'red': 'ff0000',
    'orange': 'ff8800',
    'yellow': 'ffff00',
    'grass': '88ff00',
    'green': '00ff00',
    'mermaid': '00ff88',
    'cyan': '00ffff',
    'sky': '0088ff',
    'blue': '0000ff',
    'purple': '8800ff',
    'magenta': 'ff00ff',
    'rose': 'ff0088'
}


accents_rgb = {
    'river_blue': '00aaff',  # colors that go well with this below
    'giants_orange': 'ff8811',
    'fuchsia': 'f100fe',
    'coral_pink': 'fe938c',
    'coral': 'ff5619',
    'yellow': 'ffcc919',
    'bright_pink': 'F7567C',
    'plum': '9c528b',
    'plum_web': 'ec91d8',
    'rose_bonbon': 'ff499e',
    'dark_pastel_green': '4cb944',
    'crimson': 'd72638'
}


def hex2grb0(h):
    h = h.lstrip('#')
    x = [int(h[i:i+2], 16) for i in (2, 0, 4)]
    x.append(0)
    return x


# create color map

colors = {}

for key in saturated_rgb.keys():
    colors[key] = hex2grb0(saturated_rgb[key])

for key in accents_rgb.keys():
    colors[key] = hex2grb0(accents_rgb[key])

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
    for _ in range(3):  # make sure to terminate
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
