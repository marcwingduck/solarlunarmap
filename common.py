import math


def clamp(v, a, b):
    return max(min(v, b), a)


def interpolate(a, b, t):
    if t < 0.01:
        return a
    if t > 0.99:
        return b
    return a + t * (b - a)


def cross(a, b):
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def sign(value):
    return -1 if value < 0 else 1


def wrap_to_pi(a):
    return math.atan2(math.sin(a), math.cos(a))


def wrap_to_0_2pi(a):
    return math.atan2(math.sin(a - math.pi), math.cos(a - math.pi)) + math.pi


def northclockwise2math(a):
    a_pi = 2. * math.pi - a  # clockwise to counter clockwise
    a_pi += math.pi / 2.  # add 90 deg offset from north to west
    return wrap_to_pi(a_pi)  # wrap to -pi,pi


def interpolate_rgbw(a, b, t):
    c = []
    for i in range(4):
        c.append(int(interpolate(a[i], b[i], t)))
    return c
