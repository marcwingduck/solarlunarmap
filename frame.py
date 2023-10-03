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
