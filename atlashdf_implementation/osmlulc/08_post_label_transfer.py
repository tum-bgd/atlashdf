import json
import os
import numpy as np
import rasterio
from tqdm import tqdm
import json
import os
import numpy as np
import rasterio

transform_map = {
    41: 11,
    21: 5,
    5: 12,
    11: 1,
    12: 2,
    13: 3,
    14: 4,
    22: 6,
    23: 7,
    31: 8,
    32: 9,
    33: 10,
}


def transform_label(in_tif, out_tif):
    """transform michi's label to one-hot label

    :param in_tif: input tif path
    :param out_tif: transformed label tif output path
    """
    with rasterio.open(in_tif) as src_ds:
        kwds = src_ds.profile
        label = src_ds.read(1)

        for item in transform_map.items():
            label[label == item[1]] = item[0]

        with rasterio.open(out_tif, "w", **kwds) as dst_ds:
            dst_ds.write(label, 1)


if __name__ == "__main__":
    # define the root repo, input file, and saved file names.
    root = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/DE_water_layers/"
    file = "DE_10ba_SP_10m_3035_classified.tif"
    out_file = "DE_10ba_SP_10m_3035_water.tif"
    img_input = root + file
    img_saved = root + out_file
    transform_label(img_input, img_saved)
    print("now label transfer is finished!")
