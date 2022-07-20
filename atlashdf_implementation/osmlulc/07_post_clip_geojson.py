
import json
import rasterio
from rasterio.mask import mask
import numpy as np

def savetif(X, transform, infilename, outfilename):
    # save classification map into a same georeferening tif
    with rasterio.open(infilename) as src:
        kwds = src.profile
        kwds['count'] = 1
        kwds['nodata'] = 0
        kwds['height'] = X.shape[1]
        kwds['width'] = X.shape[2]
        kwds['dtype'] = 'uint8'
        kwds['compress'] = 'lzw'
        kwds['transform'] = transform
        kwds.update(BIGTIFF='YES')
    X = X.astype(np.uint8).reshape(kwds['height'], kwds['width'])
    # check the shape of mosaic
    # print(X.shape)
    with rasterio.open(outfilename, 'w', **kwds) as dst:
        dst.write(X, 1)



def clip_geojson(in_tif, geometry, out_tif):

    with open(geometry) as src_geo:
        geoms = json.loads(src_geo.read())
        geoms = geoms['features'][0]['geometry']
    shape = [geoms]

    with rasterio.open(in_tif) as src_ds:
        out_img, out_transform = mask(src_ds, shape, crop=True)
        kwds = src_ds.meta
    print('clipping is now successful!')
    print(out_img.shape)
    savetif(out_img, out_transform, in_tif, out_tif)


if __name__ == "__main__":
    root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/"
    file = "DE_10ba_SP_10m_3035_classified.tif"
    saved_root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/"
    saved_file = "DE_10ba_SP_10m_3035_classified.tif"
    geo_file = "/mnt/sds-hd/sd17f001/OSM4EO/mosaic_EU/EU_boundary/DE_boundary.geojson"
    img_input = root + file
    img_saved = saved_root + saved_file
    clip_geojson(img_input, geo_file, img_saved)
