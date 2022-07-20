import numpy as np
import os
import rasterio
from rasterio.enums import Resampling

img_list_DE = [
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


def combine(input_path, input_two, save_path):
    """
    Decrease the pixel size of the raster.

    Args:
        input_path: filepath for input image
        input_two: filepath for second input image
        save_path (str): filepath to where the output file should be stored

    Returns: Nothing, it writes a raster file with new resolution.
    :param input_two:

    """
    file_list = [input_path, input_two]

    # Read metadata of first file
    with rasterio.open(file_list[0]) as src0:
        meta = src0.profile
        img = src0.read()

    with rasterio.open(file_list[1]) as src1:
        meta2 = src1.profile
        img2 = src1.read()
    if meta['height'] == meta2['width'] and meta2['height'] == meta['width']:
        print('dimention matched!')
    else:
        print('dimention unmatched!')
        print(meta2['width'])
        print(meta['width'])
        print(meta['height'])
        print(meta2['height'])
    # Update meta to reflect the number of layers
    meta.update(count=10)
    meta.update(nodata=0)
    meta.update(BIGTIFF='YES')
    meta.update(compress='lzw')
    img_combine = np.concatenate((img,img2))
    print(img_combine.shape)
    # Read each layer and write it to stack
    with rasterio.open(save_path, 'w', **meta) as dst:
        dst.write(img_combine)
    print('file saved in ' + save_path)


if __name__ == "__main__":
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    input_20m_dir = "_20m/S2_20m_3035_upsample.tif"
    input_10m_dir = "_10m/S2_10m_3035.tif"
    save_dir = "_10m/S2_10m_3035_10bands.tif"
    for p in img_list_DE:
        img_10m = root + p + input_10m_dir
        img_20m = root + p + input_20m_dir
        img_save = root + p + save_dir
        combine(img_10m, img_20m, img_save)
