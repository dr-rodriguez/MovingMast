
from target import get_path, convert_path_to_polygon
from polygon import parse_s_region
from mast_tap import run_tap_query, clean_up_results, get_files

location = None

# 599 Luisa (A906 HF)
obj_name = '599'
id_type = 'smallbody'
times = {'start': '2010-01-01', 'stop': '2010-01-10', 'step': '1d'}

# Jupiter WFC3 observations
obj_name = '5'
id_type = 'majorbody'
times = {'start': '2019-04-01', 'stop': '2019-04-10', 'step': '1d'}
# times = {'start': '1997-07-10', 'stop': '1997-07-15', 'step': '12h'}

eph = get_path(obj_name, id_type=id_type, times=times, location=location)
stcs = convert_path_to_polygon(eph)

# Mast results
start_time = min(eph['datetime_jd']) - 2400000.5
end_time = max(eph['datetime_jd']) - 2400000.5
# results = run_tap_query(stcs, start_time=None, end_time=None, maxrec=100)
results = run_tap_query(stcs, start_time=start_time, end_time=end_time, maxrec=100)
print(results)

filtered_results = clean_up_results(results, obj_name=obj_name, id_type=id_type, location=location)
print(filtered_results)

obs_id = 'odxc17r5q'
file_list = get_files(filtered_results, obs_id)

t = filtered_results.copy()
obs_list = obs_id.split(',')
mask = [x.decode() in obs_list for x in t['obs_id']]
# mask = [x in t['obs_id'] for x in obs_list]
t = t[mask]
data_products_by_id = Observations.get_product_list(t['obsID'].astype(str))


Observations.get_product_list(t_init[[x in obs_list for x in t_init["obs_id"]]])


# Using regions
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
from regions import PixCoord, PolygonSkyRegion, PolygonPixelRegion, CirclePixelRegion

patch_xs = parse_s_region(stcs)['ra']
patch_ys = parse_s_region(stcs)['dec']
polygon_sky = PolygonSkyRegion(vertices=SkyCoord(patch_xs, patch_ys, unit='deg', frame='icrs'))

# Treating as pixels for simplicity (and since I have no WCS)
polygon_pix = PolygonPixelRegion(vertices=PixCoord(x=patch_xs, y=patch_ys))
PixCoord(eph['RA'][1], eph['DEC'][1]) in polygon_pix
radius=0.0083
target_coords = PixCoord(eph['RA'][0], eph['DEC'][0])
target_circle = CirclePixelRegion(center=target_coords, radius=radius)
intersection = target_circle & polygon_pix
# intersection.area # not implemented yet

fig, ax = plt.subplots(figsize=(8, 4))
patch = polygon_pix.as_artist(facecolor='none', edgecolor='red', lw=2)
ax.add_patch(patch)
plt.plot([eph['RA'][1]], [eph['DEC'][1]], 'ko')
plt.xlim(84.2, 81.4)
plt.ylim(41.2, 41.5)
