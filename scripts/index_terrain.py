# يضيف ملفات التضاريس لفهرس الخرائط
import json, sys, os, hashlib, datetime
idxp, outdir = sys.argv[1], sys.argv[2]
try: idx = json.load(open(idxp, encoding="utf-8"))
except Exception: idx = {}
idx.setdefault("v", 1); idx.setdefault("regions", {})
def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
today = datetime.date.today().isoformat()
for fn in sorted(os.listdir(outdir)):
    if not fn.endswith(".pmtiles"): continue
    k, kind = fn[:-8].rsplit("-", 1)   # asir-dem / asir-contours
    r = idx["regions"].setdefault(k, {"name": k})
    t = r.setdefault("terrain", {})
    p = f"{outdir}/{fn}"
    t[kind] = {"file": f"terrain/{fn}", "size": os.path.getsize(p), "md5": md5(p), "updated": today}
    if "terrain" not in r.get("layers", []): r.setdefault("layers", ["base"]).append("terrain")
idx["updated"] = today
json.dump(idx, open("index.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v.get("terrain") for k, v in idx["regions"].items() if v.get("terrain")}, ensure_ascii=False, indent=1))
