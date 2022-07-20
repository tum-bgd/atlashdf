
import numpy as np
import rasterio
import tqdm
import json

#img_list = []
#for i in range(0, 254):
#    num = (3-len(str(i))) * '0' + str(i)
#    img_list.append("eu_countries_{}".format(num))

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


def random_label_slice(labels, label, lpad, rpad, num=1):
    """random_label_slice.

    :param labels: np.ndarry of label image
    :param label: selected label
    :param lpad: left padding
    :param rpad: right padding
    :param num: number of label slice
    """
    p_labels = np.pad(labels, (lpad, rpad))
    coords = np.argwhere(p_labels == label)
    randidx = np.random.randint(0, len(coords), num)
    for coord in coords[randidx]:
        row, col = coord
        yield ((row - lpad, col - lpad), label)


def std_image(src, eps=0.1):
    x_max = src.max()
    x_min = src.min()
    if x_max - x_min > eps:
        return 2 * ((src - x_min) / (x_max - x_min)) - 1
    return src


def navie_sample(validation, w_size, src_tif):
    """navie_sample.

    :param validation: validation geojson
    :param w_size: window size
    :param src_tif: S2 image
    """
    if w_size % 2 == 0:
        lpad = w_size // 2 - 1
        rpad = w_size // 2
    else:
        lpad == rpad == w_size // 2
    coords = []
    valid_label = []
    with open(validation) as f:
        valid_data = json.load(f)
    for feature in valid_data['features']:
        coord = feature['geometry']['coordinates']
        coords.append(coord)
        value = feature['properties']['ValValue']
        valid_label.append(value)

    valid_label[valid_label == 5] = 12  # transfer the label

    with rasterio.open(src_tif) as src_ds:
        src = src_ds.read()
        std_src = std_image(src)
        std = std_src.swapaxes(0, 1).swapaxes(1, 2)
        p_src = np.pad(std_src, ((0, 0), (lpad, rpad), (lpad, rpad)))
        p_src = p_src.swapaxes(0, 1).swapaxes(1, 2)
        for i in range(len(coords)):
            coord = coords[i]
            label = valid_label[i]
            x, y = coord[0]
            row, col = rasterio.transform.rowcol(src_ds.transform, x, y)
            p_row = std.shape[0]
            p_col = std.shape[1]
            if row>0 and row<p_row and col>0 and col<p_col:
                a = p_src[row : row + 2 * rpad, col : col + 2 * rpad, :]
                print(a.shape)
                print(label)
                yield (
                    (row, col),
                    (p_src[row : row + 2 * rpad, col : col + 2 * rpad, :], label),
                )
            else: 
            	pass



def merge_npy():
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    samples_suf = "_10m/std_samples.npy"
    samples = np.load(root + img_list[0] + samples_suf, allow_pickle=True)
    for p in img_list[1:]:
        samples = np.concatenate(
            (samples, np.load(root + p + samples_suf, allow_pickle=True))
        )

    np.random.shuffle(samples)
    np.save("DE_samples.npy", samples)




def main():
    wsize = 12
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    #src_suf = "_20m/S2_20m_3035_upsample.tif"
    src_suf = "_10m/S2_10m_3035.tif"
    validation = "/mnt/sds-hd/sd17f001/hao/GeoAI4Water/validation_states/bw_3035.geojson"
    v_samples_suf = "_10m/2_std_val_samples.npy"

    for p in tqdm.tqdm(img_list):
         src_tif = root + p + src_suf
         result = list(navie_sample(validation, wsize, src_tif))
         print(len(result))

         v_samples = [sample for _, sample in result]
         np.save(root + p + v_samples_suf, v_samples)

    print("Start to merge all npy") 
    flag = 0
    for i, p in tqdm.tqdm(enumerate(img_list[0:])):
        sample = np.load(root + p + v_samples_suf, allow_pickle=True)
        if sample.shape[0] == 0:
            pass
        else:
            if flag == 0:
                v_samples = sample
                flag = 1
            else:
                v_samples = np.concatenate(
                (v_samples, np.load(root + p + v_samples_suf, allow_pickle=True))
            )

    np.random.shuffle(v_samples)
    np.save("bw_4band_reference.npy", v_samples)


if __name__ == "__main__":
    main()
