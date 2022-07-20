
import numpy as np
import rasterio
from rasterio.merge import merge


def savetif(X, X_trans, infilename, outfilename):
    # save classification map into a same georeferening tif
    with rasterio.open(infilename) as src:
        kwds = src.profile
        kwds['count'] = 1
        kwds['nodata'] = 0
        kwds['height'] = X.shape[1]
        kwds['width'] = X.shape[2]
        kwds['dtype'] = 'uint8'
        kwds['transform'] = X_trans
        kwds['compress'] = 'lzw'
        kwds.update(BIGTIFF='YES')
    X = X.astype(np.uint8).reshape(kwds['height'], kwds['width'])
    # check the shape of mosaic
    # print(X.shape)
    with rasterio.open(outfilename, 'w', **kwds) as dst:
        dst.write(X, 1)


def extent_merge(img_input, img_saved):
    src_mosaic = []
    for img in img_input:
        src = rasterio.open(img)
        src_mosaic.append(src)
    print('Start to merge the S2 tiles: total number %s' % len(img_input))
    mosaic, out_trans = merge(src_mosaic, nodata=0)
    # visualization for mosaic with rasterio.plot.show function
    savetif(mosaic, out_trans, img, img_saved)
    print('Save the merged layers into:%s ' % img_saved)
    pass


if __name__ == "__main__":
    # this is the image list you what to merge.
    # TODO: later should be changed to read from SDS folder
    img_list_merge = [
     "eu_countries_077",
     "eu_countries_078",
     "eu_countries_079",
     "eu_countries_080",
     "eu_countries_085",
     "eu_countries_086",
     "eu_countries_087",
     "eu_countries_088",
     "eu_countries_089",
     "eu_countries_095",
     "eu_countries_096",
     "eu_countries_097",
     "eu_countries_098",
     "eu_countries_099",
     "eu_countries_108",
     "eu_countries_109",
     "eu_countries_110",
     "eu_countries_111",
     "eu_countries_112",
     "eu_countries_123",
     "eu_countries_124",
     "eu_countries_125",
     "eu_countries_126",

  
]
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    file = "_10m/S2_10m_3035_SP_pixel_classified_clipped.tif"
    img_list_new = [root + p + file for p in img_list_merge]
    # define the saved file path
    save_root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/"
    saved_file = "DE_10ba_SP_10m_3035_classified.tif"
    img_saved = save_root + saved_file
    extent_merge(img_list_new, img_saved)
