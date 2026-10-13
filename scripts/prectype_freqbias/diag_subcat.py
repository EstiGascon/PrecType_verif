"""
Check: which dataSubCategory reproduces the old Metview station count?
"""
import eccodes, numpy as np, pandas as pd
from pathlib import Path
from collections import defaultdict

BUFR = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/2023_48r1esuite/SYNOP_mannual_20230316.bufr')
AREA = [33,-11,71,35]; S,W,N,E=AREA; MISS=1e10

by_subcat = defaultdict(list)

with open(BUFR, 'rb') as f:
    while True:
        buf = eccodes.codes_bufr_new_from_file(f)
        if buf is None:
            break
        try:
            subcat = eccodes.codes_get(buf, 'dataSubCategory')
            eccodes.codes_set(buf, 'unpack', 1)
            lats = eccodes.codes_get_array(buf, 'latitude').astype(float)
            lons = eccodes.codes_get_array(buf, 'longitude').astype(float)
            hrs  = eccodes.codes_get_array(buf, 'hour').astype(float)
            lats[lats > MISS] = np.nan
            lons[lons > MISS] = np.nan
            try:
                wws = eccodes.codes_get_array(buf, 'presentWeather').astype(float)
                wws[wws > MISS] = np.nan
            except Exception:
                eccodes.codes_release(buf)
                continue  # skip messages without ww entirely
            n = len(lats)
            for i in range(n):
                if np.isnan(lats[i]) or not (S <= lats[i] <= N and W <= lons[i] <= E):
                    continue
                if hrs[i] != 0:
                    continue
                ww = wws[i] if len(wws) == n else wws[0]
                if np.isfinite(ww) and ww <= 100:
                    by_subcat[subcat].append((round(lats[i], 2), round(lons[i], 2)))
        except Exception:
            pass
        finally:
            eccodes.codes_release(buf)

gpt = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/SYN_Europe/SYN002_Europe/SYNOP_rain_20230316_0.gpt')
old = pd.read_csv(gpt, comment='#', sep=r'\s+', header=None,
                  names=['lat','lon','ht','date','time','value'])
pts_old = set(zip(old['lat'].round(2), old['lon'].round(2)))
print(f"Old stations: {len(pts_old)}")

running_pts = set()
for sc in sorted(by_subcat.keys()):
    pts = set(by_subcat[sc])
    running_pts |= pts
    print(f"subcat={sc:3d}: unique={len(pts):5d}, overlap_old={len(pts_old & pts):4d}, cumulative={len(running_pts)}")

print(f"\nAll subcats combined: {len(running_pts)}, overlap={len(pts_old & running_pts)}")
