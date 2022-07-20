
import numpy as np
import rasterio
from rasterio.merge import merge


def loadtif(filename):
    # Open a single band and plot
    with rasterio.open(filename) as src:
        a = src.read()
        nbands = src.count
        nrows = src.height
        ncolumns = src.width
    image = np.empty([nrows, ncolumns, nbands], dtype=np.uint8)
    for i in range(nbands):
        image[:, :, i] = a[i, :, :]
    return image


def savetif(X, infilename, outfilename):
    # save classification map into a same georeferening tif
    with rasterio.open(infilename) as src:
        kwds = src.profile
        kwds['count'] = 1
        kwds['nodata'] = 0
        kwds['height'] = X.shape[0]
        kwds['width'] = X.shape[1]
        kwds['dtype'] = 'uint8'
        kwds.update(BIGTIFF='YES')
    X = X.astype(np.uint8).reshape(kwds['height'], kwds['width'])
    # check the shape of mosaic
    # print(X.shape)
    with rasterio.open(outfilename, 'w', **kwds) as dst:
        dst.write(X, 1)


def extent_merge(img_label, img_mosaic, img_saved):
    label = loadtif(img_label)
    print('label', label.shape)
    mosaic = loadtif(img_mosaic)
    print('mosaic', mosaic.shape)
    product = np.where((label==5) & (mosaic==5), label, 0)
    disagreement_type1 = np.where((label!=5) & (mosaic==5))
    disagreement_type2 = np.where((label==5) & (mosaic!=5))
    product[disagreement_type1] = 1
    product[disagreement_type2] = 2
    print('product', product.shape)
    savetif(product, img_label, img_saved)
    print('Save the merged layers into:%s ' % img_saved)
    pass


if __name__ == "__main__":
    # this is the image list you what to merge.
    # TODO: later should be changed to read from SDS folder
    root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/"
    mosaic_file = "DE_water_10m_3035_classified.tif"
    label_file = "water_label_DE_10m_3035_label.tif"
    save_file = "agreement_DE_10m_3035.tif"
    img_mosaic = root + mosaic_file
    img_label = root + label_file
    img_saved = root + save_file
    extent_merge(img_label, img_mosaic, img_saved)
