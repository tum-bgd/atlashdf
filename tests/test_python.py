import atlashdf
import h5py

pbf_file = "../data/berlin-latest.osm.pbf"
hdf_file = "../data/berlin.h5"

# Test 1:
try:
    x = atlashdf.AtlasHDF()
    x.import_immediate(pbf_file)
except RuntimeError as e:
    if str(e) != "Run set_container before import":
        raise RuntimeError("TEST failed: set_container before import not enforced")
print("TEST PASSED")

# Test 2: a transformation of berlin

x = atlashdf.AtlasHDF()
x = (
    x.set_container(hdf_file)
    .set_filter("nodes", "select(.ele!=null) | .")
    .set_filter("ways", "select(.ele!=null) | .")
    .set_filter("relations", "select(.ele!=null) | .")
    .import_immediate(pbf_file)
)

h5py.File(hdf_file)["osm"]["nodes_attr"][:10]