# Functions to handle plotting

from bokeh.plotting import figure, output_file, show, output_notebook
from polygon import parse_s_region
from bokeh.models import Arrow, VeeHead
from bokeh.models import HoverTool
from bokeh.palettes import Spectral4
import matplotlib.pyplot as plt


def polygon_bokeh(stcs, display=True):
    patch_xs = parse_s_region(stcs)['ra']
    patch_ys = parse_s_region(stcs)['dec']

    p = figure(plot_width=700, x_axis_label="RA (deg)", y_axis_label="Dec (deg)")

    data = {'x': [patch_xs], 'y': [patch_ys]}
    p.patches('x', 'y', source=data, fill_alpha=0.1, line_color="black", line_width=0.5)

    p.add_layout(Arrow(end=VeeHead(line_color="black", line_width=1), line_width=2,
                       x_start=patch_xs[0], y_start=patch_ys[0], 
                       x_end=patch_xs[1], y_end=patch_ys[1]))

    p.x_range.flipped = True

    if display:
        output_notebook()
        show(p)
    else:
        return p
    

def quick_bokeh(stcs, outfile='test.html'):
    patch_xs = parse_s_region(stcs)['ra']
    patch_ys = parse_s_region(stcs)['dec']

    p = figure(plot_width=700)

    data = {'x': [patch_xs], 'y': [patch_ys]}
    p.patches('x', 'y', source=data, fill_alpha=0.1, line_color="black", line_width=0.5)

    p.y_range.flipped = True

    output_file(outfile)
    show(p)


def quick_plot(stcs):
    patch_xs = parse_s_region(stcs)['ra']
    patch_ys = parse_s_region(stcs)['dec']

    f, ax = plt.subplots(figsize=(8, 4))
    ax.scatter(patch_xs, patch_ys, edgecolors="black", marker='.', linestyle='None', s=50,
               facecolors='black')
    for i in range(len(patch_xs)):
        ax.text(patch_xs[i], patch_ys[i], str(i))
    plt.show()


def mast_bokeh(eph, mast_results, stcs=None, display=False):
    # Function to produce a Bokeh plot of MAST results with the target path

    p = figure(plot_width=700, x_axis_label="RA (deg)", y_axis_label="Dec (deg)")

    # Target path
    eph_data = {'eph_x': eph['RA'], 'eph_y': eph['DEC'], 'Date': eph['datetime_str']}
    eph_plot1 = p.line(x='eph_x', y='eph_y', source=eph_data, line_width=2,
                       line_color='black', legend=eph['targetname'][0])
    eph_plot2 = p.circle(x='eph_x', y='eph_y', source=eph_data, fill_color="black",
                         size=12, legend=eph['targetname'][0])
    p.add_tools(HoverTool(renderers=[eph_plot1, eph_plot2], tooltips=[('Date', "@Date")]))

    # Target footprint
    patch_xs = parse_s_region(stcs)['ra']
    patch_ys = parse_s_region(stcs)['dec']

    stcs_data = {'stcs_x': [patch_xs], 'stcs_y': [patch_ys]}
    p.patches('stcs_x', 'stcs_y', source=stcs_data, fill_alpha=0., line_color="grey", line_width=0.8,
              line_dash='dashed', legend='Search Area')

    # Prepare MAST footprints
    obsDF = mast_results.to_pandas()
    obsDF['coords'] = obsDF.apply(lambda x: parse_s_region(x['s_region']), axis=1)
    for col in mast_results.colnames:
        if isinstance(obsDF[col][0], bytes):
            obsDF[col] = obsDF[col].str.decode('utf-8')

    # Loop over missions, coloring each separately
    mast_plots = []
    for mission, color in zip(obsDF['obs_collection'].unique(), Spectral4):
        ind = obsDF['obs_collection'] == mission

        # Add patches with the observation footprings
        patch_xs = [c['ra'] for c in obsDF['coords'][ind]]
        patch_ys = [c['dec'] for c in obsDF['coords'][ind]]

        data = {'x': patch_xs, 'y': patch_ys, 'obs_collection': obsDF['obs_collection'][ind],
                'instrument_name': obsDF['instrument_name'][ind], 'obs_id': obsDF['obs_id'][ind],
                'target_name': obsDF['target_name'][ind], 'proposal_pi': obsDF['proposal_pi'][ind]}
        mast_plots.append(p.patches('x', 'y', source=data, legend=mission,
                                    fill_color=color, fill_alpha=0.1, line_color="white", line_width=0.5))

    # Add hover tooltip for MAST observations
    tooltip = [("instrument_name", "@instrument_name"),
               ("obs_id", "@obs_id"),
               ("target_name", "@target_name"),
               ('proposal_pi', '@proposal_pi')]
    p.add_tools(HoverTool(renderers=mast_plots, tooltips=tooltip))

    # Additional settings
    p.legend.click_policy = "hide"
    p.x_range.flipped = True

    if display:
        output_notebook()
        show(p)
    else:
        return p
