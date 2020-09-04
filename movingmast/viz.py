# Functions for handling Jupiter visualizations

import panel as pn
import param
from movingmast.mast_tap import run_tap_query, clean_up_results, get_files
from movingmast.target import get_path, convert_path_to_polygon, check_times
from movingmast.plotting import polygon_bokeh, mast_bokeh


class MastQuery(param.Parameterized):

    def __init__(self, data_tables=False):
        self.data_tables = data_tables
        self.width = 900
        if data_tables:
            self.script = """
            <script>
            $(document).ready( function () {
                $('table').DataTable();
            } );
            </script>
            """
        super().__init__()

    # Global variables
    eph = param.Parameter(default=None, doc="eph table")
    stcs = param.Parameter(default=None, doc="polygon")
    results = param.Parameter(default=None, doc="MAST Results")

    # Widgets
    obj_name = pn.widgets.TextInput(name="Object Name or Specification", value='')
    start_time = pn.widgets.TextInput(name="Start Time", value='1995-07-17')
    stop_time = pn.widgets.TextInput(name="Stop Time", value='1995-07-30')
    time_step = pn.widgets.TextInput(name="Time Step (eg, 12h, 1d)", value='1d')
    id_type = pn.widgets.Select(name='Object Type', options=['majorbody', 'smallbody', 'asteroid_name',
                                                             'comet_name', 'name', 'designation'])
    max_rec = pn.widgets.TextInput(name="Maximum number of MAST records", value='200')
    mission = pn.widgets.TextInput(name="Comma-separated mission filter (Default of None=all missions)", value='None')
    radius = pn.widgets.TextInput(name="Footprint radius/width (degrees)", value='0.0083')
    location = pn.widgets.TextInput(name="User location (Default of None=geocentric)", value='None')
    obs_ids = pn.widgets.TextInput(name="Comma-separated observations to search files for (obs_id)", value='')
    time_check = pn.widgets.Checkbox(name="Perform hard time cuts (can remove valid matches)", value=False)

    # Column selector
    eph_cols = ['targetname', 'datetime_str', 'datetime_jd', 'RA', 'DEC',
                'solar_presence', 'flags', 'RA_app', 'DEC_app', 'RA_rate', 'DEC_rate', 'AZ', 'EL',
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
    eph_col_choice = pn.widgets.MultiChoice(name="Choose columns",
                                            options=eph_cols,
                                            value=['targetname', 'datetime_str', 'datetime_jd', 'RA', 'DEC'])

    mast_cols = ['obs_id', 'obs_collection', 'target_name',
                 'dataProduct_Type', 'instrument_name',
                 'filters', 't_exptime', 'proposal_pi', 'calib_level', 's_ra',
                 's_dec', 't_min', 't_max', 'wavelength_region', 'em_min',
                 'em_max', 'target_classification', 'obs_title', 't_obs_release',
                 'proposal_id', 'proposal_type', 'project', 'sequence_number',
                 'provenance_name', 's_region', 'jpegURL', 'dataURL', 'dataRights', 'mtFlag',
                 'srcDen', 'intentType', 'obsID', 'objID', 't_mid', 'obs_mid_date', 'start_date', 'end_date']
    mast_col_choice = pn.widgets.MultiChoice(name="Choose columns",
                                             options=mast_cols,
                                             value=['obs_id', 'obs_collection', 'target_name',
                                                    'dataProduct_Type', 'instrument_name',
                                                    'filters', 't_exptime', 'proposal_pi'])

    product_columns = ['obsID', 'obs_collection', 'dataproduct_type', 'obs_id', 'description', 'type',
                       'dataURI', 'productType', 'productGroupDescription', 'productSubGroupDescription',
                       'productDocumentationURL', 'project', 'prvversion', 'proposal_id',
                       'productFilename', 'size', 'parent_obsid', 'dataRights']
    product_col_choice = pn.widgets.MultiChoice(name="Choose columns",
                                                options=product_columns,
                                                value=['obs_id', 'obs_collection', 'productFilename',
                                                       'dataproduct_type', 'productType',
                                                       'productSubGroupDescription', 'description'])

    # Actions
    ephem_button = param.Action(lambda x: x.param.trigger('ephem_button'), label='Fetch Ephemerides')
    tap_button = param.Action(lambda x: x.param.trigger('tap_button'), label='Fetch MAST Results')
    product_button = param.Action(lambda x: x.param.trigger('product_button'), label='Fetch MAST Files')
    full_run = param.Action(lambda x: x.param.trigger('full_run'), label='Search MAST')

    # Callback functions
    @param.depends('ephem_button', 'full_run')
    def get_ephem(self):
        if self.obj_name.value == '':
            self.eph = None
            self.stcs = None
            return pn.pane.Markdown('Provide the name or identifier of an object to search for.')
        times = {'start': self.start_time.value, 'stop': self.stop_time.value, 'step': self.time_step.value}
        if not check_times(times, maximum_date_range=30):
            self.eph = None
            self.stcs = None
            return pn.pane.Markdown('Invalid date strings (Year-month-day) or time range exceeds maximum (30 days).')
        try:
            radius = float(self.radius.value)
            location = self.location.value
            if location.lower() == 'none':
                location = None
            self.eph = get_path(self.obj_name.value, times, id_type=self.id_type.value, location=location)
            self.stcs = convert_path_to_polygon(self.eph, radius=radius)
            self.results = None
        except ValueError as e:
            return pn.pane.Markdown(f'{e}')

        # Display results, if available
        if self.eph is not None and len(self.eph) > 0:
            cols = self.eph_col_choice.value
            if self.data_tables:
                html = self.eph[cols].to_pandas().to_html(index=False, classes=['table', 'panel-df'])
                return pn.pane.HTML(html + self.script, sizing_mode='stretch_width')
            else:
                return self.eph[cols].show_in_notebook(display_length=10)
        else:
            return pn.pane.Markdown('No results found.')

    @param.depends('tap_button', 'full_run')
    def get_mast(self):
        if self.eph is None or self.stcs is None:
            return pn.pane.Markdown('Fetch ephemerides first and then run the MAST query.')
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
            self.results = clean_up_results(temp_results, obj_name=self.obj_name.value, orig_eph=self.eph,
                                            id_type=self.id_type.value, location=location, radius=self.radius.value,
                                            aggressive_check=self.time_check.value)
        except Exception as e:
            return pn.pane.Markdown(f'{e}')

        # Display results, if available
        if self.results is not None and len(self.results) > 0:
            cols = self.mast_col_choice.value
            if self.data_tables:
                html = self.results[cols].to_pandas().to_html(index=False, classes=['table', 'panel-df'])
                return pn.pane.HTML(html + self.script, sizing_mode='stretch_width')
            else:
                return self.results[cols].show_in_notebook(display_length=10)
        else:
            return pn.pane.Markdown('No results found.')

    @param.depends('stcs')
    def fetch_stcs(self):
        if self.stcs is None:
            return pn.pane.Markdown('## Fetch ephemerides first.')
        p = polygon_bokeh(self.stcs, display=False)
        return pn.Column(pn.pane.Markdown(f'STCS Polygon:  \n```{self.stcs}```'),
                         pn.pane.Bokeh(p))

    @param.depends('product_button')
    def get_products(self):
        if self.eph is None or self.results is None:
            return pn.pane.Markdown('Fetch ephemerides first and then run the MAST query.')
        if len(self.results) == 0:
            return pn.pane.Markdown(f'No MAST results to get.')
        if self.obs_ids.value is None or self.obs_ids.value == '':
            return pn.pane.Markdown(f'No observations selected.')
        file_list = get_files(self.results, self.obs_ids.value)

        # Display results, if available
        if file_list is not None and len(file_list) > 0:
            cols = self.product_col_choice.value
            if self.data_tables:
                # file_list['Download'] = [f'<a href="https://mast.stsci.edu/portal/api/' \
                #                          f'v0.1/Download/file?uri={x}">Download</a>'
                #                          for x in file_list['dataURI']]
                # cols = ['Download'] + cols
                html = file_list[cols].to_pandas().to_html(index=False, classes=['table', 'panel-df'])
                return pn.pane.HTML(html + self.script, sizing_mode='stretch_width')
            else:
                return file_list[cols].show_in_notebook(display_length=10)
        else:
            return pn.pane.Markdown('No results found.')

    @param.depends('eph', 'stcs', 'results')
    def mast_figure(self):
        if self.eph is None or self.results is None:
            return pn.pane.Markdown('Fetch ephemerides first and then run the MAST query.')
        if len(self.results) == 0:
            return pn.pane.Markdown(f'No MAST results to display.')
        try:
            p = mast_bokeh(self.eph, self.results, self.stcs, display=False)
        except Exception as e:
            return pn.pane.Markdown(f'{e}')
        return pn.pane.Bokeh(p)

    # Panel displays
    def additional_parameters(self):
        return pn.Column(self.time_step, self.max_rec, self.mission, self.radius, self.location, self.time_check)

    def panel(self, debug=False):
        title = pn.pane.Markdown("""
        # Search MAST for Moving Targets  
        
        This uses the [JPL Horizons service](https://ssd.jpl.nasa.gov/horizons.cgi) to resolve the target to 
        generate an ephemerides that will be used to query for observations 
        in the [MAST archive](https://mast.stsci.edu/). 
        
        Here are some interesting examples:  
        <br>
        
        |  Target  | Start Date &nbsp; &nbsp; &nbsp; | End Date &nbsp; &nbsp; &nbsp; | Type |
        |:---:|:---:|:---:|:---:|
        | (5) Jupiter | 1995-07-17 | 1995-07-30 | majorbody &nbsp; &nbsp; |
        | (42573) 1997 AN1 | 2019-02-02 | 2019-02-28 | smallbody &nbsp; &nbsp; |
        
        <br>
        Find the code for this on [GitHub](https://github.com/dr-rodriguez/MovingMast)
        
        ![](https://img.shields.io/badge/Made%20at-%23AstroHackWeek-8063d5.svg?style=flat)
        """
                                 )
        row1 = pn.Row(self.obj_name, self.id_type)
        row2 = pn.Row(self.start_time, self.stop_time)
        button_row = pn.Row(self.param['full_run'])
        output_tabs = pn.Tabs(('Ephemerides', pn.Column(self.eph_col_choice,
                                                        self.get_ephem, width=self.width, sizing_mode='stretch_width')),
                              ('MAST Results', pn.Column(self.mast_col_choice,
                                                         self.get_mast, width=self.width, sizing_mode='stretch_width')),
                              ('MAST Plot', self.mast_figure),
                              ('MAST Files', pn.Column(self.obs_ids, self.product_col_choice,
                                                       self.param['product_button'],
                                                       self.get_products, width=self.width, sizing_mode='stretch_width')),
                              ('Additional Parameters', self.additional_parameters)
                              )
        if debug:
            output_tabs.append(('Debug', pn.Column(self.param['ephem_button'],
                                                   self.param['tap_button'],
                                                   self.fetch_stcs, width=self.width, sizing_mode='stretch_width')
                                )
                               )

        # gspec = pn.GridSpec(sizing_mode='stretch_both')
        # gspec[:1, :3] = title
        # gspec[2, :3] = row1
        # gspec[3, :3] = row2
        # gspec[4, :3] = button_row
        # gspec[5, :3] = output_tabs
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
