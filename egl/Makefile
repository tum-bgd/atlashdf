CFLAGS=-Ofast -march=native
all:
	g++ -c  ${CFLAGS} -o prepare_ogl.o prepare_ogl.cpp -Wall `pkg-config --cflags --libs hdf5` -I ../include
	g++ -std=c++17 -o egl main.cpp prepare_ogl.o -lGLEW -lGL -lEGL -lGLU `pkg-config --cflags --libs hdf5` -I ../include ${CFLAGS}
