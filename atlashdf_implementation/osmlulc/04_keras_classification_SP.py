from tensorflow.keras.models import load_model
from tensorflow.keras.models import Model
from hsi_io import *
import numpy as np
import os
from hsi_io import loadtif, savetif
import time
import tqdm
import rasterio
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


def prediction(s2_image, classified_image, centers_xy, segmentation_map):
    """

    @param s2_image:
    @param classified_image:
    @param centers_xy:
    @param segmentation_map:
    """
    save_dir = os.path.join(os.getcwd(), 'saved_models')
    model_name = 'DE_SP_trained_model_single_10m.h5'
    r_ce = h5py.File(centers_xy, 'r')
    centroids = np.array(r_ce.get('centers_xy')).tolist()
    r_se = h5py.File(segmentation_map, 'r')
    segmentation = np.array(r_se.get('segmentation'))

    ###########  Data Import #############
    # config the input and output file folder and location
    if extension(s2_image) == 'tif':
        bands_matrix = loadtif(s2_image)
        nbands_HSI = bands_matrix.shape[2]
        n_row = bands_matrix.shape[0]
        n_col = bands_matrix.shape[1]
        print(bands_matrix.shape)
        # check scaling to [-1;1]
        eps = 0.1
        if abs(np.max(bands_matrix) - np.min(bands_matrix)) > eps:
            bands_matrix_new = -1 + 2 * (bands_matrix - np.min(bands_matrix)) / (
                    np.max(bands_matrix) - np.min(bands_matrix))
        else:
            bands_matrix_new = bands_matrix
    bands_matrix_new_HSI = np.lib.pad(bands_matrix_new, ((6, 6), (6, 6), (0, 0)), 'symmetric')

    print('data is okay')
    ####################load the best model############################

    # perform feature extraction
    model_path = os.path.join(save_dir, model_name)
    model = load_model(model_path)
    feature_model = Model(inputs=model.input,
                          outputs=model.output)
    # initialize the deep feature map
    feature_map = np.empty([n_row, n_col])
    start = time.time()
    pre = []
    id = 1
    for x in range(0, len(centroids), 20000):
        chunk = centroids[x:x+20000]
        length = len(chunk)
        X_window_HSI = np.empty([length, 12, 12, nbands_HSI])
        for i in range(length):
            sp = chunk[i]
            row_id = sp[0]
            col_id = sp[1]
            row_min = row_id
            row_max = row_id + 12
            col_min = col_id
            col_max = col_id + 12
            X_window_HSI[i, :, :, :] = bands_matrix_new_HSI[row_min:row_max, col_min:col_max, :]
        x_test_HSI = X_window_HSI.astype('float32')
        pred = feature_model.predict(x_test_HSI)
        pred = np.argmax(pred, axis=1).tolist()
        pre[x:x+20000] = pred
        print('Classify the deep feature for superpixel chunk:', id)
        id += 1
    pre = np.array(pre)
    sp_pixels = np.argwhere(pre == 12)
    for i in range(len(sp_pixels)):
        sp = sp_pixels[i]
        se_pixels = np.argwhere(segmentation == sp)
        feature_map[tuple(np.transpose(se_pixels))] = 5 #consider CLC classification code
        print('{} out of {}'.format(i, len(sp_pixels)))
    end = time.time()
    y_test_time = end - start

    #####################save the extracted features###########################

    feature_path = classified_image
    savetif(feature_map, s2_image, feature_path)
    print('Save classification labels into:%s ' % feature_path)
    print('prediction time', y_test_time)


def main():
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    src_suf = "_10m/S2_10m_3035.tif"
    predicted_suf = "_10m/S2_10m_3035_SP_classified.tif"
    centers_xy_repo = "_10m/SP_centroids.h5"
    segmentation_map_repo = "_10m/SP_segmentation.h5"

    for p in img_list_DE:
        src_tif = root + p + src_suf
        predicted_tif = root + p + predicted_suf
        centers = root + p + centers_xy_repo
        segmentation = root + p + segmentation_map_repo
        prediction(src_tif, predicted_tif, centers, segmentation)


if __name__ == "__main__":
    main()
