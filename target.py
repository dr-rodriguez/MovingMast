# Functions to handle the moving target

from astroquery.jplhorizons import Horizons


def get_path(obj_name, times, location='@TESS'):
    obj = Horizons(id=obj_name, location=location, epochs=times)
    eph = obj.ephemerides()
    ra = eph['RA'][0]
    dec = eph['DEC'][0]
    return ra, dec
