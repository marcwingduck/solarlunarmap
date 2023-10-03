# equations and tables from
# - https://www.aa.quae.nl/en/reken.html
# - Jean Meeus, Astronomical Algorithms, Second Edition, 1998

import math
from common import wrap_to_pi, wrap_to_0_2pi

epsilon = math.radians(23.4393)  # obliquity of the ecliptic (tilt of the earth's axis of rotation)

table_27c = [[485, 324.96, 1934.136],
             [203, 337.23, 32964.467],
             [199, 342.08, 20.186],
             [182, 27.85, 445267.112],
             [156, 73.14, 45036.886],
             [136, 171.52, 22518.443],
             [77, 222.54, 65928.934],
             [74, 296.72, 3034.906],
             [70, 243.58, 9037.513],
             [58, 119.81, 33718.147],
             [52, 297.17, 150.678],
             [50, 21.02, 2281.226],
             [45, 247.54, 29929.562],
             [44, 325.15, 31555.956],
             [29, 60.93, 4443.417],
             [18, 155.12, 67555.328],
             [17, 288.79, 4562.452],
             [16, 198.04, 62894.029],
             [14, 199.76, 31436.921],
             [12, 95.39, 14577.848],
             [12, 287.11, 31931.756],
             [12, 320.81, 34777.259],
             [9, 227.73, 1222.114],
             [8, 15.45, 16859.074]]


equinox_solstices = [[2451623.80984, 365242.37404,  0.05169, -0.00411, -0.00057],  # Mar equinox  (beginning of astronomical spring)
                     [2451716.56767, 365241.62603,  0.00325, 0.00888, -0.00030],   # Jun solstice (beginning of astronomical summer)
                     [2451810.21715, 365242.01767, -0.11575, 0.00337, 0.00078],    # Sep equinox  (beginning of astronomical autumn)
                     [2451900.05952, 365242.74049, -0.06223, -0.00823, 0.00032]]   # Dec solstice (beginning of astronomical winter)


def is_equinox_or_solstice(date_time):
    year, month, day, hour, minute, second, weekday, yearday = date_time
    julian_day_number = calc_julian_date(year, month, day, hour, minute, second)

    Y = (year-2000)/1000
    Y2 = Y*Y
    Y3 = Y*Y2
    Y4 = Y*Y3

    for i, (a, b, c, d, e) in enumerate(equinox_solstices):
        JDE0 = a+b*Y+c*Y2+d*Y3+e*Y4
        JDE = calc_equinox_solstice(JDE0)
        n = JDE - 2451545.
        if math.floor(n) == math.floor(julian_day_number):
            return i

    return -1


def calc_equinox_solstice(JDE0):
    T = (JDE0-2451545.0)/36525.0
    W = 35999.373 * T - 2.47
    W_rad = math.radians(W)
    delta_lambda = 1 + 0.00334 * math.cos(W_rad) + 0.0007 * math.cos(2*W_rad)

    S = 0.
    for row in table_27c:
        A, B, C = row
        S += A * math.cos(math.radians(B + C * T))

    JDE = JDE0 + (0.00001*S)/delta_lambda

    return JDE


def calc_julian_date(year, month, day, hour=0, minute=0, second=0):
    day += hour/24. + minute/1440. + second/86400.
    if month <= 2:
        month += 12
        year -= 1
    a = year//100
    b = a//4
    c = 2 - a + b
    e = math.floor(365.25 * (year + 4716))
    f = math.floor(30.6001 * (month + 1))

    # too large for micropython's poor floating precision; hotfix below
    # julian day
    # jd = c + day + e + f - 1524.5
    # number of days since Greenwich noon, Terrestrial Time, on 1 January 2000
    # n = jd - 2451545.
    # julian centuries since 2000
    # t = n / 36525.

    # hotfix
    # int
    jd_ = c + e + f
    n_ = jd_ - 2451545
    # float
    n_ -= 1524.5
    n_ += day
    return n_


def get_sidereal_time(d, long):
    # local sidereal time
    theta0 = math.radians(280.16 + 360.9856235 * d)
    theta = wrap_to_0_2pi(theta0 + long)  # long: eastern positive, western negative
    return theta


def calc_azim_elev(lat, ha, delta):
    # finally calculate azimuth and elevation
    azim = math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat) - math.tan(delta) * math.cos(lat))
    elev = math.asin(math.cos(delta) * math.cos(ha) * math.cos(lat) + math.sin(delta) * math.sin(lat))
    # move to north clockwise convention
    azim = wrap_to_pi(azim + math.pi)
    return azim, elev


def calc_lunar_position(coords, date_time):
    # convert coords to radians
    rlat, rlong = math.radians(coords[0]), math.radians(coords[1])
    # unpack date time
    year, month, day, hour, minute, second, weekday, yearday = date_time
    # julian date, number of days since Jan 1st 2000, 12 UTC, julian centuries since 2000
    d = calc_julian_date(year, month, day, hour, minute, second)

    # geocentric ecliptic longitude
    L = math.radians(218.316) + math.radians(13.176396) * d
    L = wrap_to_0_2pi(L)

    # mean anomaly
    M = math.radians(134.963) + math.radians(13.064993) * d
    M = wrap_to_0_2pi(M)

    # mean distance
    F = math.radians(93.272) + math.radians(13.229350) * d
    F = wrap_to_0_2pi(F)

    # geocentric ecliptic longitude
    lmda = L + math.radians(6.289) * math.sin(M)
    lmda = wrap_to_0_2pi(lmda)
    # geocentric ecliptic latitude
    beta = math.radians(5.128) * math.sin(F)
    beta = wrap_to_pi(beta)
    # distance (km)
    delta_distance = 385001 - 20905 * math.cos(M)

    # right ascension
    alpha = math.atan2(math.sin(lmda) * math.cos(epsilon) - math.tan(beta) * math.sin(epsilon), math.cos(lmda))
    alpha = wrap_to_0_2pi(alpha)

    # declination
    delta = math.asin(math.sin(beta) * math.cos(epsilon) + math.cos(beta) * math.sin(epsilon) * math.sin(lmda))
    delta = wrap_to_0_2pi(delta)

    # Greenwich hour angle at vernal equinox plus local offset
    theta = get_sidereal_time(d, rlong)
    # subtract right ascension of the moon to get hour angle
    tau = theta - alpha
    tau = wrap_to_0_2pi(tau)

    # finally calculate azimuth and elevation
    azim, elev = calc_azim_elev(rlat, tau, delta)

    return azim, elev


def calc_solar_position(coords, date_time):
    # convert coords to radians
    rlat, rlong = math.radians(coords[0]), math.radians(coords[1])
    # unpack date time
    year, month, day, hour, minute, second, weekday, yearday = date_time
    # julian date, number of days since Jan 1st 2000, 12 UTC, julian centuries since 2000
    d = calc_julian_date(year, month, day, hour, minute, second)

    # mean ecliptical length
    L = math.radians(280.460) + math.radians(0.9856474) * d
    L = wrap_to_0_2pi(L)

    # mean anomaly at epoch (0 at perihelion; increases uniformly with time)
    M = math.radians(357.528) + math.radians(0.9856003) * d
    M = wrap_to_0_2pi(M)

    # ecliptic length
    A = L + math.radians(1.915) * math.sin(M) + math.radians(0.01997) * math.sin(2. * M)
    A = wrap_to_0_2pi(A)

    # inclination to the ecliptic (plane of the earth's orbit)
    i = epsilon - math.radians(3.563e-7) * d
    i = wrap_to_0_2pi(i)

    # right ascension
    alpha = math.atan2(math.cos(i) * math.sin(A), math.cos(A))
    alpha = wrap_to_0_2pi(alpha)

    # declination
    delta = math.asin(math.sin(i) * math.sin(A))
    delta = wrap_to_0_2pi(delta)

    # Greenwich hour angle at vernal equinox plus local offset
    theta = get_sidereal_time(d, rlong)
    # subtract right ascension of the sun to get hour angle
    tau = theta - alpha
    tau = wrap_to_0_2pi(tau)

    # finally calculate azimuth and elevation
    azim, elev = calc_azim_elev(rlat, tau, delta)

    return azim, elev
