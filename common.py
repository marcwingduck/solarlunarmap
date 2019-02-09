import math


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
