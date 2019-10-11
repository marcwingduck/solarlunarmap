from machine import Pin, Timer
import utime
import math
import colors
from esp import neopixel_write
from common import sign, northclockwise2math
import solun

# number of leds
n = 180

# numbers of leds in width and height
cols = 54
rows = 36

# width and height of the frame in cm
width = 89.5
height = 60.5

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

# default colors (grb!!)
color_off = bytearray(4)
color_ambient = bytearray((0, 0, 0, 5))
color_river = bytearray((10, 0, 15, 0))

# current leds
leds_0 = bytearray(n * 4)

# leds to be faded to
leds_1 = bytearray(n * 4)

# update timer
timer = Timer(-1)

# neon clock utils
last_minute = 0
clock_color_1 = colors.random_choice()
clock_color_2 = colors.random_choice_2(clock_color_1)

# init neopixels
pin = Pin(12, Pin.OUT)
neopixel_write(pin, leds_0, True)


# ##############################################################################


def clamp(v, a, b):
    return max(min(v, b), a)


def interpolate(a, b, t):
    if t < 0. + 1e-3:
        return a
    if t > 1. - 1e-3:
        return b
    return a + t * (b - a)


def interpolate_rgbw(a, b, t):
    # return [int(round(interpolate(x, y, t))) for x, y in zip(a, b)], faster:
    c = []
    for i in range(4):
        c.append(int(interpolate(a[i], b[i], t)))
    return c


def cross(a, b):
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


# ##############################################################################


def intersect_angle_frame(angle):
    line = cross((0., 0., 1.), (math.cos(angle), math.sin(angle), 1.))
    result = get_border_intersections(width, height, line)
    if result:
        side, (x, y) = result

        # unwind to centimeters on the stripe
        cm = 0
        if side == 'south':
            cm = -x + width / 2.
        elif side == 'west':
            cm = width + y + height / 2.
        elif side == 'north':
            cm = width + height + x + width / 2.
        elif side == 'east':
            cm = 2 * width + height - y + height / 2.

        # get led at length (0.6 leds per cm)
        i = int(round(cm * 0.6 - 1))
        # return sanity clamped value
        return clamp(i, 0, n - 1)
    return None


def get_border_intersections(width, height, axis):
    side_map = {0: 'north', 1: 'east', 2: 'south', 3: 'west'}
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
        if math.fabs(s[2]) < 1e-3:  # lines are parallel
            continue
        if math.fabs(s[0]) < 1e-3 and math.fabs(s[1]) < 1e-3:  # lines are equal
            continue
        if s[2] > 0.:  # intersect on opposite side
            continue
        # normalize
        x, y = s[0] / s[2], s[1] / s[2]
        # check if intersection lies within the boundaries of the frame
        if -w2 - 1e-3 < x < w2 + 1e-3 and -h2 - 1e-3 < y < h2 + 1e-3:
            return side_map[i], (x, y)
    return None


# ##############################################################################


def fade_to(steps=10, sleep=1):
    if steps <= 1:
        neopixel_write(pin, leds_1, True)
        return
    for i in range(steps):
        t = (i + 1) / steps
        for j in range(n * 4):  # iterate all
            leds_0[j] = int(interpolate(leds_0[j], leds_1[j], t))
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(sleep)


# ##############################################################################


def off():
    global leds_0
    leds_0 = bytearray(n * 4)
    neopixel_write(pin, leds_0, True)


def set_area(center, size, primary, secondary, linear=False, direct=False):
    half = int(size / 2)
    start = center - half
    end = center + half + size % 2
    for i in range(start, end):
        d = 0. if size % 2 else 0.5
        x = center - i - d
        t = math.fabs((x - sign(x) * d) / (half - (size + 1) % 2))
        color = interpolate_rgbw(primary, secondary, t if linear else (t * t))
        index = i % n
        if direct:
            leds_0[index * 4:index * 4 + 4] = bytearray(color)
        else:
            leds_1[index * 4:index * 4 + 4] = bytearray(color)


# ##############################################################################


def ramp_up():
    center = cardinals['south'][0]
    size = (cols + 2 * rows)
    d = (size + 1) % 2
    ramp_color_1 = bytearray((0, 0, 0, 5))
    ramp_color_2 = bytearray((0, 0, 0, 20))

    off()

    set_area(center, cols // 3, ramp_color_2, color_off, False, True)
    neopixel_write(pin, leds_0, True)
    utime.sleep_ms(200)
    for i in range(size // 2):
        i1 = (center - d - (i % n)) * 4
        i2 = (center + (i % n)) * 4
        leds_0[i1:i1 + 4] = ramp_color_1
        leds_0[i2:i2 + 4] = ramp_color_1
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(10)
    for i in range(16):
        color = interpolate_rgbw(ramp_color_1, ramp_color_2, (i + 1) / 16)
        set_area(cardinals['north'][0], cols, color, ramp_color_1, False, True)
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(1)
    utime.sleep(1)
    fade_to()


# ##############################################################################


def set_sides(north, east, south, west):
    for i in range(*cardinals['north'][2]):
        leds_0[i * 4:i * 4 + 4] = bytearray(north)
    for i in range(*cardinals['east'][2]):
        leds_0[i * 4:i * 4 + 4] = bytearray(east)
    for i in range(*cardinals['south'][2]):
        leds_0[i * 4:i * 4 + 4] = bytearray(south)
    for i in range(*cardinals['west'][2]):
        leds_0[i * 4:i * 4 + 4] = bytearray(west)
    neopixel_write(pin, leds_0, True)


def neon_sides():
    set_sides((255, 0, 255, 0), (255, 255, 0, 0), (0, 255, 255, 0), (255, 0, 0, 0))


def bounce(cardinal, primary, secondary, tertiary, keep_lit=False, times=1):
    off()
    start, end = cardinals[cardinal][2]
    size = end - start
    for i in range(times * size):
        if not keep_lit:
            for j in range(size):
                index = (start + j) * 4
                leds_0[index:index + 4] = bytearray(primary)
        if (i // size) % 2 == 0:
            index = (start + i % size) * 4
            leds_0[index:index + 4] = bytearray(secondary)
        else:
            index = (end - 1 - (i % size)) * 4
            leds_0[index:index + 4] = bytearray(tertiary)
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(1)
    off()


def cycle_channels(brightness=255, n_cycles=1, timeout_ms=1):
    global leds_0
    for i in range(n * 4 * n_cycles):
        leds_0 = bytearray(n * 4)
        index = i % (n * 4)
        leds_0[index] = brightness
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(timeout_ms)
    off()


def cycle_color(color, n_cycles=1, timeout_ms=1):
    global leds_0
    for i in range(n * n_cycles):
        leds_0 = bytearray(n * 4)
        index = (i % n) * 4
        leds_0[index:index + 4] = bytearray(color)
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(timeout_ms)
    off()


# ##############################################################################


def sun(i, f=1.):
    g = int(interpolate(50, 180, f))
    set_area(i, 6, (g, 255, 0, 0), (50, 255, 0, 0))


def moon(i, f=1.):
    color = interpolate_rgbw((64, 64, 200, 0), (10, 10, 20, 100), f)
    set_area(i, 7, color, (0, 0, 0, 5))


def paris():
    global leds_1
    leds_1 = bytearray(n * [0, 0, 0, 5])

    set_area(1, 5, color_river, color_ambient)
    set_area(65, 5, color_river, color_ambient)
    set_area(142, 3, color_river, color_ambient)


def calc_solun_positions(lat_long_deg, utc_time):
    # moon
    lunar_azim, lunar_elev = solun.calc_lunar_position(lat_long_deg, utc_time)
    lunar_intersection = intersect_angle_frame(northclockwise2math(lunar_azim))
    if lunar_intersection is not None:
        if lunar_elev > 0.:
            f = clamp(math.degrees(lunar_elev), 0., 60.) / 60.
            moon(lunar_intersection, f)
    # sun
    solar_azim, solar_elev = solun.calc_solar_position(lat_long_deg, utc_time)
    solar_intersection = intersect_angle_frame(northclockwise2math(solar_azim))
    if solar_intersection is not None:
        if solar_elev > 0.:
            f = clamp(math.degrees(solar_elev), 0., 30.) / 30.
            sun(solar_intersection, f)


def paris_solun():
    paris()
    calc_solun_positions((48.860536, 2.332237), utime.localtime())
    fade_to(4)


def solun_demo():
    paris()
    fade_to()
    year, month, day, hour, minute, second, weekday, yearday = utime.localtime()
    for h in range(24):
        for m in range(0, 60, 10):
            paris()
            # solar/lunar
            calc_solun_positions((48.860536, 2.332237), (year, month, day, h, m, 0, weekday, yearday))
            # hour
            angle = (h % 12 + m / 60.) / 12. * 2. * math.pi
            index = intersect_angle_frame(northclockwise2math(angle))
            leds_1[index * 4:index * 4 + 4] = bytearray((158, 81, 188, 0))
            fade_to(2, 10)
    paris()
    fade_to()


# ##############################################################################


def clock(neon):
    global leds_0, leds_1, last_minute, clock_color_1, clock_color_2

    utc_offset = 2
    h, m, s = utime.localtime()[3:6]
    h = (h + utc_offset) % 24
    a_h = (h % 12 + m / 60.) / 12. * 2. * math.pi
    a_m = m / 60. * 2. * math.pi
    a_s = s / 60. * 2. * math.pi
    indices = [intersect_angle_frame(northclockwise2math(x)) for x in [a_h, a_m, a_s]]

    if neon:
        if last_minute != m:
            clock_color_1 = clock_color_2
            clock_color_2 = colors.random_choice_2(clock_color_1)
            last_minute = m

        start = cardinals['north'][0]
        progress = int(round(s / 60. * n))

        leds_0 = bytearray(n * list(clock_color_1))
        for i in range(start, start + progress):
            index = i % n
            leds_0[index * 4:index * 4 + 4] = clock_color_2

        for i in range((indices[1] - 1) % n, (indices[1] + 2) % n):
            for j in range(3):
                leds_0[i * 4 + j] = 255 - leds_0[i * 4 + j]
        for i in range((indices[0] - 2) % n, (indices[0] + 3) % n):
            for j in range(3):
                leds_0[i * 4 + j] = 255 - leds_0[i * 4 + j]

        neopixel_write(pin, leds_0, True)
    else:
        leds_0 = bytearray(n * list(color_ambient))
        set_area(indices[2], 5, bytearray((10, 0, 15, 63)), color_ambient, True, True)
        set_area(indices[1], 5, bytearray((10, 0, 15, 0)), color_ambient, True, True)
        set_area(indices[0], 7, bytearray((0, 0, 0, 128)), color_ambient, True, True)
        neopixel_write(pin, leds_0, True)


# ##############################################################################


def run_clock(neon=False):
    timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t: clock(neon))


def run_solun():
    paris_solun()
    timer.init(period=60000, mode=Timer.PERIODIC, callback=lambda t: paris_solun())


def stop_timer():
    timer.deinit()


# ##############################################################################


def run(is_online):
    paris()
    ramp_up()
    if is_online:
        run_solun()
