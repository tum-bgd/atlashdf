# Thanks for writing this makefile Waitman Gobble <ns@waitman.net> 
CXX = g++

CXXFLAGS = `pkg-config --cflags hdf5` -I HighFive/include -O3 -std=c++17 -Wall #-Wextra

LDFLAGS = -lprotobuf-lite -losmpbf -lz `pkg-config --libs hdf5` 

all: atlashdf

setup:
	sudo apt-get update
	sudo apt-get install pkg-config libhdf5-dev libboost-dev libosmpbf-dev -y


atlashdf: main.cpp osm_immediate.cpp osm_resolvegeom.cpp 
	$(CXX) $(CXXFLAGS) -o $@ main.cpp osm_immediate.cpp osm_resolvegeom.cpp $(LDFLAGS)

clean:
	rm -f *.o core atlashdf

test: atlashdf
	curl -C - -o "../data/berlin-latest.osm.pbf" --create-dirs "https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf"
	./atlashdf import ../data/berlin-latest.osm.pbf ../data/berlin.h5
