# يقسم حدود المناطق الإدارية (admin_level=4) من بيانات OSM إلى ملف GeoJSON لكل منطقة
import json, sys, os
KEYS = {"SA-01":"riyadh","SA-02":"makkah","SA-03":"madinah","SA-04":"eastern","SA-05":"qassim","SA-06":"hail",
        "SA-07":"tabuk","SA-08":"northern-borders","SA-09":"jazan","SA-10":"najran","SA-11":"baha","SA-12":"jouf","SA-14":"asir"}
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True); seen = {}
for line in open(src, encoding="utf-8"):
    line = line.strip().lstrip("\x1e")
    if not line: continue
    f = json.loads(line); p = f.get("properties") or {}
    iso = p.get("ISO3166-2", "")
    if p.get("admin_level") != "4" or iso not in KEYS: continue
    k = KEYS[iso]
    if k in seen: continue
    seen[k] = {"key": k, "iso": iso, "name": p.get("name:ar") or p.get("name", k), "name_en": p.get("name:en", "")}
    json.dump({"type":"Feature","properties":seen[k],"geometry":f["geometry"]}, open(f"{out}/{k}.geojson","w"), ensure_ascii=False)
json.dump(list(seen.values()), open(f"{out}/_list.json","w"), ensure_ascii=False)
print("المناطق:", len(seen), sorted(seen))
