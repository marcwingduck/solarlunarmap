import math
from common import wrap_to_pi, wrap_to_0_2pi

epsilon = math.radians(23.4393)  # obliquity of the ecliptic (tilt of the earth's axis of rotation)


def calc_julian_date(year, month, day, hour=0, minute=0, second=0):
    day += hour/24 + minute/1440 + second/86400
    if month <= 2:
        month += 12
        year -= 1
    a = year//100
    b = a//4
    c = 2 - a + b
    e = math.floor(365.25 * (year + 4716))
    f = math.floor(30.6001 * (month + 1))
    # julian day
    jd = c + day + e + f - 1524.5
    # number of days since Greenwich noon, Terrestrial Time, on 1 January 2000
    n = jd - 2451545.
    # julian centuries since 2000
    t = n / 36525.
    return jd, n, t


def get_sidereal_time(d, long):
    # local sidereal time
    theta0 = math.radians(280.16 + 360.9856235 * d)
    theta = wrap_to_0_2pi(theta0 + long)  # eastern long positive, western negative
    return theta


def calc_azim_elev(lat, ha, delta):
    # finally calculate azimuth and elevation
    azim = math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat) - math.tan(delta) * math.cos(lat))
    elev = math.asin(math.cos(delta) * math.cos(ha) * math.cos(lat) + math.sin(delta) * math.sin(lat))
    # move to north clockwise convention
    azim = wrap_to_pi(azim + math.pi)
    return azim, elev


def calc_lunar_position(coords, date_time, debug=False):
    # convert coords to radians
    rlat, rlong = math.radians(coords[0]), math.radians(coords[1])
    # unpack date time
    year, month, day, hour, minute, second, weekday, yearday = date_time
    # julian date, number of days since Jan 1st 2000, 12 UTC, julian centuries since 2000
    jd, d, t = calc_julian_date(year, month, day, hour, minute, second)

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


def calc_solar_position(coords, date_time, debug=False):
    # convert coords to radians
    rlat, rlong = math.radians(coords[0]), math.radians(coords[1])
    # unpack date time
    year, month, day, hour, minute, second, weekday, yearday = date_time
    # julian date, number of days since Jan 1st 2000, 12 UTC, julian centuries since 2000
    jd, d, t = calc_julian_date(year, month, day, hour, minute, second)

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
