# يجهّز ملف أماكن لكل منطقة: من OpenStreetMap (osm.geojsonseq) ومن Overture Maps (ov.csv إن وُجد)
# الناتج: out/pois/<المنطقة>.json  →  {"v":1,"k":..,"updated":..,"n":..,"p":[[النوع, lat, lng, "الاسم", المصدر], ...]}
import json, sys, os, csv, datetime, math
from shapely.geometry import shape, Point
from shapely.prepared import prep
regdir, osmf, ovf, outdir = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(outdir, exist_ok=True)
R = {}
for r in json.load(open(f"{regdir}/_list.json", encoding="utf-8")):
    g = shape(json.load(open(f"{regdir}/{r['key']}.geojson", encoding="utf-8"))["geometry"])
    R[r["key"]] = (prep(g), g.bounds)
def region_of(lat, lng):
    pt = Point(lng, lat)
    for k, (pg, b) in R.items():
        if b[0] <= lng <= b[2] and b[1] <= lat <= b[3] and pg.contains(pt): return k
    return None
def osm_kind(t):
    a, s, n, tu, l = t.get("amenity", ""), t.get("shop", ""), t.get("natural", ""), t.get("tourism", ""), t.get("leisure", "")
    if a == "place_of_worship" and t.get("religion", "muslim") in ("muslim", ""): return "pray"
    if a in ("drinking_water", "water_point") or n == "spring" or t.get("man_made") == "water_well": return "water"
    if a == "toilets": return "wc"
    if a == "parking": return "park"
    if a in ("fuel", "charging_station"): return "fuel"
    if a in ("hospital", "clinic", "doctors"): return "hosp"
    if a == "pharmacy": return "pharm"
    if a in ("restaurant", "cafe", "fast_food", "food_court"): return "food"
    if s in ("supermarket", "convenience", "bakery", "greengrocer"): return "shop"
    if tu == "viewpoint": return "view"
    if n == "peak": return "peak"
    if tu in ("picnic_site", "camp_site") or a == "shelter" or l == "park": return "rest"
    if tu in ("hotel", "motel", "guest_house", "chalet", "resort"): return "hotel"
    return None
def ov_kind(c):
    c = (c or "").lower()
    if not c: return None
    if "mosque" in c or "muslim_place_of_worship" in c or c == "islamic_place_of_worship": return "pray"
    if "gas_station" in c or "fuel" in c or "ev_charging" in c: return "fuel"
    if "pharmacy" in c or "drugstore" in c or "drug_store" in c: return "pharm"
    if "hospital" in c or "clinic" in c or "medical_center" in c or "emergency_room" in c or "urgent_care" in c or "health_center" in c: return "hosp"
    if any(w in c for w in ("supermarket", "grocery", "convenience_store", "hypermarket", "food_and_beverage_store", "food_store")): return "shop"
    if any(w in c for w in ("restaurant", "cafe", "coffee", "bakery", "eatery", "burger", "pizza", "shawarma", "sandwich", "juice", "tea_room", "dessert", "fast_food")): return "food"
    if "parking" in c: return "park"
    if "toilet" in c or "restroom" in c: return "wc"
    if "drinking_water" in c or c == "water_well": return "water"
    if "scenic" in c or "lookout" in c or "viewpoint" in c: return "view"
    if c in ("park", "national_park", "picnic_area", "campground", "rest_area", "rest_stop", "nature_reserve") or "picnic" in c: return "rest"
    if c in ("hotel", "resort", "motel", "chalet", "guest_house", "holiday_rental_home", "inn", "lodge") or c.endswith("_hotel"): return "hotel"
    return None
P = {k: [] for k in R}
def centroid(geom):
    t = geom["type"]; c = geom["coordinates"]
    if t == "Point": return c[1], c[0]
    ring = c[0] if t == "Polygon" else c[0][0] if t == "MultiPolygon" else c if t == "LineString" else None
    if not ring: return None
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
    return sum(ys) / len(ys), sum(xs) / len(xs)
no = 0
SEEN = set()
for line in open(osmf, encoding="utf-8"):
    line = line.strip().lstrip("\x1e")
    if not line: continue
    f = json.loads(line); t = f.get("properties") or {}
    k = osm_kind(t)
    if not k: continue
    c = centroid(f["geometry"])
    if not c: continue
    r = region_of(*c)
    if not r: continue
    name = t.get("name:ar") or t.get("name") or ""
    if k == "peak" and t.get("ele"): name = (name + " · " if name else "") + str(t.get("ele")).split(".")[0] + " م"
    key = (k, round(c[0], 4), round(c[1], 4))
    if key in SEEN: continue
    SEEN.add(key)
    P[r].append([k, round(c[0], 5), round(c[1], 5), name[:60], 0]); no += 1
nv = 0
if os.path.exists(ovf):
    grid = {}
    for r, L in P.items():
        for i, p in enumerate(L): grid.setdefault((p[0], round(p[1], 3), round(p[2], 3)), []).append(p)
    for row in csv.DictReader(open(ovf, encoding="utf-8")):
        k = ov_kind(row.get("cat"))
        if not k: continue
        try: lat, lng = float(row["lat"]), float(row["lon"])
        except Exception: continue
        dup = False
        for dy in (-0.001, 0, 0.001):
            for dx in (-0.001, 0, 0.001):
                if grid.get((k, round(lat + dy, 3), round(lng + dx, 3))): dup = True
        if dup: continue
        r = region_of(lat, lng)
        if not r: continue
        name = (row.get("name_ar") or row.get("name") or "").strip()
        P[r].append([k, round(lat, 5), round(lng, 5), name[:60], 1]); nv += 1
today = datetime.date.today().isoformat(); stats = {}
for r, L in P.items():
    L.sort(key=lambda p: (p[0], p[1]))
    json.dump({"v": 1, "k": r, "updated": today, "n": len(L), "p": L}, open(f"{outdir}/{r}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    stats[r] = len(L)
json.dump({k: list(b) for k, (pg, b) in R.items()}, open(f"{outdir}/_bbox.json", "w"))
print("OSM:", no, "Overture:", nv, stats)
