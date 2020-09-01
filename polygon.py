# Functions to handle polygon conversions

import numpy as np
import astropy.units as u
from astropy.visualization.wcsaxes.patches import _rotate_polygon
from astropy.coordinates import SkyCoord


def convert_to_polygon(center_ra, center_dec, radius, resolution=16):
    """
    Convert a circle to a polygon

    Parameters
    ----------
    center_ra: astropy.units.Quantity
    center_dec: astropy.units.Quantity
    radius: astropy.units.Quantity
    resolution: int

    Returns
    -------
    lon
    lat
    """

    lon = np.linspace(0., 2 * np.pi, resolution + 1)[:-1] * u.radian
    lat = np.repeat(0.5 * np.pi - radius.to_value(u.radian), resolution) * u.radian
    lon, lat = _rotate_polygon(lon, lat, center_ra, center_dec)
    lon = lon.to_value(u.deg).tolist()
    lat = lat.to_value(u.deg).tolist()
    return lon, lat


def parse_s_region(s_region):
    ra = []
    dec = []
    counter = 0

    if s_region is None or s_region.split()[0].upper() not in ('POLYGON', 'CIRCLE'):
        print('Unsupported shape: {}'.format(s_region))
        return None

    if s_region.split()[0].upper() == 'POLYGON':
        for elem in s_region.strip().split():
            try:
                value = float(elem)
            except ValueError:
                continue
            if counter % 2 == 0:
                ra.append(value)
            else:
                dec.append(value)
            counter += 1
    elif s_region.split()[0].upper() == 'CIRCLE':
        center_ra, center_dec, radius = None, None, None
        for elem in s_region.strip().split():
            try:
                value = float(elem)
            except ValueError:
                continue
            if counter % 2 == 1:
                center_dec = value
            if center_ra is None and counter % 2 == 0:
                center_ra = value
            else:
                radius = value
            counter += 1
        ra, dec = convert_to_polygon(center_ra*u.deg, center_dec*u.deg, radius*u.deg)

    return {'ra': ra, 'dec': dec}


def _frame_convert(points):
    # Helper function to transform points (ra/dec) to Galactic coordinates and avoid pole issues
    c_icrs = SkyCoord(ra=points[:, 0], dec=points[:, 1], unit='deg', frame='icrs')
    c_gal = c_icrs.galactic

    # Return Galactic l and b in the same format as points
    return np.dstack((c_gal.l.value, c_gal.b.value))[0]


def check_direction(STCS):
    """
    Function to check vertices of closed STCS and see if they are counter-clockwise.
    Adapted from https://gist.github.com/jd-au/45d1cdc0c6e2a7bc848a4be8f46c8958

    Parameters
    ----------
    STCS : str
        String describing the bounds of the object.

    Returns
    -------
    True/False
    """

    data = STCS.split()
    data = data[1:]  # ignore the polygon part

    # Strip string beyond polygon, if present
    try:
        _ = float(data[0])
    except ValueError:
        data = data[1:]

    try:
        points = np.array(data).reshape(int(len(data) / 2), 2).astype(float)
    except ValueError:
        print('WARNING: Unable to test polygon direction. Non-numeric characters/Multipolygon')
        return True

    # If closed, remove the last point
    if points[-1, 0] == points[0, 0] and points[-1, 1] == points[0, 1]:
        points = points[:-1]

    # Check if close to Equatorial poles, switch to Galactic
    if abs(np.mean(points[:, 1])) >= 75:
        points = _frame_convert(points)

    # Fix cases that pass ra=360/0
    min_ra = min(points[:, 0])
    max_ra = max(points[:, 0])
    avg_ra = np.mean(points[:, 0])
    delta_ra = (max_ra - min_ra) % 360
    if delta_ra >= 180:
        if avg_ra < 180:  # for values close to zero, shift them up so they are 180..540
            for i, val in enumerate(points[:, 0]):
                if points[i, 0] < avg_ra: points[i, 0] += 360
        else:  # for values close to 360, shift them down so they are -180..180
            for i, val in enumerate(points[:, 0]):
                if points[i, 0] > avg_ra: points[i, 0] -= 360

    # Implementation of Shoelace formula
    total = 0
    for curr_idx in range(len(points)):
        next_idx = curr_idx + 1 if curr_idx < len(points) - 1 else 0
        total += (points[next_idx, 0] - points[curr_idx, 0]) * (points[next_idx, 1] + points[curr_idx, 1])

    # Positive: counter-clockwise direction (as required)
    if total > 0:
        # print('Polygon is CCW')
        return True
    else:
        # print('Polygon is CW')
        return False


def reverse_direction(STCS):
    """
    Function to correct polygon cycling direction (10-28-2018 by A.P.Marston)

    Parameters
    ----------
    STCS : str
        String describing the bounds of the object.

    Returns
    -------
    STCS : str
        Reversed STCS
    """

    data = STCS.split()
    data = data[1:]  # ignore the polygon part

    # Strip string beyond polygon, if present
    extra_string = ''
    try:
        value = float(data[0])
    except ValueError:
        extra_string = data[0]
        data = data[1:]

    # make array of the points and then reverse the order of the point pairs
    points = np.array(data).reshape(int(len(data) / 2), 2)[::-1]

    # recreate STCS
    STCS = "POLYGON {}".format(extra_string)
    for x in range(len(points)):
        STCS += " {} {}".format(points[x, 0], points[x, 1])

    return STCS
