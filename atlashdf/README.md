# AtlasHDF

AtlasHDF is the central data management concept of Helena.

## Dependencies

- libhdf5-dev
- libboost-dev
- libosmpbf-dev

### Header-only (in tree)

- argparse.hpp: (<http://github.com/p-ranav/argparse>) Parsing command line arguments in a good way
- osmpbfreader.h (<https://github.com/hove-io/libosmpbfreader>) visitor interface for OSM PBF reading

### Development / Build

- make
- pkg-config

## Guiding Principles of the MVP

### Idea 1: Rely on existing, rock-solid storage technology with supercomputing support

It extends the well-established HDF library with needed metadata extensions and
spatial data types. It heavily relies on the principles of property maps in which objects and tables are stored as a primary table (e.g., points) and a set of additional tables of exactly the same shape. The row number connects these data spaces.

### Idea 2: Lineage and binding

As long as possible, all data input should come from one AtlasHDF container and go to the same or another AtlasHDF container. The lineage (how data has been created) is stored in the attributes of the fields as well.

### Idea 3: Embedded Object Store

Objects are represented as sets of JSON encoded strings. References to schemata can be put in HDF attributes. Attributes can be extracted into
property maps for further processing. These sets are stored using variable length string containers (usually).

### Idea 4: Iterators

We implement basic iterators on top of dataspaces that can be optimized (e.g., iterating over chunks, etc.). But especially, they make it
easy to implement sequential input and output.

### Idea 5: Embedded Program Code

For full reproducibility, we integrate source code or links to versioned source code repositories into the HDF container itself. Thereby, we gain data and code mobility. For running remotely, you transfer a single file holding the input data and the code. As a result, you get the same file extended (and have the option to programmatically drop input data). Data tables should be pruned by reshaping to zero rows (remember, that rows are our canonical primary key). Then, all metadata in attributes and the fact that this table existed survive and an output iterator to this
table is valid as the shape (except rows) is still correct.

## Idea 6: Randomized Worlds

We are expecting randomization to become more and more important, for example, randomly chosen parameters for machine learning pipelines or
the random nature of quantum measurements. Therefore, tables that are computed more than once (e.g., the prediction of an ML model under varying
parameters) are transparently shifted into a group of the same name.

## Components

### AtlasHDF: Python Library

```bash
from helena import AtlasHDF as h5py
```

AtlasHDF will be a wrapper around h5py with extensions. That is, all HDF5 code should be unbroken and import

### AtlasGateway: A simple OGC web services gateway

This first supports WMS and WCS and allows us to use QGIS or any other GIS for exploring AtlasHDF projects.
