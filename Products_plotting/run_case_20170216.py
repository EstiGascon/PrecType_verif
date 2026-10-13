"""Re-run the 16 Feb 2017 case: T+24 map + freezing-rain hotspot, then the 3-hourly meteogram there."""
import json

import matplotlib

matplotlib.use("Agg")
NB_DIR = "/home/moeg/PrecType_verif/Products_plotting"


def notebook_code(name: str) -> list[str]:
    nb = json.load(open(f"{NB_DIR}/{name}"))
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


code = notebook_code("ptype_most_likely_map.ipynb")
code[1] = code[1].replace('FDATE = "20240117"', 'FDATE = "20170216"').replace("STEPS = [3]", "STEPS = [24]")
assert '"20170216"' in code[1] and "STEPS = [24]" in code[1]
g = {}
for src in code:
    exec(src, g)
hot = g["hotspots"]
print(hot.to_string(), flush=True)
lat, lon, place = float(hot.loc[0, "lat"]), float(hot.loc[0, "lon"]), hot.loc[0, "nearest_place"]
country = hot.loc[0, "country"]

code = notebook_code("ptype_probability_meteogram.ipynb")
p = code[1]
p = p.replace('FDATE = (date.today() - timedelta(days=1)).strftime("%Y%m%d")', 'FDATE = "20170216"')
p = p.replace("MIN_STEP = 1 ", "MIN_STEP = 3 ")
p = p.replace("LAT, LON = 50.73, 7.1", f"LAT, LON = {lat}, {lon}")
p = p.replace('CITY, COUNTRY = "Bonn", "Germany"', f'CITY, COUNTRY = "near {place}", "{country}"')
assert '"20170216"' in p and "MIN_STEP = 3" in p and f"{lat}" in p
code[1] = p
g = {}
for src in code:
    exec(src, g)
df = g["df"]
print(df.loc[:"2017-02-19", [c for c in df.columns if (df[c] > 0).any()]].round(0).to_string(), flush=True)
