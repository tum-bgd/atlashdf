import atlashdf
import urllib.request
import os

if __name__=="__main__":

    # Ensure, we have a file
    if not os.path.exists("oberbayern-latest.osm.pbf"):
        print("Downloading Oberbayern")
        urllib.request.urlretrieve("https://download.geofabrik.de/europe/germany/bayern/oberbayern-latest.osm.pbf", "oberbayern-latest.osm.pbf")
    print("Using Oberbayern. Delete file for an update from the Internet")

    # Conversion Chain
    attribute_selection_query="""
{"iswater":(.waterway != null or .natural == "water" or .natural == "wetland" or .water != null or .landuse=="water" or .landcover=="water")} 
"""

    object_filter="""
    select(.iswater)
"""


    x = atlashdf.AtlasHDF();
    x = (x.set_container("oberbayern-water-earcut.h5")
     .set_filter("nodes",attribute_selection_query)
     .set_filter("ways",attribute_selection_query) 
     .set_filter("relations",attribute_selection_query)
     .import_immediate("oberbayern-latest.osm.pbf")
     .clear_filters()
     .set_filter("ways",object_filter)
     .resolve("earcut")
     )

        

