"""
Diagnostic: compare new Python pipeline output vs old Metview/.gpt pipeline
for a single date/step to identify the source of FBI value differences.
"""
import sys
sys.path.insert(0, '/home/moeg/PrecType_verif')
import numpy as np
import pandas as pd
from pathlib import Path
from utils import read_synop_df, extract_synop_arrays_df, apply_orog_filter, build_orog_filter
import config as _cfg

DATE = "20230316"   # mid-period date covered by both pipelines
STEP = 0
AREA = [71, -11, 33, 35]
OROG_THR = 200
N, W, S, E = AREA

def read_gpt(path):
    return pd.read_csv(path, comment='#', sep=r'\s+', header=None,
                       names=['lat','lon','ht','date','time','value'])

gpt_mod = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/ENS_Europe/ENS002_Europe')
gpt_syn = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite/SYN_Europe/SYN002_Europe')

# ── OLD pipeline ──────────────────────────────────────────────────────────────
old_syn  = read_gpt(gpt_syn / f'SYNOP_rain_{DATE}_{STEP}.gpt')
old_mod  = read_gpt(gpt_mod / f'Loc_rain_{DATE}_{STEP}.gpt')
old_n    = len(old_syn)
old_obs  = (old_syn['value'] == 1).sum()
old_prob_mean = old_mod['value'].mean()    # mean % probability across stations
old_prob_nonzero = (old_mod['value'] > 0).sum()
print(f"=== OLD pipeline ({DATE} step={STEP}) ===")
print(f"  Stations : {old_n}")
print(f"  Rain obs : {old_obs}  ({old_obs/old_n*100:.1f}%)")
print(f"  Model prob (%) mean={old_prob_mean:.2f}, nonzero={old_prob_nonzero}/{old_n}")

# FBI old-style: expand each station to 51 binary members, then sum hits/misses
n_mem = 51
a, b, c = 0, 0, 0
for i in range(old_n):
    prob_pct = min(old_mod['value'].iloc[i], 100)
    n_yes = round(prob_pct * n_mem / 100)
    syn_val = old_syn['value'].iloc[i]
    a += n_yes * syn_val
    b += n_yes * (1 - syn_val)
    c += (n_mem - n_yes) * syn_val
old_fbi = (a + b) / (a + c) if (a + c) > 0 else np.nan
print(f"  FBI (old formula): {old_fbi:.3f}")

# ── NEW pipeline ──────────────────────────────────────────────────────────────
parquet = Path(f'/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/2023_48r1esuite/SYNOP_mannual_{DATE}.parquet')
df      = read_synop_df(parquet)
arrays  = extract_synop_arrays_df(df, STEP, AREA)
orog_tree, orog_vals = build_orog_filter(_cfg.PATH_OROG)
obs_new = apply_orog_filter(arrays, OROG_THR, orog_tree, orog_vals)
new_n   = len(obs_new)
rain_codes = set(_cfg.SYNOP_CODES['rain'])
new_obs_vec = np.array([1 if int(w) in rain_codes else 0 for w in obs_new['ww']])
new_obs = new_obs_vec.sum()
print(f"\n=== NEW pipeline ({DATE} step={STEP}) ===")
print(f"  Stations : {new_n}")
print(f"  Rain obs : {new_obs}  ({new_obs/new_n*100:.1f}%)")

# ── Station spatial overlap ───────────────────────────────────────────────────
old_pts = set(zip(old_syn['lat'].round(2), old_syn['lon'].round(2)))
new_pts = set(zip(obs_new['lat'].round(2), obs_new['lon'].round(2)))
print(f"\n=== Station overlap ===")
print(f"  Old only : {len(old_pts - new_pts)}")
print(f"  New only : {len(new_pts - old_pts)}")
print(f"  Common   : {len(old_pts & new_pts)}")

# ── ww code distribution in new pipeline ────────────────────────────────────
print(f"\n=== NEW ww code distribution (all stations) ===")
ww_counts = pd.Series(obs_new['ww'].values.astype(int)).value_counts().sort_index()
print(ww_counts.to_string())

# ── ww code comparison: what's rain in old but not new, and vice versa ────────
old_rain_codes = {51,52,53,54,55,58,59,60,61,62,63,64,65,68,69,
                  80,81,82,87,88,89,90,91,92,93,94,95,96,97,99}
new_rain_codes = set(_cfg.SYNOP_CODES['rain'])
print(f"\n=== Rain ww code differences ===")
print(f"  In OLD but not NEW: {sorted(old_rain_codes - new_rain_codes)}")
print(f"  In NEW but not OLD: {sorted(new_rain_codes - old_rain_codes)}")

# ── Check for step-range coverage differences ────────────────────────────────
print(f"\n=== Step coverage check ===")
for step in [0, 3, 24, 27, 96, 99]:
    n_old_files = len(list(gpt_syn.glob(f'SYNOP_rain_{DATE}_{step}.gpt')))
    print(f"  step={step}: old gpt exists={bool(n_old_files)}")
print(f"  Old steps for {DATE}: {old_steps_avail}")

# ── Investigate the station gap ───────────────────────────────────────────────
# Old pipeline: 704 stations. New (ww<100): 383 stations. Gap = ~321.
# Question: are the missing stations ones with NaN ww in pdbufr, NaN ht,
# or stations that pdbufr doesn't decode at all?
df2 = read_synop_df(parquet)
sub = df2[
    (df2["hour"] == STEP) &
    (df2["lat"] >= S) & (df2["lat"] <= N) &
    (df2["lon"] >= W) & (df2["lon"] <= E)
].copy()
print(f"\n=== Raw parquet at hour={STEP}, in area: {len(sub)} rows ===")
print(f"  ww NaN        : {sub['ww'].isna().sum()}")
print(f"  ww valid 0-99 : {((sub['ww'] >= 0) & (sub['ww'] < 100)).sum()}")
print(f"  ww == 100     : {(sub['ww'] == 100).sum()}")
print(f"  ww 101-507    : {((sub['ww'] > 100) & (sub['ww'] < 508)).sum()}")
print(f"  ww 508-511    : {sub['ww'].isin([508,509,510,511]).sum()}")
print(f"  ht NaN        : {sub['ht'].isna().sum()}")
print(f"  ww valid 0-99 but NaN ht: {((sub['ww']>=0)&(sub['ww']<100)&sub['ht'].isna()).sum()}")

# Where do the old-only stations fall in the pdbufr data?
old_pts_ll = {(round(r.lat,2), round(r.lon,2)) for _, r in old_syn.iterrows()}
sub['latR'] = sub['lat'].round(2)
sub['lonR'] = sub['lon'].round(2)
sub['in_old'] = list(zip(sub['latR'], sub['lonR'])) 
sub['in_old'] = sub[['latR','lonR']].apply(lambda r: (r.latR, r.lonR) in old_pts_ll, axis=1)

# Of those 273 old-only stations, what does pdbufr say about them (if anything)?
old_only_ll = old_pts_ll - set(zip(obs_new['lat'].round(2), obs_new['lon'].round(2)))
sub_old_only = sub[sub[['latR','lonR']].apply(lambda r: (r.latR, r.lonR) in old_only_ll, axis=1)]
print(f"\n=== pdbufr data for the {len(old_only_ll)} 'old-only' stations ===")
print(f"  Found in parquet  : {len(sub_old_only)}")
if len(sub_old_only):
    print(f"  ww NaN            : {sub_old_only['ww'].isna().sum()}")
    print(f"  ww valid 0-99     : {((sub_old_only['ww']>=0)&(sub_old_only['ww']<100)).sum()}")
    print(f"  ww >= 100         : {(sub_old_only['ww']>=100).sum()}")
    print(f"  ht NaN            : {sub_old_only['ht'].isna().sum()}")
    print(f"  ww<100 & valid ht : {((sub_old_only['ww']>=0)&(sub_old_only['ww']<100)&sub_old_only['ht'].notna()).sum()}")
    # Show a few examples
    print(f"\n  Sample of old-only stations in parquet:")
    print(sub_old_only[['latR','lonR','ww','ht']].head(15).to_string())
else:
    print("  Not found in parquet at all → pdbufr doesn't decode these stations")
    # Check if they appear at other hours
    for other_h in [1, 2, 3, 6, 12, 18]:
        ll_sample = list(old_only_ll)[:5]
        found = df2[(df2['lat'].round(2).isin([x[0] for x in ll_sample])) &
                    (df2['hour'] == other_h)]
        if len(found):
            print(f"  Some found at hour={other_h}: {len(found)} rows")
            break


# ── Raw parquet inspection: height NaN, ww NaN ───────────────────────────────
df2 = read_synop_df(parquet)
sub = df2[
    (df2["hour"] == STEP) &
    (df2["lat"] >= S) & (df2["lat"] <= N) &
    (df2["lon"] >= W) & (df2["lon"] <= E)
]
print(f"\n=== Raw parquet at hour={STEP}, in area: {len(sub)} rows ===")
print(f"  ww NaN        : {sub['ww'].isna().sum()}")
print(f"  ht NaN        : {sub['ht'].isna().sum()}")
print(f"  ww valid 0-99 : {((sub['ww'] >= 0) & (sub['ww'] < 100)).sum()}")
print(f"  ww == 100     : {(sub['ww'] == 100).sum()}")
print(f"  ww > 100      : {(sub['ww'] > 100).sum()}")
print(f"  ww in 508-511 : {sub['ww'].isin([508,509,510,511]).sum()}")

# Stations with valid ww (0-99) but NaN height → dropped by our filter, maybe kept by Metview
valid_ww_nan_ht = sub[(sub['ww'] >= 0) & (sub['ww'] < 100) & sub['ht'].isna()]
print(f"  ww<100 but NaN ht (dropped by us): {len(valid_ww_nan_ht)}")

# Simulate ww<100 fix
ww_lt100 = sub[
    sub['ww'].notna() & (sub['ww'] < 100) &
    sub['ht'].notna() & sub['ww'].apply(lambda x: x not in [508,509,510,511])
]
rain_codes_set = set(_cfg.SYNOP_CODES['rain'])
print(f"\n=== After ww<100 fix (before orog filter): {len(ww_lt100)} stations ===")
print(f"  Rain obs: {ww_lt100['ww'].apply(lambda w: int(w) in rain_codes_set).sum()}")

# ── Check n_members in GRIB ───────────────────────────────────────────────────
from utils import load_ens_grib
import config as _cfg2
raw_dir = Path('/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/raw/raw_esuite48r1_2023')
grib = raw_dir / f'Prectype_raw_VERIF_{DATE}.grib'
prate = raw_dir / f'total_prec_VERIF_{DATE}.grib'
if grib.exists():
    pt, pr, steps, glats, glons = load_ens_grib(grib, 260015, 228219, prate_path=prate)
    s0 = steps == STEP
    print(f"\n=== GRIB at step={STEP}: {s0.sum()} member-fields ===")
    print(f"  Total fields in GRIB: {len(steps)}")
    print(f"  Unique steps: {sorted(set(steps.tolist()))[:10]} ...")

