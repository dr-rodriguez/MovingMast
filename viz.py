# Functions for handling Jupiter visualizations

import panel as pn
import param
from mast_tap import run_tap_query, clean_up_results
from target import get_path, convert_path_to_polygon


class MastQuery(param.Parameterized):
    # Global variables
    eph = param.Parameter(default=None, doc="eph table")
    stcs = param.Parameter(default=None, doc="polygon")
    results = param.Parameter(default=None, doc="MAST Results")

    # Widgets
    obj_name = pn.widgets.TextInput(name="Object Name or Specification", value='')
    start_time = pn.widgets.TextInput(name="Start Time", value='2019-04-01')
    stop_time = pn.widgets.TextInput(name="Stop Time", value='2019-04-10')
    time_step = pn.widgets.TextInput(name="Time Step", value='1d')
    id_type = pn.widgets.Select(name='Object Type', options=['majorbody', 'smallbody', 'asteroid_name',
                                                             'comet_name', 'name', 'designation'])

    # Actions
    ephem_button = param.Action(lambda x: x.param.trigger('ephem_button'), label='Fetch Ephemerides')
    tap_button = param.Action(lambda x: x.param.trigger('tap_button'), label='Fetch MAST Results')

    # Callback functions
    @param.depends('ephem_button')
    def get_ephem(self):
        if self.obj_name.value == '':
            self.eph = None
            self.stcs = None
            return pn.pane.Markdown('## Provide the name or identifier of an object to search for.')
        times = {'start': self.start_time.value, 'stop': self.stop_time.value, 'step': self.time_step.value}
        try:
            self.eph = get_path(self.obj_name.value, times, id_type=self.id_type.value, location=None)
            self.stcs = convert_path_to_polygon(self.eph)
        except ValueError as e:
            return pn.pane.Markdown(f'{e}')
        return self.eph.show_in_notebook(display_length=5)

    @param.depends('tap_button')
    def get_mast(self):
        if self.eph is None or self.stcs is None:
            return pn.pane.Markdown('## Fetch an ephemerides first and then run the query.')
        start_time = min(self.eph['datetime_jd']) - 2400000.5
        end_time = max(self.eph['datetime_jd']) - 2400000.5
        temp_results = run_tap_query(self.stcs, start_time=start_time, end_time=end_time, maxrec=100)
        self.results = clean_up_results(temp_results, obj_name=self.obj_name.value,
                                        id_type=self.id_type.value, location=None)
        return self.results.show_in_notebook(display_length=20)

    # Panel displays
    def panel(self):
        title = pn.Row(pn.pane.Markdown('# Search MAST for Moving Targets'))
        row1 = pn.Row(self.obj_name, self.id_type)
        row2 = pn.Row(self.start_time, self.stop_time, self.time_step)
        button_row = pn.Row(self.param['ephem_button'], self.param['tap_button'])
        mypanel = pn.Column(title, row1, row2, button_row,
                            pn.Tabs(('Ephemerides', self.get_ephem),
                                    ('MAST Results', self.get_mast)))
        return mypanel


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
