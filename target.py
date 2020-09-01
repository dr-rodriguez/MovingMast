# Functions to handle the moving target

from astroquery.jplhorizons import Horizons


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
    for row in eph:
        stcs += f"{row['RA']} {row['DEC']-radius} "
        stcs += f"{row['RA']} {row['DEC']+radius} "

    return stcs
