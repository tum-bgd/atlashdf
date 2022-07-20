# -------------------------------
# author: Hao Li, hao.li@uni-heidelberg.de
# data: 26.08.2020
# -------------------------------


import numpy as np
import rasterio
import time
import tqdm
from pysnic.algorithms.snic import snic, compute_grid
from itertools import chain
import h5py

img_list_DE = [
     "eu_countries_077",
     "eu_countries_078",
     "eu_countries_079",
     "eu_countries_080",
     "eu_countries_085",
     "eu_countries_086",
     "eu_countries_087",
     "eu_countries_088",
     "eu_countries_089",#issue with SP
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

img_list = [
     "eu_countries_077",
     "eu_countries_078",
     "eu_countries_079",
     "eu_countries_080",
     "eu_countries_085",
     "eu_countries_086",
     "eu_countries_087",
     "eu_countries_088",
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

class_num = 12
transform_map = {
    11: 1,
    12: 2,
    13: 3,
    14: 4,
    5: 12,
    21: 5,
    22: 6,
    23: 7,
    31: 8,
    32: 9,
    33: 10,
    41: 11,
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
            label[label == item[0]] = item[1]

        with rasterio.open(out_tif, "w", **kwds) as dst_ds:
            dst_ds.write(label, 1)


def random_label_slice(labels, label, centrioid, lpad, rpad, num=1):
    """random_label_slice.

    :param labels: np.ndarry of label image
    :param label: selected label
    :param lpad: left padding
    :param rpad: right padding
    :param num: number of label slice
    :param centrioid: centrioids coordicates from SNIC superpixel results
    """
    p_labels = np.pad(labels, (lpad, rpad))
    coords = np.argwhere(p_labels == label).tolist()
    centers_xy = np.array(centrioid).tolist()
    dict1 = {(x, y) for x, y in coords}
    dict2 = {(x, y) for x, y in centers_xy}
    match = set(dict1) & set(dict2)
    coords_SP = list(match)
    randidx = np.random.randint(0, len(coords_SP), num)
    coords_SP = np.array(coords_SP)
    #print(coords_SP[randidx])
    #assert 0
    for coord in coords_SP[randidx]:
        row, col = coord
        yield ((row - lpad, col - lpad), label)
    

def std_image(src, eps=0.1):
    x_max = src.max()
    x_min = src.min()
    if x_max - x_min > eps:
        return 2 * ((src - x_min) / (x_max - x_min)) - 1
    return src


def navie_sample(avg_num, class_num, centrioids, w_size, src_tif, label_tif):
    """navie_sample.

    :param num: sample number of each class
    :param w_size: window size
    :param src_tif: S2 image
    :param label_tif: label image
    :param centrioids: centrioids coordicates from SNIC superpixel results
    """
    if w_size % 2 == 0:
        lpad = w_size // 2 - 1
        rpad = w_size // 2
    else:
        lpad == rpad == w_size // 2

    with rasterio.open(label_tif) as label_ds:
        labels = label_ds.read(1)
        for item in transform_map.items():
            labels[labels == item[0]] = item[1]
        counts = [np.count_nonzero(labels == i) for i in range(1, class_num + 1)]
        train_label = []
        val_label = []
        if min(counts) >= avg_num:
            for i in range(1, class_num + 1):
                label_slice = list(random_label_slice(labels, i, centrioids, lpad, rpad, avg_num))
                train_label += label_slice[: int(avg_num * 0.8)]
                val_label += label_slice[int(avg_num * 0.8):]
        else:
            for i in range(class_num):
                if counts[i] >= avg_num:
                    label_slice = list(
                        random_label_slice(labels, i + 1, lpad, rpad, avg_num)
                    )
                    train_label += label_slice[: int(avg_num * 0.8)]
                    val_label += label_slice[int(avg_num * 0.8):]
                else:
                    label_slice = list(
                        random_label_slice(labels, i + 1, lpad, rpad, counts[i])
                    )
                    print(label_tif, i)
                    train_label += label_slice[: int(avg_num * 0.8)]
                    val_label += label_slice[int(avg_num * 0.8):]

    with rasterio.open(src_tif) as src_ds:
        src = src_ds.read()
        std_src = std_image(src)
        p_src = np.pad(std_src, ((0, 0), (lpad, rpad), (lpad, rpad)))
        p_src = p_src.swapaxes(0, 1).swapaxes(1, 2)
        for _ in train_label + val_label:
            coord, _label = _
            row, col = coord
            yield (
                (row, col),
                (p_src[row: row + 2 * rpad, col: col + 2 * rpad, :], _label),
            )





def main():
    wsize = 12
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    src_suf = "_10m/S2_10m_3035_10bands.tif"
    label_suf = "_10m/S2_10m_3035_label.tif"

    t_samples_suf = "_10m/SP_std_train_samples.npy"
    t_coords_suf = "_10m/SP_std_train_samples_coord.npy"

    v_samples_suf = "_10m/SP_std_val_samples.npy"
    v_coords_suf = "_10m/SP_std_val_samples_coord.npy"
    centers_xy_repo = "_10m/SP_centroids.h5"
    avg_num = 1000
    class_num = 12
    step_size = 20
    compactness = 10.00
    train_number = int(avg_num * class_num * 0.8)
    for p in tqdm.tqdm(img_list):
        src_tif = root + p + src_suf
        label_tif = root + p + label_suf
        SP_repo = root + p
        # -------------------------------
        # # or directly load the superpixel results for sampling
        r_hf = h5py.File(SP_repo + centers_xy_repo, 'r')
        centroids = r_hf.get('centers_xy')  
        # -------------------------------
        result = list(navie_sample(avg_num, class_num, centroids, wsize, src_tif, label_tif))
        train_label = result[:train_number]
        val_label = result[train_number:]

        t_samples = [sample for _, sample in train_label]
        np.save(root + p + t_samples_suf, t_samples)

        v_samples = [sample for _, sample in val_label]
        np.save(root + p + v_samples_suf, v_samples)

    print("Start to merge all npy")
    t_samples = np.load(root + img_list[0] + t_samples_suf, allow_pickle=True)
    print(len(img_list))
    for i, p in tqdm.tqdm(enumerate(img_list[1:])):
        try:
            t_samples = np.concatenate(
                (t_samples, np.load(root + p + t_samples_suf, allow_pickle=True))
            )
        except Exception:
            print(p)

    np.random.shuffle(t_samples)
    np.save("DE_10ba_1k_SP_std_train_samples.npy", t_samples)

    v_samples = np.load(root + img_list[0] + v_samples_suf, allow_pickle=True)
    for i, p in tqdm.tqdm(enumerate(img_list[1:])):
        try:
            v_samples = np.concatenate(
                (v_samples, np.load(root + p + v_samples_suf, allow_pickle=True))
            )
        except Exception:
            print(p)

    np.random.shuffle(v_samples)
    np.save("DE_10ba_1k_SP_std_val_samples.npy", v_samples)


if __name__ == "__main__":
    main()
