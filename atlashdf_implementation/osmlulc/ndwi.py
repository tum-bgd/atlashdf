import json
import rasterio
import numpy as np
from rasterio.mask import mask


def savetif(X, infilename, outfilename):
    # save classification map into a same georeferening tif
    with rasterio.open(infilename) as src:
        kwds = src.profile
        kwds['count'] = 1
        kwds['nodata'] = 0
        kwds['compress'] = 'lzw'
        kwds['dtype'] = 'float64'
    # check the shape of mosaic
    # print(X.shape)
    with rasterio.open(outfilename, 'w', **kwds) as dst:
        dst.write(X,1)


def ndwi(in_tif, out_tif):
    with rasterio.open(in_tif) as src_ds:
        green = src_ds.read(2).astype(float)
        nir = src_ds.read(4).astype(float)
        # np.seterr(divide='ignore', invalid='ignore')
    out_img = (green - nir) / (nir + green)
    print('ndwi is now successful!')
    print(out_img.shape)
    savetif(out_img, in_tif, out_tif)


if __name__ == "__main__":
    root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/S2_imagery/"
    file = "wesenberg_10ba_composite.tif"
    saved_root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/product_compare/"
    saved_file = "wesenberg_ndwi.tif"
    img_input = root + file
    img_saved = saved_root + saved_file
    ndwi(img_input, img_saved)
