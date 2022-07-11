# Thanks for writing this makefile Waitman Gobble <ns@waitman.net> 
CXX = g++

CXXFLAGS = `pkg-config --cflags hdf5` -IHighFive/include -O3 -std=c++17 -Wall #-Wextra

LDFLAGS = -lprotobuf-lite -losmpbf -lz `pkg-config --libs hdf5` 

PROGRAMS = helena

all: $(PROGRAMS)

helena: main.cpp osm_immediate.cpp 
	$(CXX) $(CXXFLAGS) -o $@ main.cpp osm_immediate.cpp $(LDFLAGS)

clean:
	rm -f *.o core $(PROGRAMS)

test:
	./helena import berlin-latest.osm.pbf berlin.h5
