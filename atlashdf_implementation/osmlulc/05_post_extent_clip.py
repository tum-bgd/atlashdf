import json
import os
import numpy as np
import rasterio
from tqdm import tqdm
import json
import os
import numpy as np
import rasterio


def loadtif(filename):
    # Open a single band and plot
    with rasterio.open(filename) as src:
        a = src.read()
        nbands = src.count
        nrows = src.height
        ncolumns = src.width
    image = np.empty([nrows, ncolumns, nbands])
    for i in range(nbands):
        image[:, :, i] = a[i, :, :]
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


def extent_clip(img_input, img_saved, mask):
    classified_dataset = rasterio.open(img_input)
    classified_label = np.array(classified_dataset.read(1))
    mask_img = rasterio.open(mask)
    mask_img = np.array(mask_img.read(1))
    none_index = np.where(mask_img != 1)
    classified_label[none_index] = 0
    savetif(classified_label, img_input, img_saved)
    print('Save the clipped layers into:%s ' % img_saved)
    pass


if __name__ == "__main__":
    # this is the image list you what to mask.
    img_list = [
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
    for p in img_list:
        # define the root repo, input file, and saved file names.
        folder_path = '/mnt/sds-hd/sd17f001/OSM4EO/sepal.io'
        in_name = 'S2_10m_3035_SP_pixel_classified.tif'
        out_name = 'S2_10m_3035_SP_pixel_classified_clipped.tif'
        mask_file = "S2_10m_3035_maskR.tif"
        img_input = os.path.join(folder_path, p+'_10m', in_name)
        img_saved = os.path.join(folder_path, p+'_10m', out_name)
        mask = os.path.join(folder_path, p+'_10m', mask_file)
        extent_clip(img_input, img_saved, mask)
