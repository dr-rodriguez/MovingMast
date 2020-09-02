# Functions for handling Jupiter visualizations

import panel as pn
from mast_tap import run_tap_query, clean_up_results
from target import get_path


def query_mast():
    obj_name = pn.widgets.TextInput(name="Object Name or Specification", value='')
    start_time = pn.widgets.TextInput(name="Start Time", value='2019-04-01')
    stop_time = pn.widgets.TextInput(name="Stop Time", value='2019-04-10')
    time_step = pn.widgets.TextInput(name="Time Step", value='1d')
    id_type = pn.widgets.Select(name='Object Type', options=['majorbody', 'smallbody', 'asteroid_name',
                                                             'comet_name', 'name', 'designation'])
    button = pn.widgets.Button(name='Fetch Ephemerides', button_type='primary')

    @pn.depends(obj_name, start_time, stop_time, time_step, id_type)
    def get_ephem(obj_name, start_time, stop_time, time_step, id_type):
        if obj_name == '':
            return pn.pane.Str('Provide the name or identifier of an object to search for.')
        times = {'start': start_time, 'stop': stop_time, 'step': time_step}
        try:
            eph = get_path(obj_name, times, id_type=id_type, location=None)
        except ValueError as e:
            return pn.pane.Str(f'{e}')
        return eph.show_in_notebook(display_length=5)

    row1 = pn.Row(obj_name, id_type)
    row2 = pn.Row(start_time, stop_time, time_step)
    button_row = pn.Row(button)
    mypanel = pn.Column(row1, row2, button_row, get_ephem)

    return mypanel
