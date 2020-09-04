# Functions to handle TAP related calls

import pyvo as vo
import warnings
from astropy.time import Time
from astroquery.jplhorizons import Horizons
from regions import PixCoord, PolygonPixelRegion, CirclePixelRegion
from .polygon import parse_s_region
from astroquery.mast import Observations
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
        mission_list = mission.split(',')
        mission_string = ','.join([f"'{x}'" for x in mission_list])
        query += f"AND obs_collection in ({mission_string}) "
    # print(query)

    # TODO: Decide: Sync vs Async queries
    print('Querying MAST...')
    results = tap.search(query, maxrec=maxrec)

    # Async query
    # job = tap.submit_job(query, maxrec=100)
    # job.run()
    # Check job.phase until it is COMPLETED
    # results = job.fetch_result()

    t = results.to_table()

    # Add extra columns
    if len(t) > 0:
        # Decode bytes columns
        for col in t.colnames:
            if isinstance(t[col][0], bytes):
                t[col] = [x.decode() for x in t[col]]

        # Add mid-point time in both jd and iso
        t['t_mid'] = (t['t_max'] + t['t_min']) / 2 + 2400000.5
        t['obs_mid_date'] = Time(t['t_mid'], format='jd').iso
        t['start_date'] = Time(t['t_min'], format='mjd').iso
        t['end_date'] = Time(t['t_max'], format='mjd').iso

    return t


def _detail_check(eph, polygon_pix, observation_coords, start_date, end_date, radius=0.0083, aggressive_check=False):
    # A more detailed check for polygon footprint matching.
    # This checks each location in the original ephemerides and confirms if an observation intersects it

    flag = False
    for row in eph:
        if aggressive_check:
            if ((row['datetime_jd'] - 2400000.5) > end_date) or ((row['datetime_jd'] - 2400000.5) < start_date):
                flag = False
                continue

        target_coords = PixCoord(row['RA'], row['DEC'])
        if radius is None or radius < 0 and observation_coords is not None:
            flag = target_coords in polygon_pix
        else:
            target_circle = CirclePixelRegion(center=target_coords, radius=radius)
            flag = (target_coords in polygon_pix) or (observation_coords in target_circle)

        if flag:
            break

    return flag


def clean_up_results(t_init, obj_name, orig_eph=None, id_type='smallbody', location=None, radius=0.0083,
                     aggressive_check=False):
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

    orig_eph: astropy Table
        Original ephemerides table

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

    radius: float
        Size of target for intersection calculations

    aggressive_check: bool
        Perform additional time checks; can remove valid observations (Default: False)

    Returns
    -------
    t: astropy Table
        Astropy Table with only those where the moving target was in the footprint
    """

    if len(t_init) == 0:
        return None

    if radius is not None and not isinstance(radius, float):
        radius = float(radius)

    t = t_init.copy()

    # Sort by mid point time
    t['t_mid'] = (t['t_max'] + t['t_min']) / 2 + 2400000.5
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
            observation_coords = PixCoord(row['s_ra'], row['s_dec'])
            if radius is None or radius < 0:
                flag = target_coords in polygon_pix
            else:
                target_circle = CirclePixelRegion(center=target_coords, radius=radius)
                flag = (target_coords in polygon_pix) or (observation_coords in target_circle)
            if orig_eph is not None and not flag:
                flag = _detail_check(orig_eph, polygon_pix, observation_coords,
                                     start_date=row['t_min'], end_date=row['t_max'],
                                     radius=radius, aggressive_check=aggressive_check)
            # print(row['obs_id'], flag)
        except Exception as e:
            print(f"ERROR checking footprint for {row['obs_id']} with: {e}"
                  f"\nAssuming False")
            flag = False

        check_list.append(flag)

    # Set the flags
    t['in_footprint'] = check_list

    return t[t['in_footprint']]


def get_files(t_init, obs_id=''):
    t = t_init.copy()
    obs_list = obs_id.split(',')
    obs_list = [x.strip() for x in obs_list]
    mask = [x in obs_list for x in t['obs_id']]
    t = t[mask]
    data_products_by_id = Observations.get_product_list(t['obsID'].astype(str))
    # data_products_by_id['Download'] = [f'<a href="https://mast.stsci.edu/portal/api/v0.1/Download/file?uri={x}">Download</a>'
    #                                    for x in data_products_by_id['dataURI']]
    return data_products_by_id
