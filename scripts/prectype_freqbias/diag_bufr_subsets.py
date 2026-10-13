"""
Test: read BUFR with different column sets to understand which subsets pdbufr decodes.
"""
import sys, pdbufr
import numpy as np
import pandas as pd
from pathlib import Path

BUFR = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/2023_48r1esuite/SYNOP_mannual_20230316.bufr')
AREA = [71, -11, 33, 35]
N, W, S, E = AREA

def in_area(df):
    return df[(df['latitude']>=S)&(df['latitude']<=N)&(df['longitude']>=W)&(df['longitude']<=E)]

# ── Read 1: only lat/lon/hour/height (no ww requirement) ─────────────────────
print("=== READ 1: lat/lon/hour/height only (no presentWeather) ===")
df1 = pdbufr.read_bufr(str(BUFR), columns=('latitude','longitude','hour','heightOfStationGroundAboveMeanSeaLevel'))
sub1 = in_area(df1)
h0_1 = sub1[sub1['hour']==0]
print(f"  All hours in area : {len(sub1)}")
print(f"  At hour=0         : {len(h0_1)}")
print(f"  Unique lat/lon    : {len(set(zip(h0_1['latitude'].round(2), h0_1['longitude'].round(2))))}")

# ── Read 2: with presentWeather ───────────────────────────────────────────────
print("\n=== READ 2: with presentWeather ===")
df2 = pdbufr.read_bufr(str(BUFR), columns=('latitude','longitude','hour','heightOfStationGroundAboveMeanSeaLevel','presentWeather'))
sub2 = in_area(df2)
h0_2 = sub2[sub2['hour']==0]
print(f"  All hours in area : {len(sub2)}")
print(f"  At hour=0         : {len(h0_2)}")
print(f"  ww NaN at h=0     : {h0_2['presentWeather'].isna().sum()}")
print(f"  ww 0-99 at h=0    : {((h0_2['presentWeather']>=0)&(h0_2['presentWeather']<100)).sum()}")

# ── Compare station sets ──────────────────────────────────────────────────────
pts1 = set(zip(h0_1['latitude'].round(2), h0_1['longitude'].round(2)))
pts2 = set(zip(h0_2['latitude'].round(2), h0_2['longitude'].round(2)))

# Old .gpt stations
gpt_syn = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/SYN_Europe/SYN002_Europe')
old = pd.read_csv(gpt_syn/'SYNOP_rain_20230316_0.gpt', comment='#', sep=r'\s+',
                  header=None, names=['lat','lon','ht','date','time','value'])
pts_old = set(zip(old['lat'].round(2), old['lon'].round(2)))

print(f"\n=== Station set sizes ===")
print(f"  Old Metview   : {len(pts_old)}")
print(f"  pdbufr (no ww): {len(pts1)}")
print(f"  pdbufr (+ww)  : {len(pts2)}")
print(f"\n  Old ∩ pdbufr(no ww) : {len(pts_old & pts1)}")
print(f"  Old ∩ pdbufr(+ww)   : {len(pts_old & pts2)}")
print(f"  Old only (not in no-ww read): {len(pts_old - pts1)}")

# ── Check with very coarse rounding ──────────────────────────────────────────
pts1_1 = set(zip(h0_1['latitude'].round(1), h0_1['longitude'].round(1)))
pts_old_1 = set(zip(old['lat'].round(1), old['lon'].round(1)))
print(f"\n  With round(1): Old ∩ pdbufr(no ww) = {len(pts_old_1 & pts1_1)}")

# ── Show sample coords from each source ───────────────────────────────────────
print(f"\n  Sample old coords : {list(pts_old)[:5]}")
print(f"  Sample pdbufr(no ww) coords : {list(pts1)[:5]}")
