
from target import get_path, convert_path_to_polygon
from polygon import parse_s_region
from mast_tap import run_tap_query
import matplotlib.pyplot as plt
from bokeh.plotting import figure, output_file, show

obj_name = '599'  # 599 Luisa (A906 HF)
id_type = 'smallbody'
times = {'start': '2010-01-01', 'stop': '2010-01-10', 'step': '1d'}

# Jupiter WFC3 observations
obj_name = '5'
id_type = 'majorbody'
times = {'start': '2019-04-01', 'stop': '2019-04-10', 'step': '1d'}
eph = get_path(obj_name, id_type=id_type, times=times,location=None)
stcs = convert_path_to_polygon(eph)

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
ax.plot(patch_xs, patch_ys)
ax.scatter(patch_xs, patch_ys, edgecolors="black", marker='.', linestyle='solid', s=50, facecolors='black')
for i in range(len(patch_xs)):
    ax.text(patch_xs[i], patch_ys[i], str(i))
plt.show()
# plt.savefig('polygon.png')

# Mast results
start_time = min(eph['datetime_jd']) - 2400000.5
end_time = max(eph['datetime_jd']) - 2400000.5
# results = run_tap_query(stcs, start_time=None, end_time=None, maxrec=100)
results = run_tap_query(stcs, start_time=start_time, end_time=end_time, maxrec=100)
print(results)

# Using regions
from astropy.coordinates import SkyCoord
from regions import PixCoord, PolygonSkyRegion, PolygonPixelRegion
polygon_sky = PolygonSkyRegion(vertices=SkyCoord(patch_xs, patch_ys, unit='deg', frame='icrs'))

# Treating as pixels for simplicity (and since I have no WCS)
polygon_pix = PolygonPixelRegion(vertices=PixCoord(x=patch_xs, y=patch_ys))
PixCoord(eph['RA'][1], eph['DEC'][1]) in polygon_pix

fig, ax = plt.subplots(figsize=(8, 4))
patch = polygon_pix.as_artist(facecolor='none', edgecolor='red', lw=2)
ax.add_patch(patch)
plt.plot([eph['RA'][1]], [eph['DEC'][1]], 'ko')
plt.xlim(84.2, 81.4)
plt.ylim(41.2, 41.5)
