# Take a debian that fits your machine
# Be prepared to update the installation of protobuflite which contains a version.

FROM debian:9

#
# This container is for building only. Output wheels are in /atlashdf/dist
# You should mount it
# But you can also just run the container and inspect what you have

RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    automake \
    autoconf \
    git\
    ca-certificates\
    libtool\
    make \
    && apt-get clean &&  rm -rf /var/lib/apt/lists/*


# Check out upstream

RUN git config --global pull.ff only && \
    git clone https://github.com/tum-bgd/atlashdf.git && cd atlashdf && \
    git checkout pythonmodule

# Build JQ

WORKDIR /atlashdf/python_module/jq
RUN autoreconf -vfi
# --disable-dependency-tracking
RUN ./configure --disable-maintainer-mode 
RUN make


# Prepare for more AtlasHDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    python3-setuptools \
    python3-pip \       
    libosmpbf-dev \
    libprotobuf-dev \
    libprotobuf-lite32 \
    libhdf5-dev \
    libboost-dev \
    && apt-get clean &&  rm -rf /var/lib/apt/lists/*

RUN pip3 install pybind11

WORKDIR /atlashdf/python_module
RUN python3 setup.py bdist_wheel

# Now, the wheel is in /atlashdf/python_module/dist and can be copied by running a container and mounting:
# in@martin:~/2023work/atlashdf/python_module$ docker run -it -v dist:/out atlashdfbuilder                           
# root@f029b3ad9157:/atlashdf/python_module# cp dist/atlashdf-0.1-cp39-cp39-linux_x86_64.whl /out
# root@f029b3ad9157:/atlashdf/python_module# exit
#
# Then, you can install this beast (but be sure to have all shared objects or use auditwheel to repair it)
