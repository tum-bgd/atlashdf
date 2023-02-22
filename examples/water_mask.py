import atlashdf
import atlashdf_rs
import rasterio
from PIL import Image


# -------------------------------------------------------------------------- #
# generate water container
# -------------------------------------------------------------------------- #
pbf_file = "../data/oberbayern-latest.osm.pbf"
h5_file = "../data/oberbayern-water.h5"

is_water_query = """
.waterway != null or .natural == "water" or .natural == "wetland" or .water != null or .landuse=="water" or .landcover=="water"
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
sentinel_file = "../data/Sentinel-2/Oberbayer_10m_3035_4bands.tif"
mask_file = "../data/oberbayern-water-mask.tif"

# read metadata
src = rasterio.open(sentinel_file)

bbox = list(src.bounds)
crs = "EPSG:3035"

# render mask
mask = atlashdf_rs.get_mask(
    width=src.width,
    height=src.height,
    bbox=bbox,
    bbox_crs=crs,
    collections=[f"{h5_file}/osm/ways_triangles", f"{h5_file}/osm/relations_triangles"],
    crs=crs,
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
