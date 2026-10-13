#!/usr/bin/env python3
"""
Build (or skip) the _v2.parquet cache for one BUFR file.
Usage: python3 build_one_parquet.py <bufr_path>
"""
import sys
from pathlib import Path

# Ensure utils is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils import read_synop_df, synop_parquet_path

bufr_path = Path(sys.argv[1])
cache = synop_parquet_path(bufr_path)

if cache.exists():
    print(f"SKIP (already exists): {cache.name}")
    sys.exit(0)

print(f"Building: {bufr_path.name} → {cache.name}", flush=True)
df = read_synop_df(bufr_path)
if df is None:
    print(f"ERROR: read_synop_df returned None for {bufr_path.name}")
    sys.exit(1)

print(f"OK: {len(df)} rows written to {cache.name}", flush=True)
