# يطلع أسماء ملفات ارتفاعات Copernicus (30 متر) اللي تغطي حدود منطقة
import json, sys, math
geo, tilelist = sys.argv[1], sys.argv[2]
g = json.load(open(geo))["geometry"]; xs, ys = [], []
def walk(c):
    if isinstance(c[0], (int, float)): xs.append(c[0]); ys.append(c[1])
    else: [walk(i) for i in c]
walk(g["coordinates"])
b = 0.05; W, E, S, N = min(xs)-b, max(xs)+b, min(ys)-b, max(ys)+b
have = set(l.strip() for l in open(tilelist) if l.strip())
out = []
for lat in range(math.floor(S), math.ceil(N)):
    for lon in range(math.floor(W), math.ceil(E)):
        n = f"Copernicus_DSM_COG_10_{'N' if lat>=0 else 'S'}{abs(lat):02d}_00_{'E' if lon>=0 else 'W'}{abs(lon):03d}_00_DEM"
        if n in have: out.append(f"/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif")
print("\n".join(out))
print(f"{W} {S} {E} {N}", file=open("bbox.txt", "w"))
