# يجمع مربعات الصور (z/x/y.png) في ملف mbtiles واحد
import sys, os, sqlite3
d, out, name = sys.argv[1], sys.argv[2], sys.argv[3]
if os.path.exists(out): os.remove(out)
c = sqlite3.connect(out)
c.executescript("CREATE TABLE metadata(name text, value text); CREATE TABLE tiles(zoom_level integer, tile_column integer, tile_row integer, tile_data blob); CREATE UNIQUE INDEX t ON tiles(zoom_level,tile_column,tile_row);")
zs = []; n = 0
for z in sorted(os.listdir(d)):
    if not z.isdigit(): continue
    zi = int(z); zs.append(zi)
    for x in os.listdir(f"{d}/{z}"):
        if not x.isdigit(): continue
        for f in os.listdir(f"{d}/{z}/{x}"):
            if not f.endswith(".png"): continue
            y = int(f[:-4]); data = open(f"{d}/{z}/{x}/{f}", "rb").read()
            c.execute("INSERT INTO tiles VALUES(?,?,?,?)", (zi, int(x), (1 << zi) - 1 - y, data)); n += 1
meta = {"name": name, "format": "png", "type": "baselayer", "minzoom": str(min(zs)), "maxzoom": str(max(zs)), "encoding": "mapbox", "attribution": "Copernicus DEM GLO-30 © DLR/ESA"}
c.executemany("INSERT INTO metadata VALUES(?,?)", meta.items()); c.commit(); c.close()
print("tiles", n, "zooms", min(zs), max(zs))
