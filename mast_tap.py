# Functions to handle TAP related calls

import pyvo as vo
import warnings
from astroquery.jplhorizons import Horizons
from regions import PixCoord, PolygonPixelRegion, CirclePixelRegion
from polygon import parse_s_region
warnings.simplefilter('ignore')  # block out warnings


def convert_stcs_for_adql(stcs):
    adql = "POLYGON('ICRS', "
    for elem in stcs.split():
        if elem == 'POLYGON': continue
        if elem == '': continue
        adql += f'{elem}, '
    adql = adql[:-2] + ')'
    return adql


def run_tap_query(stcs, start_time=None, end_time=None, mission=None,
                  service='http://vao.stsci.edu/CAOMTAP/TapService.aspx', maxrec=100):
    """
    Handler for TAP service.

    Parameters
    ----------
    stcs : str
        Polygon to search for
    start_time : float
        MJD start time
    end_time : float
        MJD end time
    mission : str
        Mission to search for (eg, HST, TESS, etc). (Default: None)
    service : str
        Service to use (Default: STScI CAOMTAP)
    maxrec : int
        Number of records to return

    Returns
    -------
    results : astropy Table
        Astropy Table of results
    """
    tap = vo.dal.TAPService(service)

    query = f"SELECT TOP {maxrec} * " \
            f"FROM dbo.ObsPointing " \
            f"WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), {convert_stcs_for_adql(stcs)}) "
    if start_time is not None:
        query += f"AND t_min >= {start_time} and t_max <= {end_time} "
    if mission is not None:
        query += f"AND obs_collection = '{mission}' "
    # print(query)

    # TODO: Decide: Sync vs Async queries
    print('Querying MAST...')
    results = tap.search(query, maxrec=maxrec)

    # Async query
    # job = tap.submit_job(query, maxrec=100)
    # job.run()
    # Check job.phase until it is COMPLETED
    # results = job.fetch_result()

    return results.to_table()


def clean_up_results(t_init, obj_name, id_type='smallbody', location=None, radius=0.0083):
    """
    Function to clean up results. Will check if the target is inside the observation footprint.
    If a radius is provided, will also construct a circle and check if the observation center is in the target circle.

    Parameters
    ----------
    t_init: atropy Table
        Initial astropy Table

    obj_name: str
        Object name. May require specific formatting (i.e. selecting between
       the codes for Jupiter and Jupiter barycenter). See JPL Horizons documentation

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

    radius : float
        Size of target for intersection calculations

    Returns
    -------
    t: astropy Table
        Astropy Table with only those where the moving target was in the footprint
    """

    t = t_init.copy()

    # Add mid-point time and sort by that first
    t['t_mid'] = (t['t_max'] + t['t_min'])/2 + 2400000.5
    t.sort('t_mid')

    # Ephemerides results are sorted by time, hence the initial sort
    print('Verifying footprints...')

    # Fix for TESS
    if location is not None and location.upper() == '@TESS':
        print('Restriction for TESS observations')
        threshold = 2456778.50000  # 2018-05-01
        ind = t['t_mid'] > threshold
        t = t[ind]

    eph = Horizons(id=obj_name, location=location, id_type=id_type, epochs=t['t_mid']).ephemerides()

    # For each row in table, check s_region versus target position at mid-time
    check_list = []
    for i, row in enumerate(t):
        # print(row['t_mid'], eph['datetime_jd'][i], eph['RA'][i], eph['DEC'][i])

        # Create a polygon for the footprint and check if target is inside polygon
        try:
            stcs = parse_s_region(row['s_region'])
            xs = stcs['ra']
            ys = stcs['dec']
            polygon_pix = PolygonPixelRegion(vertices=PixCoord(x=xs, y=ys))
            target_coords = PixCoord(eph['RA'][i], eph['DEC'][i])
            if radius is None or radius <= 0:
                flag = target_coords in polygon_pix
            else:
                target_circle = CirclePixelRegion(center=target_coords, radius=radius)
                observation_coords = PixCoord(row['s_ra'], row['s_dec'])
                flag = (target_coords in polygon_pix) or (observation_coords in target_circle)
            # print(stcs, flag)
        except Exception as e:
            print(f"ERROR checking footprint for {row['obs_id']} with: {e}"
                  f"\nAssuming False")
            flag = False

        check_list.append(flag)

    # Set the flags
    t['in_footprint'] = check_list

    return t[t['in_footprint']]
