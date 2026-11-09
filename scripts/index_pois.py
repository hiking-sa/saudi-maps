# يضيف ملفات الأماكن وحدود كل منطقة للفهرس
import json, sys, os, datetime
idxp, outdir = sys.argv[1], sys.argv[2]
try: idx = json.load(open(idxp, encoding="utf-8"))
except Exception: idx = {}
idx.setdefault("v", 1); idx.setdefault("regions", {})
bb = json.load(open(f"{outdir}/_bbox.json"))
today = datetime.date.today().isoformat()
for fn in sorted(os.listdir(outdir)):
    if not fn.endswith(".json") or fn.startswith("_"): continue
    k = fn[:-5]; p = f"{outdir}/{fn}"
    n = json.load(open(p, encoding="utf-8"))["n"]
    r = idx["regions"].setdefault(k, {"name": k})
    r["pois"] = {"file": f"pois/{fn}", "size": os.path.getsize(p), "n": n, "updated": today}
    if k in bb: r["bbox"] = [round(v, 4) for v in bb[k]]
idx["updated"] = today
json.dump(idx, open("index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v.get("pois", {}).get("n") for k, v in idx["regions"].items()})
