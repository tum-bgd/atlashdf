import numpy as np
import zipfile
from scipy.io import loadmat, savemat
import pandas as pd
import sys
import rasterio as rio
import hdf5storage

def loadtif(filename):
    # Open a single band and plot
    with rio.open(filename) as src:
        a = src.read()
        nbands = src.count
        nrows = src.height
        ncolumns = src.width
    image=np.empty([nrows, ncolumns, nbands])
    for i in range(nbands):
        image[:,:,i] = a[i,:,:]
    return image

def savetif(X, infilename, outfilename):
    # save classification map into a same georeferening tif
    with rio.open(infilename) as src:
        kwds = src.profile
        kwds['count'] = 1
        kwds['nodata'] = 0
        kwds['dtype'] = 'uint8'
    X = X.astype(np.uint8)
    with rio.open(outfilename, 'w', **kwds) as dst:
        dst.write(X,1)

def window_sample_houston(X, num, filename):
    X = X.head(num)
    X = X.index
    #if extension(filename) == 'mat':
    #    bands_mat = loadmat(filename)
    #    bands_matrix = bands_mat.popitem()[1]
    if extension(filename) == 'tif':
        bands_matrix = loadtif(filename)

        nbands = bands_matrix.shape[2]
        nrows = bands_matrix.shape[0]
        ncols = bands_matrix.shape[1]

        # check scaling to [-1;1]
        eps = 0.1
        if abs(np.max(bands_matrix) - np.min(bands_matrix)) > eps:
            bands_matrix_new = -1 + 2 * (bands_matrix - np.min(bands_matrix)) / (
                    np.max(bands_matrix) - np.min(bands_matrix))
        else:
            bands_matrix_new = bands_matrix
        bands_matrix_new_Houston = np.lib.pad(bands_matrix_new, ((6, 6), (6, 6), (0, 0)), 'symmetric')
    X_window = np.empty([num, 12, 12, nbands])
    for i in range(num):
        id = X[i]
        row_id = id // ncols
        col_id = id % ncols
        row_min = row_id
        row_max = row_id + 12
        col_min = col_id
        col_max = col_id + 12
        X_window[i, :, :, :] = bands_matrix_new_Houston[row_min:row_max, col_min:col_max, :]
    # print(X_window.shape)
    return X_window


def import_data(filename):
    """import data according to the first line: nbands nrows ncols"""
    #if extension(filename) == 'mat':
    #    bands_mat = loadmat(filename)
    #    bands_matrix = bands_mat.popitem()[1]
    if extension(filename) == 'tif':
        bands_matrix = loadtif(filename)

        nbands = bands_matrix.shape[2]
        nrows = bands_matrix.shape[0]
        ncols = bands_matrix.shape[1]

        # check scaling to [-1;1]
        eps = 0.1
        if abs(np.max(bands_matrix) - np.min(bands_matrix)) > eps:
            bands_matrix_new = -1 + 2 * (bands_matrix - np.min(bands_matrix)) / (
                    np.max(bands_matrix) - np.min(bands_matrix))
        else:
            bands_matrix_new = bands_matrix
        # construct 2D array
        data = np.empty([nrows * ncols, nbands])
        if len(bands_matrix.shape) > 2:
            for i in range(nrows):
                for j in range(ncols):
                    data[i * ncols + j, :] = bands_matrix_new[i, j, :]
        else:
            for i in range(nrows):
                data[i, :] = bands_matrix_new[i, :]
    else:
        try:
            archive = zipfile.ZipFile(filename, 'r')
            f = archive.open(filename[:-4], 'r')
        except:
            f = open(filename, 'r')
        words = []
        for line in f.readlines():
            for word in line.split():
                words.append(word)
        nbands = np.int_(words[0])
        nrows = np.int_(words[1])
        ncols = np.int_(words[2])

        # training set: number of pixels with nbands -> number of inputs
        offset = 3  # offset is due to header (nbands,nrows,ncols) in words
        data = np.empty([nrows * ncols, nbands])
        if ncols > 1:
            for row in range(nrows):
                for col in range(ncols):
                    for i in range(nbands):
                        gidx = (col * nrows + row) * nbands + i + offset
                        data[row * ncols + col, i] = np.float32(words[gidx])
        else:
            for row in range(nrows):
                for i in range(nbands):
                    gidx = i * nrows + row + offset
                    data[row, i] = np.float32(words[gidx])

        f.close()
        # pdb.set_trace()
    return nbands, nrows, ncols, data


def import_labels(filename):
    """import data according to the first line: nrows ncols"""
    if extension(filename) == 'mat':
        labels_mat = hdf5storage.loadmat(filename)
        labels_matrix = labels_mat.popitem()[1]
        nrows = labels_matrix.shape[0]
        ncols = labels_matrix.shape[1]
        labels = labels_matrix.reshape(nrows * ncols)
    else:
        try:
            archive = zipfile.ZipFile(filename, 'r')
            f = archive.open(filename[:-4], 'r')
        except:
            f = open(filename, 'r')
        words = []
        for line in f.readlines():
            for word in line.split():
                words.append(word)
        nrows = np.int_(words[0])
        ncols = np.int_(words[1])
        labels = np.zeros(nrows * ncols)
        offset = 2  # offset is due to header (nrows,ncols) in words
        for row in range(nrows):
            for col in range(ncols):
                labels[row + col * nrows] = np.float32(words[row + col * nrows + offset])

        f.close()
    return nrows, ncols, labels


def export_data(filename, X, nbands):
    """export data according to the first line: nbands nrows ncols"""
    f = open(filename, 'a')
    n_pixels = len(X)
    f.write('{} {} 1\n'.format(nbands, n_pixels))
    for i in range(n_pixels):
        a = X[i]
        np.savetxt(f, a, fmt="%.15f")
    f.close()

def split_train_test( X, ratio):
    num_GT = X.shape[0]
    Train = X[:int(num_GT * ratio)]
    Test = X[int(num_GT * ratio):]
    return Train, Test

def train_test_preprocess(Train, Test):
    num_train = Train.shape[0]
    num_test = Test.shape[0]
    x_train = np.stack(Train[:, 0], axis=0)
    x_test = np.stack(Test[:, 0], axis=0)
    y_train = Train[:, 1].astype('float16')
    y_train = np.reshape(y_train, [num_train, 1])
    y_test = Test[:, 1].astype('float16')
    y_test = np.reshape(y_test, [num_test, 1])
    return x_train, y_train, x_test, y_test



def export_labels(filename, y):
    """import data according to the first line: nbands nrows ncols"""
    f = open(filename, 'w')
    n_rows = y.shape[0]
    try:
        n_cols = y.shape[1]
    except:
        n_cols = 1
    f.write('{} {}\n'.format(n_rows, n_cols))

    def end_of_line(idx, n_cols):
        if idx == n_cols - 1:
            f.write('\n')
            idx = 0
        else:
            idx = idx + 1
        return idx

    idx = 0
    for elem in y:
        try:
            for e in elem:
                f.write(' {:.0f}'.format(e))
                idx = end_of_line(idx, n_cols)
        except:
            f.write(' {:.0f}'.format(elem))
            idx = end_of_line(idx, n_cols)
    f.close()


def extension(filename):
    return filename[-3:]


def load_zerodata(filename):
    try:
        zerodata = pd.read_csv(filename, delimiter="\t")
    except:
        print("No '%s' file exists!" % filename)
    return zerodata


def save_zerodata(zerodata, filename):
    """save data from zero class"""
    print('zerodata.shape = ', zerodata.shape)
    if zerodata.shape[0] > 0:
        zerodata.to_csv(filename, sep='\t')
    else:
        print('zerodata.shape = ', zerodata.shape)
        print("No 'zerodata' to save!")


def load_train_test(train_filename, train_labels_filename, test_filename, test_labels_filename):
    """import preprocessed train and test data"""
    [nbands_train, nrows_train, ncols_train, X_train] = import_data(train_filename)
    [nrows_train, ncols_train, y_train] = import_labels(train_labels_filename)

    # create dataframe train

    alldata_train = pd.DataFrame(X_train.reshape(X_train.shape[0], X_train.shape[1]))
    alldata_train['labels'] = y_train
    alldata_train['labels'] = alldata_train['labels'].astype('int64')
    # # filter zero classes
    zerodata_train = alldata_train[alldata_train.labels == 0]
    alldata_train = alldata_train[alldata_train.labels != 0]

    [nbands_test, nrows_test, ncols_test, X_test] = import_data(test_filename)
    [nrows_test, ncols_test, y_test] = import_labels(test_labels_filename)

    # create dataframe test
    alldata_test = pd.DataFrame(X_test.reshape(X_test.shape[0], X_test.shape[1]))
    alldata_test['labels'] = y_test
    alldata_test['labels'] = alldata_test['labels'].astype('int64')
    # filter zero classes
    zerodata_test = alldata_test[alldata_test.labels == 0]
    alldata_test = alldata_test[alldata_test.labels != 0]

    zerodata = pd.concat([zerodata_train, zerodata_test])

    # zerodata_filename = 'zerodata.csv'
    # save_zerodata(zerodata,zerodata_filename)

    X_train = alldata_train.iloc[:, :-1]
    y_train = alldata_train.iloc[:, -1]
    X_test = alldata_test.iloc[:, :-1]
    y_test = alldata_test.iloc[:, -1]

    if nbands_train == nbands_test:
        nbands = nbands_train
    else:
        print("Error in data files")
        sys.exit(1)
    return nbands, nrows_train, ncols_train, X_train, X_test, y_train, y_test, zerodata


def debug_print(filename, arr):
    file = open(filename, 'w')
    for elem in arr:
        file.write('{}\n'.format(elem))
    file.close()


def save_train_history(hist_dict, filename):
    """ save train history"""
    hist_df = pd.DataFrame(hist_dict)
    if extension(filename) == 'csv':
        with open(filename, 'w') as f:
            hist_df.to_csv(f, sep='\t')
    elif extension(filename) == 'mat':
        savemat(filename, {
            'loss': hist_df['loss'].to_numpy(),
            'accuracy': hist_df['accuracy'].to_numpy(),
            'val_loss': hist_df['val_loss'].to_numpy(),
            'val_accuracy': hist_df['val_accuracy'].to_numpy()
        })
    elif extension(filename) == 'txt':
        with open(filename, 'w') as f:
            f.write("loss\taccuracy\tval_loss\tval_accuracy\n")
            np.savetxt(f, hist_df.to_numpy(), delimiter='\t')
