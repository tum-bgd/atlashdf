CFLAGS=-Ofast -march=native

all:
	g++ -std=c++17 -c -o datasystem.o `pkg-config --cflags hdf5` -I ../include ${CFLAGS}  datasystem.cpp 
	g++ -std=c++17 -c -o viewer.o     viewer.cpp  `wx-config --cflags` ${CFLAGS}
	g++ -o viewer datasystem.o viewer.o `pkg-config --libs hdf5` -ldslab `wx-config --libs --gl-libs` -lGL -lGLU
clean:
	rm -f *.o viewer
