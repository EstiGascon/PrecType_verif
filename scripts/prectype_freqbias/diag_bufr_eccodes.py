"""
Fast BUFR diagnostic using eccodes directly.
1. Counts subsets per BUFR message type
2. Extracts lat/lon/hour from ALL messages (not just those with ww)
3. Compares against old Metview station list (.gpt)
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import eccodes

BUFR = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/2023_48r1esuite/SYNOP_mannual_20230316.bufr')
GPT_DIR = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/SYN_Europe/SYN002_Europe')
AREA = [33, -11, 71, 35]  # S, W, N, E
S, W, N, E = AREA

print(f"BUFR file: {BUFR}")
print(f"File size: {BUFR.stat().st_size / 1e6:.1f} MB")

# ── Read old Metview .gpt for hour=0 ─────────────────────────────────────────
gpt_file = GPT_DIR / 'SYNOP_rain_20230316_0.gpt'
if gpt_file.exists():
    old = pd.read_csv(gpt_file, comment='#', sep=r'\s+',
                      header=None, names=['lat','lon','ht','date','time','value'])
    pts_old = set(zip(old['lat'].round(2), old['lon'].round(2)))
    print(f"\nOld Metview stations (h=0): {len(pts_old)}")
else:
    pts_old = set()
    print(f"\nGPT file not found: {gpt_file}")

# ── Iterate BUFR messages with eccodes ───────────────────────────────────────
print("\n=== Scanning BUFR messages ===")
msg_types = {}   # dataCategory -> count
stations_all_h0 = []   # all (lat, lon, ww_or_nan) at h=0
stations_with_ww_h0 = []

with open(BUFR, 'rb') as f:
    msg_count = 0
    while True:
        try:
            buf_id = eccodes.codes_bufr_new_from_file(f)
        except eccodes.CodesInternalError:
            break
        if buf_id is None:
            break

        msg_count += 1
        try:
            cat = eccodes.codes_get(buf_id, 'dataCategory')
            n_subsets = eccodes.codes_get(buf_id, 'numberOfSubsets')
            msg_types[cat] = msg_types.get(cat, 0) + n_subsets

            # Unpack to access values
            eccodes.codes_set(buf_id, 'unpack', 1)

            try:
                lats = eccodes.codes_get_array(buf_id, 'latitude')
                lons = eccodes.codes_get_array(buf_id, 'longitude')
            except eccodes.CodesInternalError:
                eccodes.codes_release(buf_id)
                continue

            # Try to get hour
            try:
                hours = eccodes.codes_get_array(buf_id, 'hour')
            except eccodes.CodesInternalError:
                hours = np.full(len(lats), -1)

            # Try to get ww (presentWeather / 020003)
            try:
                wws = eccodes.codes_get_array(buf_id, 'presentWeather')
                has_ww = True
            except eccodes.CodesInternalError:
                wws = np.full(len(lats), np.nan)
                has_ww = False

            MISS = eccodes.CODES_MISSING_DOUBLE

            for i in range(len(lats)):
                lat = lats[i] if lats[i] != MISS else np.nan
                lon = lons[i] if lons[i] != MISS else np.nan
                hr  = int(hours[i]) if (len(hours) > 1 and hours[i] != eccodes.CODES_MISSING_LONG) else (int(hours[0]) if hours[0] != eccodes.CODES_MISSING_LONG else -1)
                ww  = wws[i] if (has_ww and wws[i] != MISS) else np.nan

                if np.isnan(lat) or np.isnan(lon):
                    continue
                if not (S <= lat <= N and W <= lon <= E):
                    continue
                if hr != 0:
                    continue

                stations_all_h0.append((round(lat, 2), round(lon, 2), ww))
                if has_ww and not np.isnan(ww):
                    stations_with_ww_h0.append((round(lat, 2), round(lon, 2), ww))

        except Exception as e:
            pass
        finally:
            eccodes.codes_release(buf_id)

print(f"Total BUFR messages: {msg_count}")
print(f"Subsets by dataCategory: {msg_types}")
print(f"\nStations in area at h=0 (eccodes ALL, incl no-ww) : {len(stations_all_h0)}")
print(f"Stations in area at h=0 (eccodes WITH ww)          : {len(stations_with_ww_h0)}")

pts_all = set((r,c) for r,c,_ in stations_all_h0)
pts_ww  = set((r,c) for r,c,_ in stations_with_ww_h0)

print(f"\nUnique lat/lon in eccodes ALL  : {len(pts_all)}")
print(f"Unique lat/lon in eccodes +ww  : {len(pts_ww)}")
if pts_old:
    print(f"\nOld ∩ eccodes ALL : {len(pts_old & pts_all)}")
    print(f"Old ∩ eccodes +ww : {len(pts_old & pts_ww)}")
    print(f"Old - eccodes ALL : {len(pts_old - pts_all)} (missing)")
    print(f"eccodes ALL - Old : {len(pts_all - pts_old)} (extra)")

# Sample some missing old stations
if pts_old and (pts_old - pts_all):
    missing = list(pts_old - pts_all)[:5]
    print(f"\nSample old stations NOT found by eccodes: {missing}")
if pts_all and (pts_all - pts_old):
    extra = list(pts_all - pts_old)[:5]
    print(f"Sample eccodes stations NOT in old:       {extra}")

print("\nDone.")
sys.stdout.flush()
