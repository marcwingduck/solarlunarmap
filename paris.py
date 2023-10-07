from machine import Pin, Timer, bitstream
import utime
import math

from common import *
from frame import *
import timing
import colors
import solunar
import clock as clk

utc_offset = 2

# solunar
equinox_or_solstice = -1
coords = (48.860536, 2.332237)  # paris
# coords = (50.038333, 8.193611)  # home

# some colors matching the frame
color_off = bytearray(4)
color_ambient = bytearray((1, 0, 1, 8))
color_river = bytearray([int(0.06 * x) for x in colors.colors['river_blue']])
color_accent = bytearray([int(0.4 * x) for x in colors.colors['crimson']])

# global dimmer
dimmer = 0.5

# displayed led colors
leds0 = bytearray(n * 4)

# led colors to be faded to
leds1 = bytearray(n * 4)

# update timer
timer = Timer(-1)

# keep track if dynamic, timer-based mode is running or a static
static = True

# check if second changed to start counting millis
start_second = 0
last_second = -1
last_minute = -1

# spin globals
last_angle = 0
last_millis = 0

# larson scanner globals
larson_bounds = (0, n)
larson_index = 0
larson_dir = 1
larson_last_dir = -1

clock = clk.Clock()
clock.set_background_colors(color_ambient, color_river)
clock.set_hand_colors([26, 26, 0, 127], [60, 0, 40, 0], color_accent)


# ##############################################################################


def neopixel_write(pin, buffer):
    # low-level driving of a NeoPixel changed from esp.neopixel_write to machine.bitstream
    bitstream(pin, 0, (400, 850, 800, 450), buffer)


# init neopixels
pin = Pin(13, Pin.OUT)
neopixel_write(pin, leds0)


# ##############################################################################


def fade(steps=10, sleep=1):

    if steps <= 1:
        leds0[:] = leds1
        neopixel_write(pin, leds0)
        return

    for i in range(steps):
        t = (i + 1) / steps
        for j in range(n * 4):  # iterate all
            leds0[j] = int(interpolate(leds0[j], leds1[j], t))
        neopixel_write(pin, leds0)
        utime.sleep_ms(sleep)


def apply_dimmer(value):
    global dimmer
    dimmer = clamp(value, 0., 1.)

    # apply in static mode only
    if static:
        for i in range(n*4):
            leds0[i] = int(dimmer*leds1[i])
        neopixel_write(pin, leds0)


def off():
    leds1[:] = bytearray(n * 4)
    fade()


def paris(leds):
    leds[:] = bytearray(n * [0, 0, 0, 5])
    set_area2(1/leds_per_cm, 6, color_river, leds)
    set_area2(65/leds_per_cm, 10, color_river, leds)
    set_area2(143/leds_per_cm, 5, color_river, leds)


def set_circular_background(color):
    for i in range(n):
        intensity = get_distance_intensity(i)
        icolor = [int(intensity * c) for c in color]
        leds1[i * 4:i * 4 + 4] = bytearray(icolor)
    fade()


def set_area(center, size, primary, secondary, leds):
    if size == 1:
        leds[center * 4:center * 4 + 4] = bytearray(primary)
        return

    half = int(size / 2)
    start = center - half
    end = center + half + size % 2
    d = 0. if size % 2 else 0.5
    for i in range(start, end):
        x = center - i - d
        t = math.fabs((x - sign(x) * d) / (half - (size + 1) % 2))
        color = interpolate_rgbw(primary, secondary, t)
        index = i % n
        leds[index * 4:index * 4 + 4] = bytearray(color)


def set_sides(north, east, south, west, linear=False):
    # set_sides((10,0,0,0), (0,10,0,0), (0,0,10,0), (0,0,0,10), False)

    leds1[:] = bytearray(n*4)

    if linear:
        for i in range(*cardinals['north'][2]):
            leds1[i * 4:i * 4 + 4] = bytearray(north)
        for i in range(*cardinals['east'][2]):
            leds1[i * 4:i * 4 + 4] = bytearray(east)
        for i in range(*cardinals['south'][2]):
            leds1[i * 4:i * 4 + 4] = bytearray(south)
        for i in range(*cardinals['west'][2]):
            leds1[i * 4:i * 4 + 4] = bytearray(west)
    else:
        set_area2(cardinals['north'][0] / leds_per_cm, width, north, leds1)
        set_area2(cardinals['east'][0] / leds_per_cm, height, east, leds1)
        set_area2(cardinals['south'][0] / leds_per_cm, width, south, leds1)
        set_area2(cardinals['west'][0] / leds_per_cm, height, west, leds1)

    fade()


def set_vertical(c1, c2):
    set_area(cols//2 + n//2, n//2, c1, c1, leds1)
    set_area(cols//2, n//2, c2, c2, leds1)
    fade()


def set_horizontal(c1, c2):
    set_area(cols+rows//2, n//2, c1, c1, leds1)
    set_area(cols+rows+cols+rows//2, n//2, c2, c2, leds1)
    fade()


def set_vertical_interp(c1, c2):
    set_area(cardinals['north'][0], cardinals['north'][1], c1, c1, leds1)
    set_area(cardinals['south'][0], cardinals['south'][1], c2, c2, leds1)
    for i in range(rows):
        color_linear = interpolate_rgbw(c1, c2, (i + 1) / rows)
        color = bytearray(color_linear)
        i_east = north_east + i
        i_west = north_west - i - 1
        leds1[i_east * 4:i_east * 4 + 4] = color
        leds1[i_west * 4:i_west * 4 + 4] = color
    fade()


# ##############################################################################


def ramp_up():
    """
    Start animation.
    Draws into leds0 array so the next animation will fade from there to leds1.
    """

    center = cardinals['south'][0]
    size = (cols + 2 * rows)
    d = (size + 1) % 2
    ramp_color_1 = bytearray((0, 0, 0, 5))
    ramp_color_2 = bytearray((0, 0, 0, 50))
    ramp_color_3 = bytearray((0, 0, 0, 200))

    leds0[:] = bytearray(n*4)
    set_area2(center/leds_per_cm, width/3, ramp_color_2, leds0)
    neopixel_write(pin, leds0)

    utime.sleep_ms(200)

    for i in range(size // 2):
        i1 = (center - (i % n) - d) % n
        i2 = (center + (i % n)) % n
        leds0[i1 * 4:i1 * 4 + 4] = ramp_color_1
        leds0[i2 * 4:i2 * 4 + 4] = ramp_color_1
        neopixel_write(pin, leds0)
        utime.sleep_ms(12)
    for i in range(16):
        color = interpolate_rgbw(ramp_color_1, ramp_color_3, (i + 1) / 16)
        set_area2(cardinals['north'][0]/leds_per_cm, width, color, leds0)
        neopixel_write(pin, leds0)
        utime.sleep_ms(1)

    fade()


# ##############################################################################


def test_led(led_id, brightness=1, n_times=2, timeout_ms=300):
    for _ in range(n_times):
        for i in range(4):
            leds0[:] = bytearray(n * 4)
            index = (led_id*4) + i
            leds0[index] = brightness
            neopixel_write(pin, leds0)
            utime.sleep_ms(timeout_ms)
    off()


def cycle_channels(brightness=255, n_cycles=1, timeout_ms=100):
    for i in range(n * 4 * n_cycles):
        leds0[:] = bytearray(n * 4)
        index = i % (n * 4)
        leds0[index] = brightness
        neopixel_write(pin, leds0)
        utime.sleep_ms(timeout_ms)
    off()


def cycle_color(color, n_cycles=1, timeout_ms=100):
    for i in range(n * n_cycles):
        leds0[:] = bytearray(n * 4)
        index = (i % n) * 4
        leds0[index:index + 4] = bytearray(color)
        neopixel_write(pin, leds0)
        utime.sleep_ms(timeout_ms)
    off()


def cycle_circular(size=1):
    n_samples = 360
    color_1 = [0, 0, 0, 0]  # background color
    color_2 = [0, 164, 0, 0]  # pointer color
    for i in range(n_samples):
        angle = 2/3.*math.pi + i/n_samples * 3/4.*math.pi
        # angle = 2/3.*math.pi + i/n_samples * 2*math.pi
        cm_on_strip, (x, y) = unwind_angle(northclockwise2math(angle))
        fraction_led = cm_on_strip * leds_per_cm
        frac, frac_led_index = math.modf(fraction_led)
        frac_led_index = int(frac_led_index)
        for i in range(n):
            leds0[i*4:i*4+4] = bytearray(color_1)
        # leds0[:] = bytearray(n * list(color_ambient))
        # leds0[:] = bytearray(n * 4)
        id0 = frac_led_index * 4
        id1 = ((frac_led_index+1) % n) * 4

        # smooth
        # leds0[id0:id0+4] = bytearray((0, 0, 0, int((1-frac)*64)))
        # leds0[id1:id1+4] = bytearray((0, 0, 0, int(frac*64)))

        # blending in: not so super smooth, but ok
        # leds0[id0:id0+4] = bytearray(interpolate_rgbw(color_2, color_1, frac))
        # leds0[id1:id1+4] = bytearray(interpolate_rgbw(color_1, color_2, frac))
        set_area2(cm_on_strip, size, color_2, leds0)

        neopixel_write(pin, leds0)
        utime.sleep_ms(1)


# ##############################################################################


def draw_solunar_positions(lat_long_deg, utc_time, leds):
    # moon
    lunar_azim, lunar_elev = solunar.calc_lunar_position(lat_long_deg, utc_time)
    lunar_result = unwind_angle(northclockwise2math(lunar_azim))
    if lunar_result and lunar_elev > 0.:
        distance = lunar_result[0]
        f1 = clamp(math.degrees(lunar_elev), 0., 18.5) / 18.5
        f2 = clamp(math.degrees(lunar_elev), 0., 6.) / 6.
        color = interpolate_rgbw((10, 10, 20, 80), (64, 64, 200, 0), f1)
        set_area2(distance, 1 + f2 * 10, (0, 0, 0, 5), leds)
        set_area2(distance, 1 + f2 * 5, color, leds)
    # sun
    solar_azim, solar_elev = solunar.calc_solar_position(lat_long_deg, utc_time)
    solar_result = unwind_angle(northclockwise2math(solar_azim))
    if solar_result and solar_elev > 0.:
        distance = solar_result[0]
        f1 = clamp(math.degrees(solar_elev), 0., 23.45) / 23.45
        f2 = clamp(math.degrees(solar_elev), 0., 6.) / 6.
        g = int(interpolate(50, 180, f1))
        set_area2(distance, 1 + f2 * 14, (50, 255, 0, 0), leds)
        set_area2(distance, 1 + f2 * 7, (g, 255, 0, 0), leds)


def paris_solunar():
    paris(leds1)
    for i in range(equinox_or_solstice + 1):
        cardinal = list(cardinals.values())[i]
        set_area2(cardinal[0]/leds_per_cm, 5, color_accent, leds1)
    draw_solunar_positions(coords, utime.localtime(), leds1)
    fade(4)


def solunar_demo():
    paris(leds1)
    fade()
    year, month, day, hour, minute, second, weekday, yearday = utime.localtime()

    for h in range(24):
        for m in range(0, 60):
            # clear
            paris(leds0)

            # hour
            angle = (h % 12 + m / 60.) / 12. * 2. * math.pi
            distance = unwind_angle(northclockwise2math(angle))[0]
            set_area2(distance, 4, [158, 81, 188, 0], leds0)

            # solar/lunar
            draw_solunar_positions(coords, (year, month, day, h, m, 0, weekday, yearday), leds0)

            # apply
            neopixel_write(pin, leds0)

    paris(leds1)
    fade()


# ##############################################################################


def update_clock():
    global start_second, last_second
    h, m, s = utime.localtime()[3:6]
    h = (h + utc_offset) % 24
    if last_second != s:  # no milliseconds in utime, count manually
        start_second = utime.ticks_ms()
    last_second = s
    ms = int(clamp(utime.ticks_ms() - start_second, 0, 1000))

    if clock.update(h, m, s, ms, leds0):
        neopixel_write(pin, leds0)


# ##############################################################################


def spin(color, frequency):
    global last_millis, last_angle

    tail = 24

    now_millis = utime.ticks_ms()
    dt = (now_millis - last_millis) / 1000.
    last_millis = now_millis

    angle = wrap_to_0_2pi(last_angle + dt * frequency * 2. * math.pi)
    cm_on_strip, (x, y) = unwind_angle(northclockwise2math(angle))
    intensity = (min(height, width) / 2.) / math.sqrt(x*x+y*y)
    fraction_led = cm_on_strip * leds_per_cm
    last_angle = angle

    frac, frac_led_index = math.modf(fraction_led)
    frac_led_index = int(frac_led_index)

    background = [0, 0, 0, 0]
    beam_color = [int(intensity * c) for c in color]

    leds0[:] = bytearray(n * background)  # initialize color

    for i in range(tail):
        index = (frac_led_index - i) % n
        t = 1. - float(i) / tail
        fading = interpolate_rgbw(background, beam_color, t)
        leds0[index * 4:index * 4 + 4] = bytearray(fading)

    neopixel_write(pin, leds0)


def larson_scanner(primary, secondary):
    global larson_index, larson_dir, larson_last_dir

    size = 6

    leds1[:] = bytearray(n * secondary)
    leds1[larson_index * 4:larson_index * 4 + 4] = bytearray(primary)

    for i in range(size):
        b = larson_index + 1 + i
        a = larson_index - 1 - i
        t = float(i+1) / size
        fading = interpolate_rgbw(secondary, primary, 1-t)
        if larson_bounds[0] <= a and a < larson_bounds[1]:
            leds1[a * 4:a * 4 + 4] = bytearray(fading)
        if larson_bounds[0] <= b and b < larson_bounds[1]:
            leds1[b * 4:b * 4 + 4] = bytearray(fading)

    neopixel_write(pin, leds1)

    larson_last_dir = larson_dir
    larson_index += larson_dir
    if larson_dir == 1 and larson_index == larson_bounds[1] - 1:
        larson_dir = -1
    elif larson_dir == -1 and larson_index == larson_bounds[0]:
        larson_dir = 1


# ##############################################################################


def set_color(led_index, color, clear=False):
    led_index = clamp(led_index, 0, n-1)
    if clear:
        leds0[:] = bytearray(n * (0, 0, 0, 0))
    leds0[led_index*4:led_index*4+4] = bytearray(color)
    neopixel_write(pin, leds0)


def fade_random():
    leds1[:] = bytearray(n * list(colors.random_saturated()))
    fade(20)


# ##############################################################################


def run_random():
    global static

    static = False
    timer.init(period=5000, mode=Timer.PERIODIC, callback=lambda t: fade_random())


def run_solunar():
    global static, equinox_or_solstice

    # calculate once if today is equinox or solstice
    equinox_or_solstice = solunar.is_equinox_or_solstice(utime.localtime())

    paris_solunar()

    static = False
    timer.init(period=60000, mode=Timer.PERIODIC, callback=lambda t: paris_solunar())


def clock_demo():
    for h in range(24):
        for m in range(0, 60):
            for s in range(0, 60):
                for ms in range(0, 1000, 250):
                    clock.update(h, m, s, ms, leds0)
                    neopixel_write(pin, leds0)


def run_cls_clock(continuous=False):
    global static

    clock.update_params({'mode': 'cls', 'continuous': continuous})
    clock.set_background_colors(color_ambient, color_river)
    clock.set_hand_colors([26, 26, 0, 127], [60, 0, 40, 0], color_accent)

    timing.update_time()

    static = False
    timer.init(period=100, mode=Timer.PERIODIC, callback=lambda t: update_clock())


def run_neo_clock(start_at_minute=False, two_colors=False, ambient=False):
    global static, last_minute

    clock.update_params({'mode': 'neo',
                         'start_at_minute': start_at_minute,
                         'two_colors': two_colors,
                         'ambient': ambient})

    if ambient:
        clock.set_background_colors(color_ambient, color_river)
        clock.set_hand_colors([26, 26, 0, 127], [60, 0, 40, 0], color_accent)
    else:
        clock.set_background_colors(colors.colors['cyan'], colors.colors['orange'])

    timing.update_time()
    s = utime.localtime()[5]  # seconds
    while True:  # wait for the next full second
        if utime.localtime()[5] != s:
            last_minute = utime.localtime()[4]  # prevents color update on first neo draw
            break
        utime.sleep_ms(10)

    static = False
    timer.init(period=100, mode=Timer.PERIODIC, callback=lambda t: update_clock())


def run_spin(color, frequency=0.25):
    global static

    static = False
    timer.init(period=50, mode=Timer.PERIODIC, callback=lambda t: spin(color, frequency))


def run_larson_scanner(cardinal, primary, secondary):
    global static, larson_bounds, larson_index, larson_dir, larson_last_dir

    larson_bounds = cardinals[cardinal][2]
    larson_index = larson_bounds[0]
    larson_dir = 1
    larson_last_dir = -1

    n_leds = cardinals[cardinal][1]
    seconds = 2.
    dt = seconds / n_leds * 1000.

    static = False
    timer.init(period=int(round(dt)), mode=Timer.PERIODIC, callback=lambda t: larson_scanner(primary, secondary))


def stop_timer():
    global static
    leds0[:] = leds1  # copy currently displayed colors to start array for next fade

    static = True  # back to static mode
    timer.deinit()


# ##############################################################################


def run(is_online):
    paris(leds1)
    ramp_up()
    if is_online:
        run_solunar()
    else:
        set_sides((0, 0, 0, 0), (50, 50, 0, 80), (0, 0, 0, 0), (50, 50, 0, 80), False)
