# يحدّث فهرس الخرائط (index.json) اللي يقرأه التطبيق
import json, sys, os, hashlib, datetime
old, regdir, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
build = sys.argv[4] if len(sys.argv) > 4 else ""
try: idx = json.load(open(old, encoding="utf-8"))
except Exception: idx = {}
idx.setdefault("v", 1); idx.setdefault("regions", {})
meta = {r["key"]: r for r in json.load(open(f"{regdir}/_list.json", encoding="utf-8"))}
today = datetime.date.today().isoformat()
for fn in sorted(os.listdir(outdir)):
    if not fn.endswith(".pmtiles"): continue
    k = fn[:-8]; p = f"{outdir}/{fn}"; h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""): h.update(b)
    m = meta.get(k, {})
    idx["regions"][k] = {"name": m.get("name", k), "name_en": m.get("name_en", ""), "file": f"regions/{fn}",
                         "size": os.path.getsize(p), "md5": h.hexdigest(), "updated": today, "layers": ["base"], "schema": "protomaps", "source": build}
idx["updated"] = today
json.dump(idx, open("index.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(idx, ensure_ascii=False, indent=1))
