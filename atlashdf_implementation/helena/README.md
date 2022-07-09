# Helena

Helena is the swiss army knife tool for AtlasHDF and the surrounding suite of GeoAI tools. In this directory, a basic version of helena is implemented in C++. Packages for Debian, Ubuntu and Windows binaries are generated later as well.

The helena tool functionalities (growing)

- helena import <osm file> <atlasgroup> --representation=immediate

We take care that all helena functions are implemented using plain C++11 data types and structures such
that it is easy to embed this into a python package (pybind11) at a later stage.

In addition, a Windows build is required, we will first try to stick with MXnet cross compilation
where I have quite good results in the past. An MSVC project should be created "at the end" as well hoping that the code changes are not too heavy. However, argparse is C++17 and I am not up to date with MS support.



# Dependencies / Libraries


## Header-Only 	 

- argparse.hpp: (upstream link!) Parsing command line arguments in a good way (C++11)
- osmpbfreader.h (https://github.com/hove-io/libosmpbfreader) visitor interface for OSM PBF reading

## Libraries

- libosmpbf (apt-get install libosmpbf-dev, MXE to be done)

## Submodules

- libosmpbf would be a candidate to submodule