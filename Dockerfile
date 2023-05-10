# You may need to adapt this configuration in case you want to use this docker
# file to build a wheel for your system. Take a builder image that fits your machine
# and be prepared to update the installation of a matching protobuflite version.

FROM python:3.10.9-bullseye AS builder

# This stage is for building only. Output wheels are in `/atlashdf/dist`.
# You can mount it or run the container and inspect what you have.

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    sqlite3 \
    libclang-dev \
    libosmpbf-dev \
    libhdf5-dev \
    libboost-dev \
    && apt-get clean &&  rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"


WORKDIR /atlashdf

COPY ./ .

# Build atlashdf-rs wheel
RUN pip3 install maturin[patchelf]
RUN maturin build --release -m atlashdf-rs/Cargo.toml

# Build JQ
WORKDIR /atlashdf/python_module/jq
RUN autoreconf -vfi
RUN ./configure --disable-maintainer-mode 
RUN make


# Build atlashdf python wheel
RUN pip3 install pybind11
WORKDIR /atlashdf/python_module
RUN python3 setup.py bdist_wheel

# Now, the wheel is in /atlashdf/python_module/dist and can be copied by running a container and mounting:
# $ docker run -it -v dist:/out image-tag                           
# root@f029b3ad9157:/atlashdf/python_module# cp dist/atlashdf-0.1-cp310-cp310-linux_x86_64.whl /out
# root@f029b3ad9157:/atlashdf/python_module# exit
#
# Then, you can install this beast (but be sure to have all shared objects or use auditwheel to repair it)


FROM jupyter/tensorflow-notebook AS jupyter

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    libosmpbf-dev \
    libhdf5-dev \
    libboost-dev \
    && apt-get clean &&  rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

COPY --from=builder /atlashdf/python_module/dist/* ./
COPY --from=builder /atlashdf/target/wheels/* ./
COPY --from=builder /atlashdf/assets/* assets/
COPY --from=builder /atlashdf/*.ipynb ./

RUN pip install atlashdf-0.1-cp310-cp310-linux_x86_64.whl
RUN pip install atlashdf_rs-0.1.0-cp310-cp310-manylinux_2_31_x86_64.whl
RUN pip install rasterio
RUN pip install torchgeo
