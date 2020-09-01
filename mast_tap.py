# Functions to handle TAP related calls

import pyvo as vo
import warnings
warnings.simplefilter('ignore')  # block out warnings


def run_query(stcs, start_time, end_time, mission=None,
              service='http://vao.stsci.edu/CAOMTAP/TapService.aspx', maxrec=1000):
    tap = vo.dal.TAPService(service)

    # TODO: write this
    query = "SELECT * FROM dbo.ObsPointing"
    print(query)

    # TODO: Decide: Sync vs Async queries
    results = tap.search(query, maxrec=maxrec)

    # Async query
    # job = tap.submit_job(query, maxrec=100)
    # job.run()
    # Check job.phase until it is COMPLETED
    # results = job.fetch_result()

    return results.to_table()

