import machine
import network
import ntptime
import utime
import math
import neopixel

# numbers of leds in width and height
cols = 54
rows = 36

# number of leds
n = 180

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

off = (0, 0, 0, 0)
red = (255, 0, 0, 0)
orange = (255, 128, 0, 0)
yellow = (255, 255, 0, 0)
grass = (128, 255, 0, 0)
green = (0, 255, 0, 0)
mermaid = (0, 255, 128, 0)
cyan = (0, 255, 255, 0)
sky = (0, 128, 255, 0)
blue = (0, 0, 255, 0)
purple = (127, 0, 255, 0)
magenta = (255, 0, 255, 0)
rose = (255, 0, 127, 0)
white = (0, 0, 0, 255)

np = neopixel.NeoPixel(machine.Pin(12), n, bpp=4)


# ##############################################################################


def clamp(v, a, b):
    return max(min(v, b), a)


def interpolate_rgbw(a, b, t):
    return tuple([int(round(interpolate(x, y, t))) for x, y in zip(a, b)])


def interpolate(a, b, t):
    return a + clamp(t, 0., 1.) * (b - a)


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


def calc_solar_position(coords, date_time, debug=False):
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

    if debug:
        print('jd={}\tn={}\tL={}°'.format(jd, n, math.degrees(L)))
        print('g={}°\tA={}°\te={}°'.format(math.degrees(g), math.degrees(A), math.degrees(epsilon)))
        print('a={}°\td={}°'.format(math.degrees(alpha), math.degrees(delta)))
        print('t0={}\ttgh={}\tt={}°'.format(t_0, theta_g_h, math.degrees(theta)))
        print('a={}°\th={}°'.format(math.degrees(azim), math.degrees(elev)))

    return azim, elev


def intersect_azimuth_with_frame(azim):
    azim_math = northclockwise2math(azim)
    azim_vec = cross((0., 0., 1.), (math.cos(azim_math), math.sin(azim_math), 1.))
    result = get_border_intersections(width, height, azim_vec)
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


# ##############################################################################


def uni(color):
    np.fill(color)
    np.write()


def interpolate_side(cardinal, primary, secondary):
    set_area(cardinals[cardinal][0], cardinals[cardinal][1], primary, secondary)
    np.write()


def set_area(center, size, primary, secondary):
    half = size // 2
    start = center - half
    end = center + half + size % 2
    for i in range(start, end):
        d = 0 if size % 2 else 0.5
        t = math.fabs((center - i - d) / size)
        color = interpolate_rgbw(primary, secondary, t)
        np[i % n] = color


def paris_solaire():
    paris()
    solar((48.860536, 2.332237), utime.localtime())
    np.write()


# ##############################################################################


def paris():
    bg = (0, 0, 0, 5)
    river = (0, 10, 15, 0)
    np.fill(bg)
    set_area(1, 5, river, bg)
    set_area(65, 5, river, bg)
    set_area(142, 3, river, bg)


def sun(i):
    set_area(i, 7, (255, 127, 0, 0), (255, 50, 0, 0))


def moon(i):
    set_area(i, 7, (0, 0, 200, 0), (0, 0, 0, 10))


# ##############################################################################


def ramp_up():
    c = cardinals['south'][0]
    size = (cols + 2 * rows)
    d = (size + 1) % 2
    for i in range(size // 2):
        np[c - d - (i % n)] = (0, 1, 2, 3)
        np[c + (i % n)] = (0, 1, 2, 3)
        np.write()
        utime.sleep_ms(10)
    fade = 32
    for i in range(fade):
        color = interpolate_rgbw(off, (0, 10, 15, 20), i / fade)
        set_area(cardinals['north'][0], cols, color, off)
        np.write()
        utime.sleep_ms(1)
    utime.sleep_ms(50)


def solar(lat_long_deg, utc_time):
    azim, elev = calc_solar_position(lat_long_deg, utc_time)
    i = intersect_azimuth_with_frame(azim)
    if i is not None:
        sun(i) if elev > 0. else moon(i)


# ##############################################################################


if __name__ == '__main__':
    init()

    uni(off)
    ramp_up()
    paris_solaire()

    timer = machine.Timer(-1)  # virtual timer
    timer.init(period=60000, mode=machine.Timer.PERIODIC, callback=lambda t: paris_solaire())
