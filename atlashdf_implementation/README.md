# AtlasHDF Implementation

## Batch Resizing (for supporting target_size parameter)
Below, quant_dataset is a batch of (N, 64,64,13) and goes to (N,224,224,13).
```
tf.image.resize(quant_dataset, [224,224])
```