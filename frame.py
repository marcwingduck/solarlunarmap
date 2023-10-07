import math
from common import *

# numbers of leds in width and height
rows, cols = 36, 54
# rows, cols = 3, 4

# number of leds
n = 2*(cols+rows)

leds_per_cm = 0.6
led_offset_cm = (1./leds_per_cm)/2.
strip_length_cm = n / leds_per_cm

# width and height of the frame in meters
width = cols/leds_per_cm  # 90 cm
height = rows/leds_per_cm  # 60 cm

# led indices at intercardinal directions
south_east = 0
south_west = cols
north_west = cols + rows
north_east = 2 * cols + rows

# map from cardinal direction to tuple containing (center index, number of pixels, (start, end))
cardinals = {'north': ((north_east + north_west) // 2, cols, (north_west, north_east)),
             'east': ((north_east + n) // 2, rows, (north_east, n)),
             'south': ((south_west + south_east) // 2, cols, (south_east, south_west)),
             'west': ((south_west + north_west) // 2, rows, (south_west, north_west))}


def unwind_angle(angle):
    """
    Calculate the intersection of a vector with its origin
    at the center of the frame with the frame border and
    calculate the length in cm on the led strip.

    Parameters:
    ----------------
    angle : float
        angle in radians

    Returns:
    ----------------
    tuple : float, (float, float)
        distance in cm on strip and intersection coords
    """
    side_map = {0: 'north', 1: 'east', 2: 'south', 3: 'west'}

    axis = cross((0., 0., 1.), (math.cos(angle), math.sin(angle), 1.))

    w2, h2 = width / 2., height / 2.
    frame = [(-w2, h2, 1.),  # north west
             (w2, h2, 1.),  # north east
             (w2, -h2, 1.),  # south east
             (-w2, -h2, 1.)]  # south west

    for i in range(4):
        # build vecs for north, east, south, west
        line = cross(frame[i], frame[(i + 1) % 4])
        # intersect
        s = cross(axis, line)

        if math.fabs(s[2]) < 1e-3:
            # lines are parallel
            continue

        if math.fabs(s[0]) < 1e-3 and math.fabs(s[1]) < 1e-3:
            # lines are equal
            continue

        if s[2] > 0.:
            # intersect on opposite side
            continue

        # normalize
        x, y = s[0] / s[2], s[1] / s[2]

        # if intersection lies within the boundaries of the frame
        if -w2 - 1e-3 < x < w2 + 1e-3 and -h2 - 1e-3 < y < h2 + 1e-3:
            # unwind to distance on the strip
            dist = 0
            if side_map[i] == 'south':
                dist = -x + width / 2.
            elif side_map[i] == 'west':
                dist = width + y + height / 2.
            elif side_map[i] == 'north':
                dist = width + height + x + width / 2.
            elif side_map[i] == 'east':
                dist = 2 * width + height - y + height / 2.
            return dist, (x, y)

    return None


def get_distance_intensity(i):
    side = ''
    x = 0
    y = 0
    for e in cardinals:
        side_range = cardinals[e][2]
        if side_range[0] <= i and i < side_range[1]:
            side = e
            break
    if side == 'south':
        j = float(cols-i)
        x = j/cols * width - width/2.
        y = -height/2.
    if side == 'west':
        j = float(i-cols)
        x = -width/2.
        y = j/rows * height - height/2.
    if side == 'north':
        j = float(i-cols-rows)
        x = j/cols * width - width/2.
        y = height/2.
    if side == 'east':
        j = float(rows-(i-cols-rows-cols))
        x = width/2.
        y = j/cols * height - height/2.
    norm = math.sqrt(x*x+y*y)
    intensity = (height/2.) / norm
    return intensity


def sine(c, w, x):
    """
    Sine wave centered around c with frequency adjusted to be w/2
    """
    unit = w/2.
    y = math.sin(math.pi/unit * x + math.pi/2.-(c/unit)*math.pi)
    return (y+1.)/2.


def set_area2(center, size, primary, leds):
    """
    Parameters:
    ----------------
    center : float
        area center on the strip in cm
    size : float
        width of the area in cm
    primary : tuple
        primary color
    leds : array
        current led colors of the whole strip
        used for interpolation
    """
    # at least two leds to avoid flickering in motion
    size = max(2./leds_per_cm, size)
    i0 = int((center-size/2.) * leds_per_cm)  # not yet in area
    i1 = int((center+size/2.) * leds_per_cm)  # last one in area
    for i in range(i0+1, i1+1):
        w = i % n
        k = sine(center, size, i/leds_per_cm)
        current_color = leds[w*4:w*4+4]
        leds[w*4:w*4+4] = bytearray(interpolate_rgbw(current_color, primary, k))


if __name__ == '__main__':
    import numpy as np
    import matplotlib.pyplot as plt

    leds = bytearray(n*4)
    cm_on_strip = 12
    size = 1.0
    set_area2(cm_on_strip, size, 4*[64], leds)
    x = np.arange(0, 30, 1/leds_per_cm)
    x2 = np.arange(0, 30, 0.1)
    size = max(2./leds_per_cm, size)
    y = (1+np.sin(np.pi/(size/2.) * x2 + np.pi/2.-(cm_on_strip/(size/2.))*np.pi))*0.5  # unit > 2pi
    fig, ax = plt.subplots()
    ax.set_xticks(x)
    ax.set_xticklabels(['{}\n{}'.format(i, round(x[i], 2)) for i in range(len(x))])
    for l in [cm_on_strip-size/2., cm_on_strip, cm_on_strip+size/2.]:
        plt.axvline(l, color='red')
    ax.set_ylim([0, 1])
    ax.plot(x2, y)
    plt.show()
