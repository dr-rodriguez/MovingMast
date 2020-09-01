# Functions to handle plotting

from bokeh.plotting import figure, output_file, show
from polygon import parse_s_region
import matplotlib.pyplot as plt


def quick_bokeh(stcs, outfile='test.html'):
    patch_xs = parse_s_region(stcs)['ra']
    patch_ys = parse_s_region(stcs)['dec']

    p = figure(plot_width=700)

    data = {'x': [patch_xs], 'y': [patch_ys]}
    p.patches('x', 'y', source=data, fill_alpha=0.1, line_color="black", line_width=0.5)

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
