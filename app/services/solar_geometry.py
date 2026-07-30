
import math

OBLIQUITY = 23.45

SOLSTICE_SUMMER_DOY = 172
EQUINOX_DOY = 81
SOLSTICE_WINTER_DOY = 355


def declination(day_of_year):
    return OBLIQUITY * math.sin(math.radians(360.0 * (284 + day_of_year) / 365.0))


def sun_vector(lat_deg, decl_deg, hour_angle_deg):
    phi = math.radians(lat_deg)
    dec = math.radians(decl_deg)
    omega = math.radians(hour_angle_deg)
    east = -math.cos(dec) * math.sin(omega)
    north = math.cos(phi) * math.sin(dec) - math.sin(phi) * math.cos(dec) * math.cos(omega)
    up = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(omega)
    return east, north, up


def elevation(lat_deg, decl_deg, hour_angle_deg):
    return math.degrees(math.asin(
        max(-1.0, min(1.0, sun_vector(lat_deg, decl_deg, hour_angle_deg)[2]))))


def azimuth_from_north(east, north):
    return math.degrees(math.atan2(east, north)) % 360.0


def sunrise_hour_angle(lat_deg, decl_deg):
    phi = math.radians(lat_deg)
    dec = math.radians(decl_deg)
    cos_omega = -math.tan(phi) * math.tan(dec)
    if cos_omega >= 1.0:
        return 0.0
    if cos_omega <= -1.0:
        return 180.0
    return math.degrees(math.acos(cos_omega))


def day_length_hours(lat_deg, decl_deg):
    return 2.0 * sunrise_hour_angle(lat_deg, decl_deg) / 15.0


def sun_track(lat_deg, decl_deg, step_deg=2.0):
    limit = sunrise_hour_angle(lat_deg, decl_deg)
    if limit <= 0:
        return []
    points = []
    omega = -limit
    while omega <= limit + 1e-9:
        east, north, up = sun_vector(lat_deg, decl_deg, omega)
        if up >= -1e-6:
            points.append((omega, east, north, max(0.0, up)))
        omega += step_deg
    return points


def sunrise_azimuth(lat_deg, decl_deg):
    limit = sunrise_hour_angle(lat_deg, decl_deg)
    east, north, _ = sun_vector(lat_deg, decl_deg, -limit)
    return azimuth_from_north(east, north)


def incidence_cosine(sun, tilt_deg, panel_azimuth_deg):
    beta = math.radians(tilt_deg)
    gamma = math.radians(panel_azimuth_deg)
    normal = (math.sin(beta) * math.sin(gamma),
              math.sin(beta) * math.cos(gamma),
              math.cos(beta))
    return max(0.0, sum(a * b for a, b in zip(sun, normal)))
