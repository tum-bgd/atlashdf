import atlashdf_rs
import rasterio
from PIL import Image

print(atlashdf_rs.proj_info())

h5file = "/home/balthasar/git/atlashdf/data/oberbayern-water-earcut.h5"
tiff = "/home/balthasar/git/atlashdf/data/Sentinel-2/Oberbayer_10m_3035_4bands.tif"

src = rasterio.open(tiff)

bbox = list(src.bounds)
crs = "EPSG:3035"

mask = atlashdf_rs.get_mask(src.width, src.height, bbox, crs, [
                            f"{h5file}/osm/ways_triangles"], crs)

Image.fromarray(mask)
