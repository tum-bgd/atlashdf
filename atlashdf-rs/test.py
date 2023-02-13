import atlashdf_rs
import rasterio
from PIL import Image

# print(atlashdf_rs.proj_info())

h5file = "/home/balthasar/git/atlashdf/data/oberbayern-water-earcut.h5"
tiff = "/home/balthasar/git/atlashdf/data/Sentinel-2/Oberbayer_10m_3035_4bands.tif"

# read tif metadata
src = rasterio.open(tiff)

bbox = list(src.bounds)
crs = "EPSG:3035"

# render mask
mask = atlashdf_rs.get_mask(width=src.width, height=src.height,
                            bbox=bbox, bbox_crs=crs,
                            collections=[f"{h5file}/osm/ways_triangles"],
                            crs=crs)
Image.fromarray(mask)

# save mask
mask = mask.astype("int8")
with rasterio.open(
    '../data/mask.tif',
    'w',
    driver='GTiff',
    height=src.height,
    width=src.width,
    count=1,
    dtype=mask.dtype,
    crs=src.crs,
    transform=src.transform,
    compress="JPEG",
) as dst:
    dst.write(mask, 1)
