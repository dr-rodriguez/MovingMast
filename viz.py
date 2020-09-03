# Functions for handling Jupiter visualizations

import panel as pn
import param
from mast_tap import run_tap_query, clean_up_results
from target import get_path, convert_path_to_polygon
from plotting import polygon_bokeh, mast_bokeh


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
    max_rec = pn.widgets.TextInput(name="Maximum number of MAST records", value='200')
    mission = pn.widgets.TextInput(name="Mission filter for MAST queries (Default of None=all missions)", value='None')
    radius = pn.widgets.TextInput(name="Footprint radius/width (degrees)", value='0.0083')
    location = pn.widgets.TextInput(name="User location (Default of None=geocentric)", value='None')

    # Column selector
    eph_cols = ['solar_presence', 'flags', 'RA_app', 'DEC_app', 'RA_rate', 'DEC_rate', 'AZ', 'EL',
               'AZ_rate', 'EL_rate', 'sat_X',
               'sat_Y', 'sat_PANG', 'siderealtime', 'airmass', 'magextinct', 'V', 'surfbright', 'illumination',
               'illum_defect', 'sat_sep', 'sat_vis', 'ang_width', 'PDObsLon', 'PDObsLat', 'PDSunLon',
               'PDSunLat', 'SubSol_ang', 'SubSol_dist', 'NPole_ang', 'NPole_dist', 'EclLon', 'EclLat', 'r',
               'r_rate', 'delta', 'delta_rate', 'lighttime', 'vel_sun', 'vel_obs', 'elong', 'elongFlag',
               'alpha', 'lunar_elong', 'lunar_illum', 'sat_alpha', 'sunTargetPA', 'velocityPA',
               'OrbPlaneAng', 'constellation', 'TDB-UT', 'ObsEclLon', 'ObsEclLat', 'NPole_RA', 'NPole_DEC',
               'GlxLon', 'GlxLat', 'solartime', 'earth_lighttime', 'RA_3sigma', 'DEC_3sigma', 'SMAA_3sigma',
               'SMIA_3sigma', 'Theta_3sigma', 'Area_3sigma', 'RSS_3sigma', 'r_3sigma', 'r_rate_3sigma',
               'SBand_3sigma', 'XBand_3sigma', 'DoppDelay_3sigma', 'true_anom', 'hour_angle',
               'alpha_true', 'PABLon', 'PABLat']
    eph_col_choice = pn.widgets.MultiChoice(name="Choose Extra Columns", options=eph_cols)

    mast_cols = ['calib_level', 's_ra',
                 's_dec', 't_min', 't_max', 'wavelength_region', 'em_min',
                 'em_max', 'target_classification', 'obs_title', 't_obs_release',
                 'proposal_id', 'proposal_type', 'project', 'sequence_number',
                 'provenance_name', 's_region', 'jpegURL', 'dataURL', 'dataRights', 'mtFlag',
                 'srcDen', 'intentType', 'obsID', 'objID', 't_mid']
    mast_col_choice = pn.widgets.MultiChoice(name="Choose Extra Columns", options=mast_cols)

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
            radius = float(self.radius.value)
            location = self.location.value
            if location.lower() == 'none':
                location = None
            req_cols = ['targetname', 'datetime_str', 'datetime_jd', 'RA', 'DEC']
            cols = req_cols + self.eph_col_choice.value
            self.eph = get_path(self.obj_name.value, times, id_type=self.id_type.value, location=location)
            self.stcs = convert_path_to_polygon(self.eph, radius=radius)
            self.results = None
        except ValueError as e:
            return pn.pane.Markdown(f'{e}')
        return self.eph[cols].show_in_notebook(display_length=10)

    @param.depends('tap_button')
    def get_mast(self):
        if self.eph is None or self.stcs is None:
            return pn.pane.Markdown('## Fetch an ephemerides first and then run the MAST query.')
        start_time = min(self.eph['datetime_jd']) - 2400000.5
        end_time = max(self.eph['datetime_jd']) - 2400000.5
        try:
            maxrec = int(self.max_rec.value)
            location = self.location.value
            mission = self.mission.value
            if location.lower() == 'none':
                location = None
            if mission.lower() == 'none':
                mission = None
            temp_results = run_tap_query(self.stcs, start_time=start_time, end_time=end_time,
                                         maxrec=maxrec, mission=mission)
            self.results = clean_up_results(temp_results, obj_name=self.obj_name.value,
                                            id_type=self.id_type.value, location=location)
            req_cols = ['obs_id', 'obs_collection', 'target_name', 'dataProduct_Type', 'instrument_name',
                        'filters', 't_exptime', 'proposal_pi']
            cols = req_cols + self.mast_col_choice.value
        except Exception as e:
            return pn.pane.Markdown(f'{e}')
        return self.results[cols].show_in_notebook(display_length=10)

    @param.depends('stcs')
    def fetch_stcs(self):
        if self.stcs is None:
            return pn.pane.Markdown('## Fetch an ephemerides first.')
        p = polygon_bokeh(self.stcs, display=False)
        return pn.Column(pn.pane.Markdown(f'STCS Polygon:  \n```{self.stcs}```'),
                         pn.pane.Bokeh(p))

    @param.depends('eph', 'stcs', 'results')
    def mast_figure(self):
        if self.eph is None or self.results is None:
            return pn.pane.Markdown('## Fetch an ephemerides first and then run the MAST query.')
        p = mast_bokeh(self.eph, self.results, self.stcs, display=False)
        return pn.pane.Bokeh(p)

    # Panel displays
    def additional_parameters(self):
        return pn.Column(self.max_rec, self.mission, self.radius, self.location)

    def panel(self, debug=False):
        title = pn.pane.Markdown('# Search MAST for Moving Targets')
        row1 = pn.Row(self.obj_name, self.id_type)
        row2 = pn.Row(self.start_time, self.stop_time, self.time_step)
        button_row = pn.Row(self.param['ephem_button'], self.param['tap_button'])
        output_tabs = pn.Tabs(('Ephemerides', pn.Column(self.eph_col_choice,
                                                        self.get_ephem)),
                              ('MAST Results', pn.Column(self.mast_col_choice,
                                                         self.get_mast)),
                              ('MAST Plot', self.mast_figure),
                              ('Additional Parameters', self.additional_parameters)
                              )
        if debug:
            output_tabs.append(('Debug', self.fetch_stcs))
        mypanel = pn.Column(title, pn.layout.Divider(),
                            row1, row2, button_row,
                            output_tabs)
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
