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
    if (a == "place_of_worship" or t.get("building") == "mosque") and t.get("religion", "muslim") in ("muslim", ""): return "pray"
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
PRAY_W = ("مسجد", "جامع", "مصلى", "mosque", "masjid", "masjed", "jami")
def ov_kind(c, name=""):
    c = (c or "").lower()
    nl = (name or "").lower()
    if any(w in nl for w in PRAY_W) and not any(w in c for w in ("store", "restaurant", "school", "shop")): return "pray"
    if "religious" in c and "muslim" in c: return "pray"
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
import re
def norm(n):
    n = re.sub("[\u064B-\u0652\u0640]", "", (n or "").lower())
    n = n.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    for w in ("مسجد", "جامع", "مصلى", "mosque", "masjid"): n = n.replace(w, "")
    return re.sub(r"[^\w]", "", n)
def dist(a, b, c, d): return 111320 * math.hypot(a - c, (b - d) * math.cos(math.radians(a)))
G = {}
def cell(lat, lng): return (round(lat / 0.0005), round(lng / 0.0005))
def near(k, lat, lng, r):
    cy, cx = cell(lat, lng)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            for q in G.get((k, cy + dy, cx + dx), ()):
                if dist(lat, lng, q[1], q[2]) < r: yield q
def add(r, p):
    P[r].append(p); cy, cx = cell(p[1], p[2]); G.setdefault((p[0], cy, cx), []).append(p)
no = 0
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
    if any(True for q in near(k, c[0], c[1], 30) if not q[3] or not name or norm(q[3]) == norm(name)): continue
    add(r, [k, round(c[0], 5), round(c[1], 5), name[:60], 0]); no += 1
nv = 0
if os.path.exists(ovf):
    for row in csv.DictReader(open(ovf, encoding="utf-8")):
        name = (row.get("name_ar") or row.get("name") or "").strip()
        k = ov_kind(row.get("cat"), name + " " + (row.get("name") or ""))
        if not k: continue
        try: lat, lng = float(row["lat"]), float(row["lon"])
        except Exception: continue
        nn = norm(name); dup = False
        for q in near(k, lat, lng, 120):
            dd = dist(lat, lng, q[1], q[2]); qn = norm(q[3])
            if dd < 15 or (nn and qn and (nn == qn or (len(nn) > 3 and (nn in qn or qn in nn)))) or (dd < 40 and (not nn or not qn)): dup = True; break
        if dup: continue
        r = region_of(lat, lng)
        if not r: continue
        add(r, [k, round(lat, 5), round(lng, 5), name[:60], 1]); nv += 1
today = datetime.date.today().isoformat(); stats = {}
for r, L in P.items():
    L.sort(key=lambda p: (p[0], p[1]))
    json.dump({"v": 1, "k": r, "updated": today, "n": len(L), "p": L}, open(f"{outdir}/{r}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    stats[r] = len(L)
json.dump({k: list(b) for k, (pg, b) in R.items()}, open(f"{outdir}/_bbox.json", "w"))
print("OSM:", no, "Overture:", nv, stats)
