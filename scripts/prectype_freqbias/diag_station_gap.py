"""
Diagnostic: understand exactly why old Metview pipeline has 704 stations
while new pdbufr pipeline has 331 for the same date/step.
Focus: what are the 485 'old-only' stations in the pdbufr data?
"""
import sys
sys.path.insert(0, '/home/moeg/PrecType_verif')
import numpy as np
import pandas as pd
from pathlib import Path
from utils import read_synop_df, build_orog_filter
import config as _cfg

DATE  = "20230316"
STEP  = 0           # obsfilter time=0 → hour=0
AREA  = [71, -11, 33, 35]
N, W, S, E = AREA

parquet = Path(f'/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/2023_48r1esuite/SYNOP_mannual_{DATE}.parquet')
gpt_syn = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/SYN_Europe/SYN002_Europe')

# ── Read old pipeline output (the Metview-produced station list) ──────────────
old_syn = pd.read_csv(gpt_syn / f'SYNOP_rain_{DATE}_{STEP}.gpt',
                      comment='#', sep=r'\s+', header=None,
                      names=['lat','lon','ht','date','time','value'])
old_pts = set(zip(old_syn['lat'].round(2), old_syn['lon'].round(2)))
print(f"Old pipeline stations : {len(old_syn)}")

# ── Read full pdbufr parquet ──────────────────────────────────────────────────
df = read_synop_df(parquet)
print(f"\n=== Full parquet: {len(df)} rows, hours: {sorted(df['hour'].unique())} ===")

# ── Check if old stations appear at OTHER hours in pdbufr ────────────────────
# (Metview obsfilter might use a looser time match)
all_hours_in_area = df[
    (df['lat'] >= S) & (df['lat'] <= N) &
    (df['lon'] >= W) & (df['lon'] <= E)
].copy()
all_hours_in_area['latR'] = all_hours_in_area['lat'].round(2)
all_hours_in_area['lonR'] = all_hours_in_area['lon'].round(2)
all_pts_any_hour = set(zip(all_hours_in_area['latR'], all_hours_in_area['lonR']))
print(f"\n=== Stations in area at ANY hour (pdbufr): {len(all_pts_any_hour)} ===")
print(f"Old-only found at any hour: {len(old_pts & all_pts_any_hour - (old_pts & set(zip(all_hours_in_area[all_hours_in_area['hour']==STEP]['latR'], all_hours_in_area[all_hours_in_area['hour']==STEP]['lonR']))))}")

# More clearly: which old-only stations appear in pdbufr at hour!=0?
at_h0 = all_hours_in_area[all_hours_in_area['hour'] == STEP]
at_h0_pts = set(zip(at_h0['latR'], at_h0['lonR']))
old_only_from_hour0 = old_pts - at_h0_pts

in_other_hour = old_pts & (all_pts_any_hour - at_h0_pts)
print(f"Old-only stations found in pdbufr at hour != {STEP}: {len(in_other_hour)}")
if in_other_hour:
    sample = list(in_other_hour)[:5]
    for pt in sample:
        rows = all_hours_in_area[(all_hours_in_area['latR']==pt[0]) & (all_hours_in_area['lonR']==pt[1])]
        print(f"  lat={pt[0]} lon={pt[1]}: hours={sorted(rows['hour'].unique())}, ww={rows['ww'].values}")

# ── Stations completely absent from pdbufr ───────────────────────────────────
completely_absent = old_pts - all_pts_any_hour
print(f"\nOld-only stations NOT in pdbufr at all (any hour): {len(completely_absent)}")
# Show a few so we can investigate
print(f"  Sample coords: {list(completely_absent)[:10]}")

# ── What hour does pdbufr assign to the old-only stations? ───────────────────
print(f"\n=== Hour distribution for old-pipeline stations in pdbufr ===")
found_rows = all_hours_in_area[all_hours_in_area[['latR','lonR']].apply(
    lambda r: (r.latR, r.lonR) in old_pts, axis=1)]
print(f"  Total old-station rows in pdbufr (any hour): {len(found_rows)}")
print(f"  Hour distribution:\n{found_rows['hour'].value_counts().sort_index().to_string()}")

# ── Specifically at hour=0: what ww/ht are the old-only stations? ─────────────
at_h0_old = at_h0[at_h0[['latR','lonR']].apply(
    lambda r: (r.latR, r.lonR) in old_pts, axis=1)]
print(f"\n=== Old-pipeline stations at hour=0 in pdbufr: {len(at_h0_old)} ===")
print(f"  ww NaN   : {at_h0_old['ww'].isna().sum()}")
print(f"  ww 0-99  : {((at_h0_old['ww']>=0)&(at_h0_old['ww']<100)).sum()}")
print(f"  ww >=100 : {(at_h0_old['ww']>=100).sum()}")
print(f"  ht NaN   : {at_h0_old['ht'].isna().sum()}")

# ── After orog filter: how many old stations pass? ───────────────────────────
orog_tree, orog_vals = build_orog_filter(_cfg.PATH_OROG)
from scipy.spatial import cKDTree
grid_lats = orog_tree.data[:, 0] if hasattr(orog_tree, 'data') else None

# Apply the same orog filter to all old stations present in pdbufr at h=0
at_h0_old_valid = at_h0_old[
    at_h0_old['ww'].notna() & (at_h0_old['ww'] < 100) & at_h0_old['ht'].notna()
]
if len(at_h0_old_valid):
    coords = np.deg2rad(np.column_stack([at_h0_old_valid['lat'], at_h0_old_valid['lon']]))
    _, idx = orog_tree.query(coords)
    orog_at_st = orog_vals[idx]
    ht_vals = at_h0_old_valid['ht'].values
    orog_ok = np.abs(ht_vals - orog_at_st) < 200
    print(f"\n=== Old stations (at h=0, ww<100, ht valid) passing orog filter: {orog_ok.sum()}/{len(at_h0_old_valid)} ===")
