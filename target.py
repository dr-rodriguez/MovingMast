# Functions to handle the moving target

from astroquery.jplhorizons import Horizons


def get_path(obj_name, times, location=None):
    # See more details at https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html
    # For valid locations: https://minorplanetcenter.net//iau/lists/ObsCodesF.html
    obj = Horizons(id=obj_name, location=location, epochs=times)
    eph = obj.ephemerides()
    return eph


def convert_path_to_polygon(eph):
    # TODO: Implement this
    return
