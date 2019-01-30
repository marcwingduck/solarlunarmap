import machine
import network
import ntptime
import utime
import math
import neopixel

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

# default colors
off = [0, 0, 0, 0]
ambient = [0, 0, 0, 5]
river = [0, 10, 15, 0]

# leds to fade to
leds = [off for x in range(n)]

# init neopixels
neo = neopixel.NeoPixel(machine.Pin(12), n, bpp=4)
neo.fill(off)
neo.write()


# ##############################################################################


def clamp(v, a, b):
    return max(min(v, b), a)


def interpolate(a, b, t):
    return a + clamp(t, 0., 1.) * (b - a)


def interpolate_rgbw(a, b, t):
    # too slow :/ return [int(round(interpolate(x, y, t))) for x, y in zip(a, b)]
    # faster:
    c = []
    for i in range(4):
        c.append(int(interpolate(a[i], b[i], t)))
    return c


def cross(a, b):
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def wrap_to_pi(a):
    return math.atan2(math.sin(a), math.cos(a))


def wrap_to_0_2pi(a):
    return math.atan2(math.sin(a - math.pi), math.cos(a - math.pi)) + math.pi


def northclockwise2math(a):
    # clockwise to counter clockwise
    a_pi = 2. * math.pi - a
    # add 90 deg offset from north to west
    a_pi = a_pi + math.pi / 2.
    # wrap to -pi,pi
    return wrap_to_pi(a_pi)


# ##############################################################################


def calc_solar_position(coords, date_time):
    """
    :param coords: in degrees
    :param date_time: tuple (year, month, day, hour, minute, second, weekday, yearday)
    :param debug: print variables if True
    :return: (azimuth, elevation) in degrees using north clockwise convention
    """

    # convert coords to radians
    rlat, rlong = math.radians(coords[0]), math.radians(coords[1])

    # unpack date time
    year, month, day, hour, minute, second, weekday, yearday = date_time

    # julian day
    jd = (1461 * (year + 4800 + (month - 14) // 12)) // 4 + (367 * (month - 2 - 12 * ((month - 14) // 12))) // 12 - (3 * ((year + 4900 + (month - 14) // 12) // 100)) // 4 + day - 32075

    # number of days since Jan 1st 2000, 12 UTC
    n = jd - 2451545.

    # mean ecliptical length
    L = math.radians(280.460) + math.radians(0.9856474) * n
    L = wrap_to_0_2pi(L)

    # mean anomaly
    g = math.radians(357.528) + math.radians(0.9856003) * n
    g = wrap_to_0_2pi(g)

    # ecliptical length
    A = L + math.radians(1.915) * math.sin(g) + math.radians(0.01997) * math.sin(2. * g)
    A = wrap_to_0_2pi(A)

    # ecliptic inclination
    epsilon = math.radians(23.439) - math.radians(0.0000004) * n
    epsilon = wrap_to_0_2pi(epsilon)

    # right ascension
    # alpha = math.atan2(epsilon, A)
    a1 = math.atan(math.cos(epsilon) * math.tan(A))
    a2 = math.atan(math.cos(epsilon) * math.tan(A)) + math.pi
    alpha = a1 if math.cos(A) > 0 else a2
    alpha = wrap_to_0_2pi(alpha)

    # declination
    delta = math.asin(math.sin(epsilon) * math.sin(A))
    delta = wrap_to_0_2pi(delta)

    # julian centery since 2000
    t_0 = n / 36525.

    # middle sidereal time in hours
    theta_g_h = 6.697376 + 2400.05134 * t_0 + 1.002738 * (hour + minute / 60.)
    theta_g_h = theta_g_h % 24

    # Greenwich hour angle at vernal equinox (Frühlingspunkt)
    theta_g = theta_g_h * math.radians(15.)
    theta = theta_g + rlong
    tau = theta - alpha

    # finally calculate azimuth and elecvation
    azim = math.atan2(math.sin(tau), (math.cos(tau) * math.sin(rlat) - math.tan(delta) * math.cos(rlat)))
    elev = math.asin(math.cos(delta) * math.cos(tau) * math.cos(rlat) + math.sin(delta) * math.sin(rlat))

    # move to north clockwise convention
    azim = wrap_to_pi(azim + math.pi)

    return azim, elev


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


def connect():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.active(True)
        wlan.connect('mywifi', 'mywifikey')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


def set_time():
    while True:
        try:
            ntptime.settime()
            break
        except OSError:
            utime.sleep_ms(10)
    print(utime.localtime())


def init():
    connect()
    set_time()


def apply(steps=10, sleep=1, pixels=None):
    for i in range(steps):
        t = (i + 1) / steps
        if pixels:
            for j in pixels:  # iterate set
                neo[j] = interpolate_rgbw(neo[j], leds[j], t)
        else:
            for j in range(n):  # iterate all
                neo[j] = interpolate_rgbw(neo[j], leds[j], t)
        neo.write()
        utime.sleep_ms(sleep)


# ##############################################################################


def uni(color):
    leds[:] = n * [color]


def interpolate_side(cardinal, primary, secondary):
    set_area(cardinals[cardinal][0], cardinals[cardinal][1], primary, secondary)


def set_area(center, size, primary, secondary, direct=False):
    changed_leds = set()
    half = size // 2
    start = center - half
    end = center + half + size % 2
    for i in range(start, end):
        d = 0 if size % 2 else 0.5
        t = math.fabs((center - i - d) / size)
        color = interpolate_rgbw(primary, secondary, t)
        if direct:
            neo[i % n] = color
        else:
            leds[i % n] = color
        changed_leds.add(i % n)
    return changed_leds


# ##############################################################################


def sun(i):
    set_area(i, 7, (255, 127, 0, 0), (255, 50, 0, 0))


def moon(i):
    set_area(i, 7, (0, 0, 200, 0), (0, 0, 0, 10))


def paris():
    uni(ambient)
    set_area(1, 5, river, ambient)
    set_area(65, 5, river, ambient)
    set_area(142, 3, river, ambient)


def solar(lat_long_deg, utc_time):
    azim, elev = calc_solar_position(lat_long_deg, utc_time)
    i = intersect_angle_frame(northclockwise2math(azim))
    if i is not None:
        sun(i) if elev > 0. else moon(i)


def clock():
    h, m, s = utime.localtime()[3:6]
    a_h = ((h + 1) % 12 + m / 60.) / 12. * 2 * math.pi
    a_m = m / 60. * 2 * math.pi
    a_s = s / 60. * 2 * math.pi
    indices = [intersect_angle_frame(northclockwise2math(x)) for x in [a_h, a_m, a_s]]

    neo.fill((0, 0, 0, 0))
    neo[indices[0]] = (0, 0, 0, 128)
    neo[indices[1]] = river
    neo[indices[2]] = ambient
    neo.write()


# ##############################################################################


def ramp_up():
    center = cardinals['south'][0]
    size = (cols + 2 * rows)
    d = (size + 1) % 2
    ramp_color_1 = [0, 1, 2, 3]
    ramp_color_2 = [0, 10, 15, 20]

    affected = set_area(center, 12, ramp_color_2, off)
    apply(6, 1, affected)
    for i in range(size // 2):
        neo[center - d - (i % n)] = ramp_color_1
        neo[center + (i % n)] = ramp_color_1
        neo.write()
        utime.sleep_ms(10)
    for i in range(16):
        color = interpolate_rgbw(off, ramp_color_2, (i + 1) / 16)
        set_area(cardinals['north'][0], cols, color, off, True)
        neo.write()
        utime.sleep_ms(1)
    utime.sleep(1)


def paris_solaire():
    paris()
    solar((48.860536, 2.332237), utime.localtime())
    apply()


def solar_demo():
    paris()
    apply()
    for i in range(24):
        for j in range(0, 60, 10):
            paris()
            solar((48.860536, 2.332237), (2019, 1, 27, i, j, 0, 6, 27))
            apply(3)
    paris()
    apply()


def time():
    for i in range(20):
        clock()
        utime.sleep(1)
    paris()
    apply()


# ##############################################################################


if __name__ == '__main__':
    init()
    ramp_up()
    paris()
    apply()
    paris_solaire()

    timer = machine.Timer(-1)
    timer.init(period=60000, mode=machine.Timer.PERIODIC, callback=lambda t: paris_solaire())
