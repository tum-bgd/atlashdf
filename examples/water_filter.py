"""
This script imports all water-related polygons in Berlin using
the atlashdf package.

Afterwards, triangulation is still done with the binary atlashdf program, but
can be embedded later.
"""

import atlashdf


# Query Construction following https://wiki.openstreetmap.org/wiki/DE:Map_Features#Wasserl%C3%A4ufe
#
# But query resolution is wrong. Selections are not sensible in import as they might suppress features.
# However, selection of relevant attributes makes sense.


attribute_selection_query = """
{"iswater":(.waterway != null or .natural == "water" or .water != null or .landuse=="water" or .landcover=="water")} 
"""

object_filter = """
select(.waterway != null or .natural == "water" or .water != null or .landuse=="water" or .landcover=="water")|. 
"""

pbf_file = "../data/berlin-latest.osm.pbf"
hdf_file = "../data/berlin.h5"

x = atlashdf.AtlasHDF()
x = (
    x.set_container(hdf_file)
    .set_filter("nodes", attribute_selection_query)
    .set_filter("ways", attribute_selection_query)
    .set_filter("relations", attribute_selection_query)
    .import_immediate(pbf_file)
    .clear_filters()
    .set_filter("relations", object_filter)
    .resolve("earcut")
)
