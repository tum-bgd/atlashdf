### OSMLULC classficaiton and surface water mapping with deep residual convolutional neural networks

This is the source code repo for the deep learning method within OSMLULC (surface water mapping) work.

To be noticed, all the code was designed for bwcluster GPU server with python packages and environment (ps: dependency comes later...) on Anaconda. 

**Importantly, all trained models for different EU countries can be found in saved_models repo. Please simply ignore all the file names in the script for now since they refer to old repo. **

**All results availble in SDS under the OSM4EO folder**

- classified map file example: *OSM4EO\sepal.io\eu_countries_010_10m\S2_10m_3035_classified.tif*
- sived classified map file example: *OSM4EO\sepal.io\eu_countries_010_10m\S2_10m_3035_classified_sieved.tif*
- country mosaic file example: *OSM4EO\mosaic_EU\DE_10m_3035_classified_sieved.tif*
- OSM label file example:*OSM4EO\label_EU\DE_10m_3035_label.tif*


### Sentinel-2 Feature Space Engineering
 
The first step is to resample the 20m S2 MSI band into 10m and combine them with 4 10m bands in order to have 10 bands MSI. This will need the following scripts.

```bash
$ python 00_resampling.py
$ python 00_combine_fs.py
```

### Superpixel Segmentation 
 
The next step is to conduct unsupervised SLIC superpixel segmentation based on the RGB image of all Sentinel-2 tiles. Within the code, one would have the segementations as well as centriod points for each tile.

```bash
$ python 01_SNIC_superpixel.py
```

### Preprocessing
 
The next step is to prepare the training/validation samples from SDS OSM label files (already in raster format with Corine classes). Within the code, one should define the training samples images list and output files.

```bash
$ python 02_preproce_prepare_sample.py
$ python 02_validate_sample.py
```

### Training

After preparing the training samples, one could start the model training. The current model is based on deep residual convolutional neural networks (ResNet), SVM and Rf, within this code, one could have the model depth and the locations of input and output files.

```bash
$ python 03_keras_models_single.py
$ python 03_SVM_models_single.py
$ python 03_RF_models_single.py
```

### Prediction 

Once the model training is finished, this code will do the model inference (two different way, one for each pixel another for each superpixel) to get the classification results based on the trained model and images list. Within the code, one could change this trained model path and image index.

```bash
$ python 04_keras_classification_pixel.py
$ python 04_keras_classification_SP.py

```

### Postprocessing

After the prediction, there are several postprocessing steps (e.g., overlap clip, label transfer, product merge, extract LU, sieve filtering). one could extract individual layer by implmenting this postprocessing code. Here as a example, we extract the class 12 (water) from the entire Germany.

```bash
$ python 05_post_extent_clip.py
$ python 06_post_extent_merge.py
$ python 07_post_clip_geojson.py
$ python 08_post_label_transfer.py
$ python 09_post_product_merge.py
$ python 10_post_extract_LU.py
$ python 11_post_sieve_filtering.py

```

### Others

There is also some script for NDWI calculating, etc

```bash
$ python ndwi.py
```


## Sample product for Germany:

https://doi.org/10.11588/data/AAKAF9



## Related work:
* Schultz, M., Voss, J., Auer, M., Carter, S., and Zipf, A. (2017): Open land cover from OpenStreetMap and remote sensing. International Journal of Applied Earth Observation and Geoinformation, 63, pp. 206-213. DOI: 10.1016/j.jag.2017.07.014.
* Li, H.; Ghamisi, P.; Rasti, B.; Wu, Z.; Shapiro, A.; Schultz, M.; Zipf, A. A Multi-Sensor Fusion Framework Based on Coupled Residual Convolutional Neural Networks. Remote Sens. 2020, 12, 2067. https://doi.org/10.3390/rs12122067
* Li, H. J. Zech, C. Ludwig, S. Fendrich, A. Shapiro, M. Schultz, A. Zipf (2021): Automatic mapping of national surface water with OpenStreetMap and Sentinel-2 MSI data using deep learning.. International Journal of Applied Earth Observation and Geoinformation, Vol 104, 2021, 102571.
https://doi.org/10.1016/j.jag.2021.102571.
