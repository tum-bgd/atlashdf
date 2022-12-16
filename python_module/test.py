import atlashdf;

# Test 1:
try:
    x = atlashdf.AtlasHDF();
    x.import_immediate("berlin-latest.osm.pbf")
except RuntimeError as e:
    if str(e) != "Run set_container before import":
        raise RuntimeError("TEST failed: set_container before import not enforced")
print("TEST PASSED")
del(x)

# now a transformation of berlin

x = atlashdf.AtlasHDF();
x = (x.set_container("berlin.h5")
     .set_filter("nodes","select(.ele!=null) | .")
     .set_filter("ways","select(.ele!=null) | .")
     .set_filter("relations","select(.ele!=null) | .")
     .import_immediate("berlin-latest.osm.pbf")
     )


