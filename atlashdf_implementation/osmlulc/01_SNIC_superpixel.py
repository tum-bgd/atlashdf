# -------------------------------
# author: Hao Li, hao.li@uni-heidelberg.de
# data: 26.08.2020
# -------------------------------


import numpy as np
import rasterio
import time
import tqdm
import skimage.color
from pysnic.algorithms.snic import snic, compute_grid
from itertools import chain
import h5py
from skimage import exposure

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

img_list = [
     "eu_countries_124",
     "eu_countries_125",
     "eu_countries_126",

]


def loadtif(filename):
    """
    @param filename:
    @return:
    """
    # Open a single band and plot
    with rasterio.open(filename) as src:
        a = src.read()
        nbands = src.count
        nrows = src.height
        ncolumns = src.width
    nbands = 3
    image = np.empty([nrows, ncolumns, nbands])
    for i in range(nbands):
        arr = a[(nbands - i - 1), :, :]
        vmin, vmax = np.nanpercentile(arr, (1, 99))
        arr = exposure.rescale_intensity(arr, in_range=(vmin, vmax))
        RGB = ((arr - arr.min()) * (1 / (arr.max() - arr.min()) * 255)).astype('uint8')
        image[:, :, i] = RGB
    return image


def SNIC_SP(input_image, output_folder, step, compactness):
    """
    Apply the SNIC superpixel segementation to the S2 tile, and save the centeriods and segementations into .npy file

    @param input_image: the input S2 tile
    @param output_folder: the folder for saving the outputs
    @param step: hyperparameter for SNIC
    @param compactness: hyperparameter for SNIC
    """

    # load the image and convert to LAB color space
    color_image = loadtif(input_image)
    lab_image = skimage.color.rgb2lab(color_image).tolist()
    number_of_pixels = color_image.shape[0] * color_image.shape[1]
    # SNIC parameters
    step_size = step
    number_of_segments = number_of_pixels / (step_size * step_size)
    # compute grid
    grid = compute_grid(color_image.shape, number_of_segments)
    seeds = list(chain.from_iterable(grid))
    # SNIC for generating the superpixel
    segmentation, distances, centroids = snic(
        lab_image, seeds, compactness,
        update_func=lambda num_pixels: print("processed %05.2f%%" % (num_pixels * 100 / number_of_pixels)))
    # Calculate centeriods based on segmentation map for Sampling and Prediction
    segmentation_map = np.array(segmentation)
    centers_xy = (np.round(np.array(centroids)[:, 0].tolist()))
    centers_xy = np.array(centers_xy).astype(np.uint16)
    centers_xy = centers_xy[:, [1, 0]]  # correct the image coordinates and array coordinates
    centers_xy_repo = "_10m/SP_centroids.h5"
    segmentation_map_repo = "_10m/SP_segmentation.h5"
    hf = h5py.File(output_folder + centers_xy_repo, 'w')
    hf.create_dataset('centers_xy', data=centers_xy)
    hf.close()
    hf2 = h5py.File(output_folder + segmentation_map_repo, 'w')
    hf2.create_dataset('segmentation', data=segmentation_map)
    hf2.close()
    return centers_xy


def main():
    root = "/mnt/sds-hd/sd17f001/OSM4EO/sepal.io/"
    src_suf = "_10m/S2_10m_3035.tif"
    label_suf = "_10m/S2_10m_3035_label.tif"
    step_size = 15
    compactness = 50.00
    for p in tqdm.tqdm(img_list):
        src_tif = root + p + src_suf
        label_tif = root + p + label_suf
        SP_repo = root + p
        # -------------------------------
        # SNIC for generating the superpixel
        centroids = SNIC_SP(src_tif, SP_repo, step_size, compactness)
        print("Successfully created superpixel for: {}" .format(p))
        
if __name__ == "__main__":
    main()
