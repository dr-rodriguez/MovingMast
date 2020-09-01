import numpy as np
from target import get_path, convert_path_to_polygon
from polygon import parse_s_region, check_direction, reverse_direction
from mast_tap import run_tap_query
import matplotlib.pyplot as plt
from bokeh.plotting import figure, output_file, show


eph = get_path('599', times={'start':'2010-01-01', 'stop':'2010-01-10', 'step':'1d'})
radius=0.0083
stcs = convert_path_to_polygon(eph)

if not check_direction(stcs):
    print('Reversing')
    stcs = reverse_direction(stcs)

patch_xs = parse_s_region(stcs)['ra']
patch_ys = parse_s_region(stcs)['dec']


# Bokeh
tools = 'pan, box_zoom, wheel_zoom, save, reset, resize'
p = figure(plot_width=700)

data = {'x': [patch_xs], 'y': [patch_ys]}
p.patches('x', 'y', source=data, fill_alpha=0.1, line_color="black", line_width=0.5)

output_file("test.html")
show(p)

# Matplotlib
f, ax = plt.subplots(figsize=(8, 4))
ax.scatter(patch_xs, patch_ys, edgecolors="black", marker='.', linestyle='None', s=50,
           facecolors='black')
for i in range(len(patch_xs)):
    ax.text(patch_xs[i], patch_ys[i], str(i))
plt.show()

# Mast results
results = run_tap_query(stcs, start_time=None, end_time=None, maxrec=100)
print(results)
