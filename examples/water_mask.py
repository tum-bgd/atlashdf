# -------------------------------------------------------------------------- #
# generate water container
# -------------------------------------------------------------------------- #
import atlashdf

pbf_file = "../data/bayern-latest.osm.pbf"
h5_file = "../data/bayern-water.h5"

is_water_query = """
.natural == "water" or .water != null  or .waterway != null or .landuse=="basin"
"""

x = atlashdf.AtlasHDF()
x = (
    x.set_container(h5_file)
    .import_immediate(pbf_file)
    .set_filter("ways", f"""select({is_water_query})""")
    .set_filter(
        "relations", f"""select(.type == "multipolygon" and ({is_water_query}))"""
    )
    .resolve("earcut")  # FIXME: surpress progress output which might break notebook
)


# -------------------------------------------------------------------------- #
# generate water mask
# -------------------------------------------------------------------------- #
import atlashdf_rs
import rasterio
from PIL import Image

print(atlashdf_rs.proj_info())  # may need to link proj binary

h5_file = "../data/bayern-water.h5"
sentinel_file = "../data/Sentinel-2/Oberbayer_10m_3035_4bands.tif"
mask_file = "../data/oberbayern-water-mask.tif"

# FIXME: set right projection (EPSG:3035)
from osgeo import gdal
import pyproj

ds = gdal.Open(sentinel_file, gdal.GA_Update)
ds.SetProjection(pyproj.CRS.from_epsg(3035).to_wkt())
ds = None

# read metadata
src = rasterio.open(sentinel_file)

# render mask
mask = atlashdf_rs.get_mask(
    width=src.width,
    height=src.height,
    bbox=list(src.bounds),
    bbox_crs=src.crs.to_string(),
    collections=[f"{h5_file}/osm/ways_triangles", f"{h5_file}/osm/relations_triangles"],
    crs=src.crs.to_string(),
)
Image.fromarray(mask)

# save mask
mask = mask.astype("int8")
with rasterio.open(
    mask_file,
    "w",
    driver="GTiff",
    height=src.height,
    width=src.width,
    count=1,
    dtype=mask.dtype,
    crs=src.crs,
    transform=src.transform,
    # compress="JPEG", // FIXME: generates pseudo classes which break the training task
) as dst:
    dst.write(mask, 1)
