# Functions to handle TAP related calls

import pyvo as vo
import warnings
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
    Handler for TAP service

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

    # TODO: add start/end time
    query = f"SELECT TOP {maxrec} * FROM dbo.ObsPointing " \
            f"WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), {convert_stcs_for_adql(stcs)}) "
    if start_time is not None:
        query += f"AND t_min >= {start_time} and t_max <= {end_time} "
    if mission is not None:
        query += f"AND obs_collection = '{mission}' "
    print(query)

    # TODO: Decide: Sync vs Async queries
    results = tap.search(query, maxrec=maxrec)

    # Async query
    # job = tap.submit_job(query, maxrec=100)
    # job.run()
    # Check job.phase until it is COMPLETED
    # results = job.fetch_result()

    return results.to_table()


def clean_up_results(t, radius=0.0083):
    """
    Function to clean up results. Will add a column for distance to target at that time
    and will filter out those where the distance is too large
    Parameters
    ----------
    t
    radius

    Returns
    -------

    """

    return
