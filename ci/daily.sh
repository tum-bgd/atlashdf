#!/bin/bash

# first step: get the planet
# Get the planet
rm -f planet-latest.osm.pbf

test -f planet-latest.osm.pbf || curl -L --output planet-latest.osm.pbf https://planet.osm.org/pbf/planet-latest.osm.pbf

# Get the software
rm -Rf hdf4water
git clone git@github.com:tumbgd/hdf4water.git

# compile in a subshell
pushd hdf4water/atlashdf_implementation/helena && make
popd
hdf4water/atlashdf_implementation/helena/helena import planet-latest.osm.pbf planet-latest.h5

# depends on
# sudo apt-get install make pkg-config libhdf5-dev libosmpbf-dev p
