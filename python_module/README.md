# Python Module

AtlasHDF gets a nice python module. But for now, it must be a slightly ugly one. Let me comment:

## The module

At the moment, the module implements three functions as a PoC

```
    .def("import_immediate", &AtlasHDF::import)
    .def("set_nodes_filter", &AtlasHDF::set_nodes_filter)
    .def("set_container", &AtlasHDF::set_container)
```
All of them support method chaining such that the following snippet works
```
x = atlashdf.AtlasHDF();
x.set_container("berlin.h5").set_nodes_filter("select(.ele!=null) | .").import_immediate("berlin-latest.osm.pbf")
```

Similarly, you can filter just some content to suppress unneeded attributes. For example, the following query
would suppress all attributes except elevation, but elevation would even have a good structure in the sense that the key will exist in all nodes (which was not true before), but can have a null value for those that did not have
the elevation key in the input:

```
set_nodes_filter("{\"ele\":.ele}")
```
Without this filter, the file `berlin.h5` starts like this:
```
>>> h5py.File("berlin.h5")["osm"]["nodes_attr"][:10]
array([[b'{"ele":"39.1"}'],
       [b'{}'],
       [b'{}'],
       [b'{}'],
       [b'{}'],
       [b'{"crossing":"uncontrolled","crossing:island":"yes","highway":"crossing","tactile_paving":"yes"}'],
       [b'{}'],
       [b'{}'],
       [b'{}'],
       [b'{"bus":"yes","name":"Londoner Stra\xc3\x9fe","public_transport":"stop_position","ref:BVG":"103010","website":
"https:\\/\\/qr.bvg.de\\/h103010"}']],                                                                                
      dtype=object)
```

But with this filter, it has the following structure:
```
>>> import h5py
>>> h5py.File("berlin.h5")["osm"]["nodes_attr"][:10]
array([[b'{"ele":"39.1"}'],
       [b'{"ele":null}'],
       [b'{"ele":null}'],
       [b'{"ele":null}'],
       [b'{"ele":null}'],
       [b'{"ele":null}'],
       [b'{"ele":null}'],
       [b'{"ele":null}'],
       [b'{"ele":null}'],
       [b'{"ele":null}']], dtype=object)
>>> 
```



## Usage and Roadmap

At the moment, filtering is enabled for the nodes, which does not make ultimate sense. Any JQ query across the
attributes is allowed. Any empty result `null` leads to omit of the nodes. This has to be extended to ways and
relations. In a common setting, JQ queries will first be used to suppress all elements that we are not interested in.

For example, a query on polygons could look like
```
select(.natural != null) | select(.natural == "water") | {"natural": .natural}
```
This example would select all polygons with a tag "natural==water" and then suppresses all other attributes by building
a new output object. In essence, if the "natural==water" is not present, it will suppress the whole polygon entry, if
it is there, the attributes will be `{"natural":"water"}` but can be extended in the query.

JQ is a beast, but the best beast I know. See [https://stedolan.github.io/jq/manual/v1.5/](https://stedolan.github.io/jq/manual/v1.5/)

We will have to extend this to ways and relations, but this is easy, I will do so soon.


## Development Decision

While jq and oniguruma should be embedded (to compile on Windows later), I decided not to make them submodules at the
moment as I had to even change the Makefile.am to compile them. I hope that this compilation can later by pythonized,
but it might not be so easy. Hence, we will (at least for Windows) have to cross-compile or compile independently.

jq and onig are the upstreams with just adding -fPIC to AM_LDFLAGS, AM_CFLAGS and AM_CPPFLAGS followed by an
```
autoreconf -vfi
./configure
make
```
This generates libraries that are explicitly added in `setup.py`.

If you have problem with non-relocatable code, triple-check your settings. And don't rebuild the lexer of JQ, especially not on Mac (they have an old bison).


## Requirements
- Install dependencies from Debian using apt

This depends on

- libosmpbf
- protobuf-lite
- zlib
- hdf5 (serial version)
