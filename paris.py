from machine import Pin, Timer
import utime
import math
from esp import neopixel_write

from common import *
import colors
import solun
import timing

# number of leds
n = 180

# numbers of leds in width and height
cols = 54
rows = 36

leds_per_cm = 0.6

coords = (48.860536, 2.332237)  # paris
# coords = (50.038333, 8.193611)  # home

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
last_minute = -1
last_second = -1
start_second = 0
clock_color_1 = colors.random_choice()
clock_color_2 = colors.random_choice_2(clock_color_1)
clock_old_hands = clock_color_2
clock_new_hands = clock_color_2

last_angle = 0
last_millis = 0

larson_bounds = (0, n)
larson_index = 0
larson_dir = 1
larson_last_dir = -1

# init neopixels
pin = Pin(13, Pin.OUT)
neopixel_write(pin, leds_0, True)


# ##############################################################################


def interpolate_rgbw(a, b, t):
    # return [int(round(interpolate(x, y, t))) for x, y in zip(a, b)], faster:
    c = []
    for i in range(4):
        c.append(int(interpolate(a[i], b[i], t)))
    return c


# ##############################################################################


def angle_to_unwind(angle):
    line = cross((0., 0., 1.), (math.cos(angle), math.sin(angle), 1.))
    result = get_border_intersections(width, height, line)
    if result:
        side, (x, y) = result
        # unwind to distance on the stripe
        dist = 0
        if side == 'south':
            dist = -x + width / 2.
        elif side == 'west':
            dist = width + y + height / 2.
        elif side == 'north':
            dist = width + height + x + width / 2.
        elif side == 'east':
            dist = 2 * width + height - y + height / 2.
        return dist, (x, y)
    return None


def intersect_angle_frame(angle, sub=False, norm=False):
    result = angle_to_unwind(angle)
    if result:
        distance, (x, y) = result
        n_leds = distance * leds_per_cm
        if not sub:
            n_leds = int(n_leds)  # round down (0,...,n-1)
        if norm:  # closest led is 1
            return n_leds, (min(height, width) / 2.) / math.sqrt(x*x+y*y)
        return n_leds  # flattened number of leds with fraction
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


def set_circular_background(color):
    global leds_1

    for i in range(n):
        intensity = get_distance_intensity(i)
        icolor = [int(intensity * c) for c in color]
        leds_1[i * 4:i * 4 + 4] = bytearray(icolor)

    fade_to()


def set_area(center, size, primary, secondary, linear=False, direct=False):
    half = int(size / 2)
    start = center - half
    end = center + half + size % 2
    d = 0. if size % 2 else 0.5
    for i in range(start, end):
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
    ramp_color_2 = bytearray((0, 0, 0, 50))
    ramp_color_3 = bytearray((0, 0, 0, 200))

    off()

    set_area(center, cols // 3, ramp_color_2, color_off, False, True)
    neopixel_write(pin, leds_0, True)
    utime.sleep_ms(200)
    for i in range(size // 2):
        i1 = (center - (i % n) - d) % n
        i2 = (center + (i % n)) % n
        leds_0[i1 * 4:i1 * 4 + 4] = ramp_color_1
        leds_0[i2 * 4:i2 * 4 + 4] = ramp_color_1
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(12)
    for i in range(16):
        color = interpolate_rgbw(ramp_color_1, ramp_color_3, (i + 1) / 16)
        set_area(cardinals['north'][0], cols, color, ramp_color_1, False, True)
        neopixel_write(pin, leds_0, True)
        utime.sleep_ms(1)
    utime.sleep(1)
    fade_to()


# ##############################################################################


def set_sides(north, east, south, west):
    for i in range(*cardinals['north'][2]):
        leds_1[i * 4:i * 4 + 4] = bytearray(north)
    for i in range(*cardinals['east'][2]):
        leds_1[i * 4:i * 4 + 4] = bytearray(east)
    for i in range(*cardinals['south'][2]):
        leds_1[i * 4:i * 4 + 4] = bytearray(south)
    for i in range(*cardinals['west'][2]):
        leds_1[i * 4:i * 4 + 4] = bytearray(west)
    fade_to()


def set_vertical(c1, c2):
    set_area(cols//2 + n//2, n//2, c1, c1)
    set_area(cols//2, n//2, c2, c2)
    fade_to()


def set_horizontal(c1, c2):
    set_area(cols+rows//2, n//2, c1, c1)
    set_area(cols+rows+cols+rows//2, n//2, c2, c2)
    fade_to()


def set_vertical_interp(c1, c2):
    set_area(cardinals['north'][0], cardinals['north'][1], c1, c1)
    set_area(cardinals['south'][0], cardinals['south'][1], c2, c2)
    for i in range(rows):
        color_linear = interpolate_rgbw(c1, c2, (i + 1) / rows)
        color = bytearray(color_linear)
        i_east = north_east + i
        i_west = north_west - i - 1
        leds_1[i_east * 4:i_east * 4 + 4] = color
        leds_1[i_west * 4:i_west * 4 + 4] = color
    fade_to()


def neon_sides():
    set_sides((255, 0, 255, 0), (255, 255, 0, 0), (0, 255, 255, 0), (255, 0, 0, 0))


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
    calc_solun_positions(coords, utime.localtime())
    fade_to(4)


def solun_demo():
    global leds_1
    paris()
    fade_to()
    year, month, day, hour, minute, second, weekday, yearday = utime.localtime()
    for h in range(24):
        for m in range(0, 60, 10):
            paris()
            # solar/lunar
            calc_solun_positions(coords, (year, month, day, h, m, 0, weekday, yearday))
            # hour
            angle = (h % 12 + m / 60.) / 12. * 2. * math.pi
            index = intersect_angle_frame(northclockwise2math(angle))
            leds_1[index * 4:index * 4 + 4] = bytearray((158, 81, 188, 0))
            neopixel_write(pin, leds_1, True)
    paris()
    fade_to()


# ##############################################################################


def spin(color):
    global leds_0, last_millis, last_angle

    tail = 24
    rps = 0.25

    now_millis = utime.ticks_ms()
    dt = (now_millis - last_millis) / 1000.
    last_millis = now_millis

    angle = wrap_to_0_2pi(last_angle + dt * rps * 2. * math.pi)
    fraction_led, intensity = intersect_angle_frame(northclockwise2math(angle), True, True)
    last_angle = angle

    frac, frac_led_index = math.modf(fraction_led)
    frac_led_index = int(frac_led_index)

    background = [0, 0, 0, 0]
    beam_color = [int(intensity * c) for c in color]

    leds_0 = bytearray(n * background)  # initialize color

    for i in range(tail):
        index = (frac_led_index - i) % n
        t = 1. - float(i) / tail
        fading = interpolate_rgbw([0, 0, 0, 0], beam_color, t)
        leds_0[index * 4:index * 4 + 4] = bytearray(fading)

    neopixel_write(pin, leds_0, True)


def larson_scanner(primary, secondary):
    global larson_index, larson_dir, larson_last_dir, leds_1

    size = 6

    leds_1 = bytearray(n * secondary)
    leds_1[larson_index * 4:larson_index * 4 + 4] = bytearray(primary)

    for i in range(size):
        b = larson_index + 1 + i
        a = larson_index - 1 - i
        t = float(i+1) / size
        fading = interpolate_rgbw(secondary, primary, 1-t)
        if larson_bounds[0] <= a and a < larson_bounds[1]:
            leds_1[a * 4:a * 4 + 4] = bytearray(fading)
        if larson_bounds[0] <= b and b < larson_bounds[1]:
            leds_1[b * 4:b * 4 + 4] = bytearray(fading)

    neopixel_write(pin, leds_1, True)

    larson_last_dir = larson_dir
    larson_index += larson_dir
    if larson_dir == 1 and larson_index == larson_bounds[1] - 1:
        larson_dir = -1
    elif larson_dir == -1 and larson_index == larson_bounds[0]:
        larson_dir = 1


def clock(neon, linear):
    global leds_0, last_minute, last_second, start_second, clock_new_hands, clock_old_hands, clock_color_1, clock_color_2

    utc_offset = 1
    h, m, s = utime.localtime()[3:6]
    h = (h + utc_offset) % 24
    a_h = (h % 12 + m / 60.) / 12. * 2. * math.pi

    h_i = intersect_angle_frame(northclockwise2math(a_h))

    if neon:
        if last_minute != m:  # switch color
            clock_old_hands = clock_color_1
            clock_new_hands = clock_color_2
            clock_color_1 = clock_color_2
            clock_color_2 = colors.random_choice_2(clock_color_1)
            last_minute = m
        if last_second != s:
            start_second = utime.ticks_ms()
            last_second = s

        seconds = s + clamp((utime.ticks_ms() - start_second) / 1000., 0.0, 1.0)
        minutes = (m + seconds / 60.) / 60. * 2. * math.pi
        m_i = intersect_angle_frame(northclockwise2math(minutes))  # 12 o'clock

        start = intersect_angle_frame(northclockwise2math(0))  # 12 o'clock

        frac_led_index = 0  # partially lit led index
        frac = 0.  # interpolation factor
        n_leds = 0  # number of seconds leds (from top to seconds hand)

        if linear:  # interpolate indices (linear velocity)
            fraction_led = seconds / 60. * n
            frac, frac_led_index = math.modf(fraction_led)
            n_leds = int(frac_led_index)
            frac_led_index = (start + n_leds) % n
        else:  # clock  hand (faster at edges)
            a_s = seconds / 60. * 2. * math.pi
            fraction_led = intersect_angle_frame(northclockwise2math(a_s), True)
            frac, frac_led_index = math.modf(fraction_led)
            frac_led_index = int(frac_led_index)
            n_leds = (frac_led_index - start) % n

        h_hand_range = range(h_i-4, h_i+4)
        m_hand_range = range(m_i-2, m_i+2)
        icolor = clock_color_1

        # fully lit seconds leds
        for i in range(start, start + n):
            a_i = i % n
            is_hand = a_i in h_hand_range or a_i in m_hand_range
            if i < start + n_leds:  # seconds passed
                icolor = clock_color_2 if not is_hand else clock_new_hands
            elif i > start + n_leds:  # seconds to be passed
                icolor = clock_color_1 if not is_hand else clock_old_hands
            elif is_hand:  # frac_led_index and hand (partially lit)
                icolor = interpolate_rgbw(clock_old_hands, clock_new_hands, frac)
            else:  # frac_led_index and not a hand (partially lit)
                icolor = interpolate_rgbw(clock_color_1, clock_color_2, frac)
            leds_0[a_i * 4:a_i * 4 + 4] = bytearray(icolor)
    else:
        a_m = m / 60. * 2. * math.pi
        a_s = s / 60. * 2. * math.pi

        m_i = intersect_angle_frame(northclockwise2math(a_m))
        s_i = intersect_angle_frame(northclockwise2math(a_s))

        leds_0 = bytearray(n * list(color_ambient))
        set_area(m_i, 5, bytearray((10, 0, 15, 0)), color_ambient, True, True)
        set_area(h_i, 7, bytearray((0, 0, 0, 128)), color_ambient, True, True)
        set_area(s_i, 5, bytearray((10, 0, 15, 63)), color_ambient, True, True)

    neopixel_write(pin, leds_0, True)


# ##############################################################################

def set_color(count, color):
    global leds_0
    count = clamp(count, 0, n)
    leds_0 = bytearray(count * color + (n - 1) * (0, 0, 0, 0))
    neopixel_write(pin, leds_0, True)


def fade_random():
    global leds_1
    leds_1 = bytearray(n * list(colors.random_choice()))
    fade_to(20)


# ##############################################################################


def run_random():
    timer.init(period=2000, mode=Timer.PERIODIC, callback=lambda t: fade_random())


def run_solun():
    paris_solun()
    timer.init(period=60000, mode=Timer.PERIODIC, callback=lambda t: paris_solun())


def run_clock(neon=False, linear=True):
    timing.update_time()
    s = utime.localtime()[5]  # seconds
    while True:  # wait for the next full second
        if utime.localtime()[5] != s:
            break
        utime.sleep_ms(10)
    dt = 50 if neon else 1000
    timer.init(period=dt, mode=Timer.PERIODIC, callback=lambda t: clock(neon, linear))


def run_spin(color):
    timer.init(period=50, mode=Timer.PERIODIC, callback=lambda t: spin(color))


def run_larson_scanner(cardinal, primary, secondary):
    global larson_bounds, larson_index, larson_dir, larson_last_dir
    larson_bounds = cardinals[cardinal][2]
    larson_index = larson_bounds[0]
    larson_dir = 1
    larson_last_dir = -1
    timer.init(period=30, mode=Timer.PERIODIC, callback=lambda t: larson_scanner(primary, secondary))


def stop_timer():
    timer.deinit()


# ##############################################################################


def run(is_online):
    paris()
    ramp_up()
    if is_online:
        run_solun()
    else:
        set_circular_background([111, 48, 115, 0])
