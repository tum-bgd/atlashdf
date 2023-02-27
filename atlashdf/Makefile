# Thanks for writing this makefile Waitman Gobble <ns@waitman.net> 
CXX = g++

CXXFLAGS = `pkg-config --cflags hdf5` -I ../include -O3 -std=c++17 -Wall #-Wextra

LDFLAGS = -lprotobuf-lite -losmpbf -lz `pkg-config --libs hdf5`

all: clean setup build

setup:
	sudo apt-get update
	sudo apt-get install pkg-config libhdf5-dev libboost-dev libosmpbf-dev -y

build: main.cpp osm_immediate.cpp osm_resolvegeom.cpp 
	$(CXX) $(CXXFLAGS) -o atlashdf main.cpp osm_immediate.cpp osm_resolvegeom.cpp $(LDFLAGS)

clean:
	rm -f *.o atlashdf

test: build
	curl -C - -o "../data/berlin-latest.osm.pbf" --create-dirs "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf"
	./atlashdf import ../data/berlin-latest.osm.pbf ../data/berlin.h5
	./atlashdf resolve ../data/berlin.h5
	python3 ../examples/streets_sequential.py ../data/berlin.h5
	python3 ../tests/test_linestrings.py ../data/berlin.h5
