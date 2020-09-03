# Functions to handle the moving target

from astroquery.jplhorizons import Horizons
from polygon import check_direction, reverse_direction
import time


def get_path(obj_name, times, id_type='smallbody', location=None):
    """

    # See more details at https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html
    # For valid locations: https://minorplanetcenter.net//iau/lists/ObsCodesF.html

    Parameters
    ----------

    obj_name: str
       Object name. May require specific formatting (i.e. selecting between
       the codes for Jupiter and Jupiter barycenter). See JPL Horizons documentation

    times: float or arr
       Times to check, input as a float, array, or specified start/stop/step
       (example: {'start':'2019-01-01', 'stop':'2019-12-31', 'step':'1d'})

    id_type: str
       Object ID type for JPL Horizons. Defaults to smallbody (an asteroid or comet).
       Best to be as specific as possible to find the correct body.

       majorbody: planets and satellites
       smallbody: asteroids and comets
       asteroid_name: name of asteroid
       comet_name: name of comet
       name: any target name
       designation: any asteroid or comet designation

    location: str
       Default of None uses a geocentric location for queries.
       For specific spacecrafts, insert location

       Examples:
       TESS: @TESS
       Hubble: @hst
       Kepler: 500@-227

    Returns
    -------
    eph: Astropy table
        Table object with the JPL Horizons calculated ephemerides

    """

    obj = Horizons(id=obj_name, location=location, id_type=id_type, epochs=times)
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


def check(date):
    try:
      valid_date = time.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True
