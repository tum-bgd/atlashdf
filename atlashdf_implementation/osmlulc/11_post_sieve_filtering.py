# Author: Zhaoyan Wu
import os
import sys
import numpy as np
import rasterio
from rasterio.features import sieve, shapes

def savetif(X, infilename, outfilename):
    # save classification map into a same georeferening tif
    with rasterio.open(infilename) as src:
        kwds = src.profile
        kwds['count'] = 1
        kwds['nodata'] = 0
        kwds['dtype'] = 'uint8'
        kwds['compress'] = 'lzw'

    X = X.astype(np.uint8)
    with rasterio.open(outfilename, 'w', **kwds) as dst:
        dst.write(X, 1)


def seieve(in_file, out_file, size):
    with rasterio.Env():
        with rasterio.open(in_file) as src:
            shade = src.read(1)

        sieved = sieve(shade, size, out=np.zeros(src.shape, src.dtypes[0]), connectivity=8)

        kwargs = src.meta
        kwargs['transform'] = rasterio.transform.guard_transform(kwargs['transform'])
    savetif(sieved, in_file, out_file)


def main():
    size = 64
    folder_path = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/"
    in_name = 'DE_10ba_SP_10m_3035_water.tif'
    out_name = 'DE_10ba_SP_10m_3035_water.tif'
    in_file = folder_path + in_name
    out_file = folder_path + out_name
    seieve(in_file, out_file, size)


if __name__ == '__main__':
    main()
