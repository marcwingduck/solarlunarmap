import math


def clamp(v, a, b):
    return max(min(v, b), a)


def cross(a, b):
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def sign(value):
    return -1 if value < 0 else 1


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
