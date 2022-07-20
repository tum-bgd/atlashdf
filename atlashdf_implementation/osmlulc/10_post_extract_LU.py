import json
import os
import numpy as np
import rasterio
from tqdm import tqdm


def loadtif(filename):
    # Open a single band and plot
    with rasterio.open(filename, "r+") as src:
        src.nodata = 0
        a = src.read(1)
    image = a.astype(np.uint8)
    return image


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


def extract_LU_layers(img_input, img_saved, LU_class):
    classified_label = loadtif(img_input)
    filtered_label = np.where(classified_label == LU_class, LU_class, 0)
    savetif(filtered_label, img_input, img_saved)
    print('Save the classified layers into:%s ' % img_saved)


    pass


if __name__ == "__main__":
    # please define the LULC classes that you what to extract.
    LU_class = 5
    # define the root repo, input file, and saved file names.
    root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/"
    file = "DE_10ba_SP_10m_3035_water.tif"
    out_file = "DE_10ba_SP_10m_3035_water.tif"
    img_input = root + file
    img_saved = root + out_file
    extract_LU_layers(img_input, img_saved, LU_class)
