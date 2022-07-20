import tensorflow.keras as keras
# from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import add
from tensorflow.keras.layers import concatenate, maximum
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten, BatchNormalization
from tensorflow.keras.layers import Conv2D, MaxPooling2D, AveragePooling2D
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.utils import to_categorical
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import matthews_corrcoef
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report

import numpy as np
import math 
from datetime import datetime

from hsi_io import *
import os
import time



def lr_schedule(epoch):
    """Learning Rate Schedule

    Learning rate is scheduled to be reduced after 80, 120, 160, 180 epochs.
    Called automatically every epoch as part of callbacks during training.

    # Arguments
        epoch (int): The number of epochs

    # Returns
        lr (float32): learning rate
    """
    lr = 0.01
    if epoch > 400:
        lr *= 0.5e-3
    elif epoch > 300:
        lr *= 0.5e-3
    elif epoch > 200:
        lr *= 1e-3
    elif epoch > 150:
        lr *= 1e-2
    elif epoch > 80:
        lr *= 1e-1
    print('Learning rate: ', lr)
    return lr


def resnet_layer(inputs,
                 num_filters=16,
                 kernel_size=5,
                 strides=1,
                 activation='relu',
                 batch_normalization=True,
                 conv_first=True):
    """2D Convolution-Batch Normalization-Activation stack builder

    # Arguments
        inputs (tensor): input tensor from input image or previous layer
        num_filters (int): Conv2D number of filters
        kernel_size (int): Conv2D square kernel dimensions
        strides (int): Conv2D square stride dimensions
        activation (string): activation name
        batch_normalization (bool): whether to include batch normalization
        conv_first (bool): conv-bn-activation (True) or
            bn-activation-conv (False)

    # Returns
        x (tensor): tensor as input to the next layer
    """
    conv = Conv2D(num_filters,
                  kernel_size=kernel_size,
                  strides=strides,
                  padding='same')

    x = inputs
    if conv_first:
        x = conv(x)
        if batch_normalization:
            x = BatchNormalization()(x)
        if activation is not None:
            x = Activation(activation)(x)
    else:
        if batch_normalization:
            x = BatchNormalization()(x)
        if activation is not None:
            x = Activation(activation)(x)
        x = conv(x)
    return x


def resnet_v2(input_shape, depth, num_classes=13):
    """ResNet Version 2 Model builder [b]

    Stacks of (1 x 1)-(5 x 5)-(1 x 1) BN-ReLU-Conv2D or also known as
    bottleneck layer
    First shortcut connection per layer is 1 x 1 Conv2D.
    Second and onwards shortcut connection is identity.
    At the beginning of each stage, the feature map size is halved (downsampled)
    by a convolutional layer with strides=2, while the number of filter maps is
    doubled. Within each stage, the layers have the same number filters and the
    same filter map sizes.
    Features maps sizes:
    conv1  : 32x32,  16
    stage 0: 32x32,  64
    stage 1: 16x16, 128
    stage 2:  8x8,  256

    # Arguments
        input_shape (tensor): shape of input image tensor
        depth (int): number of core convolutional layers
        num_classes (int): number of classes (CIFAR10 has 10)

    # Returns
        model (Model): Keras model instance
    """
    if (depth - 2) % 9 != 0:
        raise ValueError('depth should be 9n+2 (eg 56 or 110 in [b])')
    # Start model definition.
    num_filters_in = 16
    num_res_blocks = int((depth - 2) / 9)

    inputs = Input(shape=input_shape)
    # v2 performs Conv2D with BN-ReLU on input before splitting into 2 paths
    x = resnet_layer(inputs=inputs,
                     num_filters=num_filters_in,
                     conv_first=True)

    # Instantiate the stack of residual units
    for stage in range(3):
        for res_block in range(num_res_blocks):
            activation = 'relu'
            batch_normalization = True
            strides = 1
            if stage == 0:
                num_filters_out = num_filters_in * 4
                if res_block == 0:  # first layer and first stage
                    activation = None
                    batch_normalization = False
            else:
                num_filters_out = num_filters_in * 2
                if res_block == 0:  # first layer but not first stage
                    strides = 2  # downsample

            # bottleneck residual unit
            y = resnet_layer(inputs=x,
                             num_filters=num_filters_in,
                             kernel_size=1,
                             strides=strides,
                             activation=activation,
                             batch_normalization=batch_normalization,
                             conv_first=False)
            y = resnet_layer(inputs=y,
                             num_filters=num_filters_in,
                             conv_first=False)
            y = resnet_layer(inputs=y,
                             num_filters=num_filters_out,
                             kernel_size=1,
                             conv_first=False)
            if res_block == 0:
                # linear projection residual shortcut connection to match
                # changed dims
                x = resnet_layer(inputs=x,
                                 num_filters=num_filters_out,
                                 kernel_size=1,
                                 strides=strides,
                                 activation=None,
                                 batch_normalization=False)
            x = keras.layers.add([x, y])

        num_filters_in = num_filters_out

    # Add classifier on top.
    # v2 has BN-ReLU before Pooling
    x = BatchNormalization()(x)
    x = Activation('relu')(x)
    x = AveragePooling2D(pool_size=3)(x)
    y = Flatten()(x)
    outputs = Dense(num_classes,
                    activation='softmax',
                    kernel_initializer='he_normal')(y)

    # Instantiate model.
    model = Model(inputs=inputs, outputs=outputs)
    return model


###########  Hyperparameters #############
batch_size = 256
num_classes = 12
epochs = 500

data_augmentation = False
save_dir = os.path.join(os.getcwd(), 'saved_models')
model_name = 'DE_10ba_1k_SP_trained_model_single_10m.h5'
filepath = r"DE_10ba_1k_SP_Best_model_single_10m.hdf5"


###########  Data Import #############
Train = r"./data/DE_10ba_1k_SP_std_train_samples.npy"
Test = r"./data/DE_10ba_1k_SP_std_val_samples.npy"
Train = np.load(Train, allow_pickle=True)
Test = np.load(Test, allow_pickle=True)
X_train, y_train, X_test, y_test = train_test_preprocess(Train, Test)
X_train = X_train.astype('float16')
X_test = X_test.astype('float16')
y_train = to_categorical(y_train, 13)
y_test = to_categorical(y_test, 13)
print('Data Pratation is ready.')



################################################
input = X_train.shape[1:]
### #########################################

model = resnet_v2(input_shape=input, depth=29)

# initiate RMSprop optimizer

opt = keras.optimizers.Nadam(lr=lr_schedule(0), beta_1=0.9, beta_2=0.999)

model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])
model.summary()
# ###############l#################################
# Train the model
#training logging
logdir = "logs/fit/" + datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir, histogram_freq=1)

# checkpoint
checkpoint = ModelCheckpoint(filepath, monitor='val_accuracy', save_best_only=True, mode='max')

model.fit(X_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          callbacks=[checkpoint, tensorboard_callback],
          validation_data=(X_test, y_test))


# ## # ################################################
# Save model and weights
model_path = os.path.join(save_dir, model_name)
model.load_weights(filepath)
if not os.path.isdir(save_dir):
    os.makedirs(save_dir)
model_path = os.path.join(save_dir, model_name)
model.save(model_path)
print('Saved trained model at %s ' % model_path)

# # ################################################
### Score the trained model.

model = load_model(model_path)
start = time.time()
X_test = X_test.astype('float16')
y_test_pre = model.predict(X_test, verbose=0)
end = time.time()
y_test_time = end - start
y_test_pre = np.argmax(y_test_pre, axis=1)
print(len(y_test_pre))
y_test = np.argmax(y_test, axis=1)
print('classification accuracy', accuracy_score(y_test, y_test_pre))
print('cohen kappa', cohen_kappa_score(y_test, y_test_pre))
cm = confusion_matrix(y_test, y_test_pre)

cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
classes_indi = cm.diagonal()
print('classes individual accuracy', classes_indi)
print('average accuracy', sum(classes_indi) / 12)
print('prediction time', y_test_time )



