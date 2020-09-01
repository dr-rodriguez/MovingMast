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


def run_query(stcs, start_time, end_time, mission=None,
              service='http://vao.stsci.edu/CAOMTAP/TapService.aspx', maxrec=100):
    tap = vo.dal.TAPService(service)

    # TODO: add start/end time
    query = f"SELECT TOP {maxrec} * FROM dbo.ObsPointing " \
            f"WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec), {convert_stcs_for_adql(stcs)})"
    print(query)

    # TODO: Decide: Sync vs Async queries
    results = tap.search(query, maxrec=maxrec)

    # Async query
    # job = tap.submit_job(query, maxrec=100)
    # job.run()
    # Check job.phase until it is COMPLETED
    # results = job.fetch_result()

    return results.to_table()
