import math
from common import wrap_to_pi, wrap_to_0_2pi

epsilon = math.radians(23.4393)  # obliquity of the ecliptic (tilt of the earth's axis of rotation)
M_0_Earth = 357.528  # mean anomaly at epoch


def calc_julian_date(y, m, d):
    # julian day
    jd = (1461 * (y + 4800 + (m - 14) // 12)) // 4 + (367 * (m - 2 - 12 * ((m - 14) // 12))) // 12 - (3 * ((y + 4900 + (m - 14) // 12) // 100)) // 4 + d - 32075
    # number of days since Jan 1st 2000, 12 UTC
    n = jd - 2451545.
    # julian centuries since 2000
    t = n / 36525.
    return jd, n, t


def get_sidereal_time(t, hours):
    # middle sidereal time in hours
    theta_g_h = 6.697376 + 2400.05134 * t + 1.002738 * hours
    theta_g_h = theta_g_h % 24
    # Greenwich hour angle at vernal equinox (Frühlingspunkt)
    return theta_g_h * math.radians(15.)


def calc_azim_elev(lat, ha, delta):
    # finally calculate azimuth and elevation
    azim = math.atan2(math.sin(ha), (math.cos(ha) * math.sin(lat) - math.tan(delta) * math.cos(lat)))
    elev = math.asin(math.cos(delta) * math.cos(ha) * math.cos(lat) + math.sin(delta) * math.sin(lat))
    # move to north clockwise convention
    azim = wrap_to_pi(azim + math.pi)
    return azim, elev


def calc_lunar_position(coords, date_time, debug=False):
    # convert coords to radians
    rlat, rlong = math.radians(coords[0]), math.radians(coords[1])
    # unpack date time
    year, month, day, hour, minute, second, weekday, yearday = date_time
    # julian date, number of days since Jan 1st 2000, 12 UTC, julian centeries since 2000
    jd, d, t = calc_julian_date(year, month, day)
    # Greenwich hour angle at vernal equinox (Frühlingspunkt)
    theta_g = get_sidereal_time(t, hour + minute / 60.)
    # hour angle at given location
    theta = theta_g + rlong

    # geocentric ecliptic longitude
    L = math.radians(218.316) + math.radians(13.176396) * d
    L = wrap_to_0_2pi(L)

    # mean anomaly
    M = math.radians(134.963) + math.radians(13.064993) * d
    M = wrap_to_0_2pi(M)

    # mean distance
    F = math.radians(93.272) + math.radians(13.229350) * d

    # geocentric ecliptic coordinates
    # longitude
    lmda = L + math.radians(6.289) * math.sin(M)
    lmda = wrap_to_0_2pi(lmda)
    # latitude
    beta = math.radians(5.128) * math.sin(F)
    beta = wrap_to_0_2pi(beta)
    # distance (km)
    delta_distance = 385001 - 20905 * math.cos(M)

    # right ascension
    alpha = math.atan2(math.sin(lmda) * math.cos(epsilon) - math.tan(beta) * math.sin(epsilon), math.cos(lmda))
    alpha = wrap_to_0_2pi(alpha)

    # declination
    delta = math.asin(math.sin(beta) * math.cos(epsilon) + math.cos(beta) * math.sin(epsilon) * math.sin(lmda))
    delta = wrap_to_0_2pi(delta)

    # subtract right ascension of the moon to get hour angle
    tau = theta - alpha

    # finally calculate azimuth and elevation
    azim, elev = calc_azim_elev(rlat, tau, delta)

    if debug:
        print('-lunar------------------')
        print('jd = {}\tn = {}\tt = {}'.format(jd, d, t))
        print('L = {}°\tM = {}°\tF = {}'.format(math.degrees(L), math.degrees(M), F))
        print('lambda = {}°\tbeta = {}°\tdelta_dist = {}'.format(math.degrees(lmda), math.degrees(beta), delta_distance))
        print('delta = {}°\talpha = {}°\ttheta = {}°'.format(math.degrees(delta), math.degrees(alpha), math.degrees(theta)))
        print('azim = {}°\telev = {}°'.format(math.degrees(azim), math.degrees(elev)))
        print('-----------------------')

    return azim, elev


def calc_solar_position(coords, date_time, debug=False):
    # convert coords to radians
    rlat, rlong = math.radians(coords[0]), math.radians(coords[1])
    # unpack date time
    year, month, day, hour, minute, second, weekday, yearday = date_time
    # julian date, number of days since Jan 1st 2000, 12 UTC, julian centeries since 2000
    jd, d, t = calc_julian_date(year, month, day)
    # Greenwich hour angle at vernal equinox (Frühlingspunkt)
    theta_g = get_sidereal_time(t, hour + minute / 60.)
    # hour angle at given location
    theta = theta_g + rlong

    # mean ecliptical length
    L = math.radians(280.460) + math.radians(0.9856474) * d
    L = wrap_to_0_2pi(L)

    # mean anomaly (0 at perihelion; increases uniformly with time)
    M = math.radians(M_0_Earth) + math.radians(0.9856003) * d
    M = wrap_to_0_2pi(M)

    # ecliptic length
    A = L + math.radians(1.915) * math.sin(M) + math.radians(0.01997) * math.sin(2. * M)
    A = wrap_to_0_2pi(A)

    # inclination to the ecliptic (plane of the earth's orbit)
    i = epsilon - math.radians(3.563e-7) * d
    i = wrap_to_0_2pi(i)

    # right ascension ( not working: alpha = math.atan2(epsilon, A) )
    a1 = math.atan(math.cos(i) * math.tan(A))
    a2 = math.atan(math.cos(i) * math.tan(A)) + math.pi
    alpha = a1 if math.cos(A) > 0 else a2
    alpha = wrap_to_0_2pi(alpha)

    # declination
    delta = math.asin(math.sin(i) * math.sin(A))
    delta = wrap_to_0_2pi(delta)

    # subtract right ascension of the sun to get hour angle
    tau = theta - alpha

    # finally calculate azimuth and elevation
    azim, elev = calc_azim_elev(rlat, tau, delta)

    if debug:
        print('-solar------------------')
        print('jd = {}\tn = {}\tL = {}°'.format(jd, d, math.degrees(L)))
        print('g = {}°\tA = {}°\te = {}°'.format(math.degrees(M), math.degrees(A), math.degrees(i)))
        print('a = {}°\td = {}°'.format(math.degrees(alpha), math.degrees(delta)))
        print('t0 = {}\tt = {}°'.format(t, math.degrees(theta)))
        print('a = {}°\th = {}°'.format(math.degrees(azim), math.degrees(elev)))
        print('-----------------------')

    return azim, elev


if __name__ == '__main__':
    coords = (48.860536, 2.332237)
    now = 2021, 2, 7, 15, 31, 2, 6, 38
    solar = calc_solar_position(coords, now, True)
    lunar = calc_lunar_position(coords, now, True)
