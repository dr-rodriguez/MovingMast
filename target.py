# Functions to handle the moving target

from astroquery.jplhorizons import Horizons
from polygon import check_direction, reverse_direction


def get_path(obj_name, times, location=None):
    # See more details at https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html
    # For valid locations: https://minorplanetcenter.net//iau/lists/ObsCodesF.html
    obj = Horizons(id=obj_name, location=location, epochs=times)
    eph = obj.ephemerides()
    return eph


def convert_path_to_polygon(eph, radius=0.0083):
    """

    Parameters
    ----------
    eph
    radius : float
        Width of path to build

    Returns
    -------

    """

    stcs = 'POLYGON '
    # Get first (upper) set of points
    for row in eph:
        stcs += f"{row['RA']} {row['DEC']-radius} "
    # Work backwords for the second set of coordinates
    for row in eph[::-1]:
        stcs += f"{row['RA']} {row['DEC']+radius} "

    # Check winding direction, these need to be counter-clockwise
    if not check_direction(stcs):
        stcs = reverse_direction(stcs)

    return stcs
