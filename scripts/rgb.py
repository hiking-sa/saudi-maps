# يحوّل ملف الارتفاعات إلى ألوان بترميز terrain-rgb (الارتفاع = -10000 + (R*65536 + G*256 + B) * 0.1)
import sys
import numpy as np
from osgeo import gdal
src = gdal.Open(sys.argv[1]); b = src.GetRasterBand(1); nd = b.GetNoDataValue()
xs, ys = src.RasterXSize, src.RasterYSize
out = gdal.GetDriverByName("GTiff").Create(sys.argv[2], xs, ys, 4, gdal.GDT_Byte, options=["COMPRESS=DEFLATE", "TILED=YES", "BIGTIFF=YES"])
out.SetGeoTransform(src.GetGeoTransform()); out.SetProjection(src.GetProjection())
out.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
step = 1024
for y in range(0, ys, step):
    h = min(step, ys - y)
    a = b.ReadAsArray(0, y, xs, h).astype("float64")
    m = np.isnan(a) | (a == nd if nd is not None else False) | (a < -1000)
    v = np.round((np.where(m, 0, a) + 10000) * 10).astype(np.int64)
    for i, ch in enumerate([(v >> 16) & 255, (v >> 8) & 255, v & 255, np.where(m, 0, 255)]):
        out.GetRasterBand(i + 1).WriteArray(ch.astype(np.uint8), 0, y)
out.FlushCache(); out = None
print("rgb ok", xs, ys)
