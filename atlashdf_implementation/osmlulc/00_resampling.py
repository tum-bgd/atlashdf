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


def resample(input_path, reference_path, save_path):
    """
    Decrease the pixel size of the raster.

    Args:
        reference_path: reference_path you want to resample
        input_path: filepath for input image

        save_path (str): filepath to where the output file should be stored

    Returns: Nothing, it writes a raster file with new resolution.
    :param reference_path:

    """

    with rasterio.open(reference_path) as src:
        meta = src.profile
        n_height = meta['height']
        n_width = meta['width']

    with rasterio.open(input_path) as img:
        kwds = img.profile
        # resample data to target shape
        data = img.read(
            out_shape=(
                img.count,
                n_height,
                n_width
            ),
            resampling=Resampling.nearest
        )
        print(img.height)
        print(n_height)
        # scale image transform
        transform = img.transform * img.transform.scale(
            (img.width / data.shape[-1]),
            (img.height / data.shape[-2])
        )
        # update the image profile
        kwds['nodata'] = 0
        kwds['height'] = n_height
        kwds['width'] = n_width
        kwds['transform'] = transform
        kwds['compress'] = 'lzw'
        kwds.update(BIGTIFF='YES')
    with rasterio.open(save_path, 'w', **kwds) as dst:
        dst.write(data)
    print('file saved in ' + save_path)
    print(data.shape)


if __name__ == "__main__":
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    input_dir = "_20m/S2_20m_3035.tif"
    input_10m_dir = "_10m/S2_10m_3035.tif"
    save_dir = "_20m/S2_20m_3035_upsample.tif"
    for p in img_list_DE:
        img = root + p + input_dir
        img_10m = root + p + input_10m_dir
        img_save = root + p + save_dir
        resample(img, img_10m, img_save)