from pathlib import Path
from matplotlib import pyplot as plt
import numpy as np
import torch
from torch.utils.data import DataLoader
from torchgeo.datasets import (
    BoundingBox,
    GeoDataset,
    RasterDataset,
    IntersectionDataset,
    stack_samples,
    unbind_samples,
)
from torchgeo.samplers import (
    GridGeoSampler,
    RandomGeoSampler,
    RandomBatchGeoSampler,
    get_random_bounding_box,
)
from torchgeo.datamodules import GeoDataModule
from torchgeo.trainers import SemanticSegmentationTask
from lightning import Trainer
from pytorch_lightning.loggers import TensorBoardLogger
import rasterio as rio
import geopandas as gp
from shapely.geometry import box
from sklearn.metrics import (
    matthews_corrcoef,
    precision_score,
    recall_score,
    accuracy_score,
    f1_score,
)


DATA = Path(__file__).parent.joinpath("../data").resolve()


class Sentinel2(RasterDataset):
    """Custom Sentinel 2 raster dataset."""

    filename_glob = "Oberbayer_10m_3035_4bands.tif"
    is_image = True
    separate_files = False
    all_bands = ["B01", "B02", "B03", "B04"]
    rgb_bands = ["B01", "B02", "B03"]


class WaterMask(RasterDataset):
    """Custom water mask raster dataset."""

    filename_glob = "*mask.tif"
    is_image = False
    separate_files = False


class CustomDataset(IntersectionDataset):
    """Custom instersetion dataset with hardcoded dataset intialization."""

    def __init__(self, split="train", download=False, **kwargs):
        sentinel = Sentinel2(DATA.joinpath("Sentinel-2"), **kwargs)
        mask = WaterMask(DATA, **kwargs)
        # FIXME: bad performance, needs some sort of caching and indexing
        # mask = DynamicMask(
        #     atlashdf="../data/oberbayern-water.h5", ds=sentinel, **kwargs
        # )
        super().__init__(dataset1=sentinel, dataset2=mask)

    def plot(self, sample):
        # Find the correct band index order
        rgb_indices = []
        for band in self.datasets[0].rgb_bands:
            rgb_indices.append(self.datasets[0].all_bands.index(band))

        # Reorder and rescale the image
        image = sample["image"][rgb_indices].permute(1, 2, 0)  # reorder
        image = torch.clamp(image * 0.13, 0, 255)  # brighten
        image = (image - image.min()) / (image.max() - image.min())  # normalize
        image = image.numpy()

        # Get mask
        mask = sample["mask"][0].squeeze().numpy().round()
        mask = mask.reshape(
            (*mask.shape, 1)
        )  # make torch lightning pass soundness checks

        # Plot the image
        fig, ax = plt.subplots(1, 2)
        ax[0].imshow(image)
        ax[0].set_title("Sentinel 2")
        ax[1].imshow(mask)
        ax[1].set_title("Mask")

        return fig


class CustomSampler(RandomGeoSampler):
    """Custom random geo sampler to skip unmasked tiles."""

    def __init__(self, dataset, size, length, max_trials=100, threshold=0.01, **kwargs):
        self.dataset = dataset
        self.max_trials = max_trials
        self.threshold = threshold
        super().__init__(dataset, size, length, **kwargs)

    def __iter__(self):
        for _ in range(len(self)):
            # Choose a random tile, weighted by area
            idx = torch.multinomial(self.areas, 1)
            hit = self.hits[idx]
            bounds = BoundingBox(*hit.bounds)

            # Choose a random non-empty index within that tile
            for _ in range(self.max_trials):
                # Choose a random index within that tile
                bounding_box = get_random_bounding_box(bounds, self.size, self.res)

                # Test wether the amount of classified pixels exceedes threshold
                mask = self.dataset.datasets[1][bounding_box]["mask"]
                if torch.count_nonzero(mask) / torch.numel(mask) > self.threshold:
                    break

            yield bounding_box


class CustomBatchSampler(RandomBatchGeoSampler):
    """Custom random bactch geo sampler to skip unmasked tiles."""

    def __init__(
        self,
        dataset,
        size,
        batch_size,
        length,
        max_trials=100,
        threshold=0.01,
        **kwargs,
    ):
        self.max_trials = max_trials
        self.threshold = threshold
        self.dataset = dataset
        super().__init__(dataset, size, batch_size, length, **kwargs)

    def __iter__(self):
        for _ in range(len(self)):
            # Choose a random tile, weighted by area
            idx = torch.multinomial(self.areas, 1)
            hit = self.hits[idx]
            bounds = BoundingBox(*hit.bounds)

            # Choose random indices within that tile
            batch = []
            for _ in range(self.batch_size):
                for _ in range(self.max_trials):
                    bounding_box = get_random_bounding_box(bounds, self.size, self.res)

                    # Test wether the amount of classified pixels exceedes threshold
                    mask = self.dataset.datasets[1][bounding_box]["mask"]
                    if torch.count_nonzero(mask) / torch.numel(mask) > self.threshold:
                        break

                batch.append(bounding_box)
            yield batch


class CustomDataModule(GeoDataModule):
    """Custom geo data module using custom samplers."""

    def setup(self, stage: str):
        if stage in ["fit"]:
            self.train_dataset = self.dataset_class(**self.kwargs)
            self.train_batch_sampler = CustomBatchSampler(
                self.train_dataset, self.patch_size, self.batch_size, self.length
            )
        if stage in ["fit", "validate"]:
            self.val_dataset = self.dataset_class(**self.kwargs)
            self.val_sampler = CustomSampler(
                self.val_dataset, self.patch_size, 200, 1000, 0.1
            )
        if stage in ["test"]:
            self.test_dataset = self.dataset_class(**self.kwargs)
            self.test_sampler = CustomSampler(
                self.test_dataset, self.patch_size, 100, 1000, 0.1
            )
        if stage in ["predict"]:
            self.predict_dataset = self.dataset_class(**self.kwargs)
            self.predict_sampler = GridGeoSampler(
                dataset=self.predict_dataset,
                size=self.patch_size,
                stride=self.patch_size,
            )


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #

# basic configuration
config = {
    "model": "unet",
    "backbone": "resnet50",
    "weights": "imagenet",
    "loss": "ce",
    "batch_size": "64",
    "patch_size": "64",
    "samples": "4000",
    "epochs": "20",
    "lr": "0.1",
}

# make it configurable from the command line
if __name__ == "__main__" and not callable(globals().get("get_ipython", None)):
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--model", help="Specify network model")
    parser.add_argument("--backbone", help="Specify backbone")
    parser.add_argument("--weights", help="Specify weights")
    parser.add_argument("--loss", help="Specify loss")
    parser.add_argument("--batch_size", help="Specify batch size")
    parser.add_argument("--patch_size", help="Specify patch size")
    parser.add_argument("--samples", help="Specify number of samples")
    parser.add_argument("--epochs", help="Specify number of epochs")
    parser.add_argument("--lr", help="Specify learning rate")

    args = parser.parse_args()

    # update config from commandline args
    for k, v in vars(args).items():
        if v is not None:
            config[k] = v


print(f"{config=}")

torch.manual_seed(76)

# --------------------------------------------------------------------------- #
# dataloader
# --------------------------------------------------------------------------- #

# setup datamodule
datamodule = CustomDataModule(
    dataset_class=CustomDataset,
    batch_size=int(config["batch_size"]),
    patch_size=int(config["patch_size"]),
    length=int(config["samples"]),
    num_workers=4,
)

# plot some image and mask
dataset = CustomDataset()
sampler = CustomSampler(dataset, size=256, length=1, max_trials=100, threshold=0.01)
dataloader = DataLoader(dataset, sampler=sampler, collate_fn=stack_samples)

for batch in dataloader:
    sample = unbind_samples(batch)[0]
    dataset.plot(sample)
    plt.show()

# --------------------------------------------------------------------------- #
# training
# --------------------------------------------------------------------------- #

# setup segmentation task
task = SemanticSegmentationTask(
    model=config["model"],
    backbone=config["backbone"],
    weights=config["weights"],
    in_channels=4,
    num_classes=2,
    loss=config["loss"],
    ignore_index=None,
    learning_rate=float(config["lr"]),
    learning_rate_schedule_patience=6,
)

logger = TensorBoardLogger(
    DATA.joinpath("lightning_logs"),
    name="{}-{}".format(config["model"], config["backbone"]),
    version=config["samples"],
)

# setup trainer
trainer = Trainer(
    accelerator="gpu",
    devices=1,
    max_epochs=int(config["epochs"]),
    default_root_dir=DATA,
    log_every_n_steps=10,
    logger=logger,
)

# train
trainer.fit(model=task, datamodule=datamodule)

# --------------------------------------------------------------------------- #
# inference
# --------------------------------------------------------------------------- #

# make predictions
predictions = trainer.predict(datamodule=datamodule, ckpt_path="last")

# assemble prediction patches
datamodule.setup("predict")
ds = datamodule.predict_dataset

width = round((ds.bounds.maxx - ds.bounds.minx) / ds.res)
height = round((ds.bounds.maxy - ds.bounds.miny) / ds.res)
pred = np.zeros((height, width))

for i, batch in enumerate(datamodule.predict_dataloader()):
    for j, sample in enumerate(unbind_samples(batch)):
        p = predictions[i][j]
        p = p[1].squeeze().numpy().round()

        bounds = sample["bbox"]

        col = round((bounds.minx - ds.bounds.minx) / ds.res)
        row = round((ds.bounds.maxy - bounds.maxy) / ds.res)

        pred[row : row + p.shape[0], col : col + p.shape[1]] = p.astype("int8")

# save prediction
with rio.open(
    DATA.joinpath("prediction.tif"),
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype=pred.dtype,
    crs=ds.crs,
    transform=rio.Affine(ds.res, 0.0, ds.bounds.minx, 0.0, -ds.res, ds.bounds.maxy),
    # compress="JPEG", // FIXME: generates pseudo classes which break the training task
) as dst:
    dst.write(pred, 1)

# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #

# load predicion
pred = rio.open(DATA.joinpath("prediction.tif"))
values = pred.read(1)
bounds = box(*pred.bounds)

# load validation
df = gp.read_file(DATA.joinpath("Validation_Bavaria/validations.shp"))

# extract predition values
df["pred"] = df.geometry.to_crs(pred.crs).centroid.apply(
    lambda p: values[pred.index(p.x, p.y)] if bounds.contains(p) else None
)

df = df[df["pred"].notnull()]  # filter

# calculate metrics
y_true = df["ValValue"].apply(lambda x: 1 if x == "5" else 0)
y_pred = df["pred"]

print("Model metrics\n")
print(f"Precision: {precision_score(y_true, y_pred):.2f}")
print(f"Recall:    {recall_score(y_true, y_pred):.2f}")
print(f"Accuracy:  {accuracy_score(y_true, y_pred):.2f}")
print(f"F1:        {f1_score(y_true, y_pred):.2f}")
print(f"MCC:       {matthews_corrcoef(y_true, y_pred):.2f}")


# --------------------------------------------------------------------------- #
# plot
# --------------------------------------------------------------------------- #
import rasterio as rio
from rasterio.plot import reshape_as_image, show
import numpy as np
from matplotlib import pyplot as plt

sentinel = rio.open(DATA.joinpath("Sentinel-2/Oberbayer_10m_3035_4bands.tif"))
mask = rio.open(DATA.joinpath("oberbayern-water-mask.tif"))
pred = rio.open(DATA.joinpath("prediction.tif"))
gswl = rio.open(DATA.joinpath("GSWL/Oberbayer_occurrence_resampled_3035.tif"))

# Reorder and rescale the image
image = reshape_as_image(sentinel.read((3, 2, 1)))
image = np.clip(image * 0.13, 0, 255)  # brighten
image = (image - image.min()) / (image.max() - image.min())  # normalize

# Get mask and pediction
m = np.squeeze(mask.read(1)).round()
p = np.squeeze(pred.read(1)).round()
r = np.squeeze(gswl.read(1) * 0.5).round()

size = 256

l = np.random.rand(6, 2) * (min(m.shape) - size)
l = l.astype("int")
l[1]

# selection
l = np.array(
    [
        [15302, 10720],
        [4783, 856],
        [15688, 6356],
        [14490, 16631],
        [14276, 4348],
        [13725, 17206],
    ]
)

# Plot the selected examples [3 x 8]
fig, axs = plt.subplots(nrows=3, ncols=8, figsize=(12, 5.5))
for i in range(3):
    for j in range(2):
        n = i * 2 + j
        x, y = l[n, 0], l[n, 1]
        axs[i, j * 4].imshow(image[x : x + size, y : y + size, :])
        axs[i, j * 4].set_title(f"Sentinel 2 [{n + 1}]")
        axs[i, j * 4].axis("off")
        axs[i, j * 4 + 1].imshow(m[x : x + size, y : y + size])
        axs[i, j * 4 + 1].set_title(f"Mask [{n + 1}]")
        axs[i, j * 4 + 1].axis("off")
        axs[i, j * 4 + 2].imshow(p[x : x + size, y : y + size])
        axs[i, j * 4 + 2].set_title(f"Prediction [{n + 1}]")
        axs[i, j * 4 + 2].axis("off")
        axs[i, j * 4 + 3].imshow(r[x : x + size, y : y + size])
        axs[i, j * 4 + 3].set_title(f"GSWL [{n + 1}]")
        axs[i, j * 4 + 3].axis("off")
fig.tight_layout()
fig.subplots_adjust(hspace=0)
plt.show()


# --------------------------------------------------------------------------- #
# reference
# --------------------------------------------------------------------------- #

# Global Surface Water Mapping (GSWL)
gswl = rio.open(DATA.joinpath("GSWL/Oberbayer_occurrence_resampled_3035.tif"))
values = gswl.read(1)
bounds = box(*gswl.bounds)

# load validation
df = gp.read_file(DATA.joinpath("Validation_Bavaria/validations.shp"))

# extract gswl values
df["pred"] = df.geometry.to_crs(gswl.crs).centroid.apply(
    lambda p: None
    if not bounds.contains(p)
    else 1
    if values[gswl.index(p.x, p.y)] > 0
    else 0
)

df = df[df["pred"].notnull()]  # filter

# calculate metrics
y_true = df["ValValue"].apply(lambda x: 1 if x == "5" else 0)
y_pred = df["pred"]

print("GSWL metrics\n")
print(f"Precision: {precision_score(y_true, y_pred):.2f}")
print(f"Recall:    {recall_score(y_true, y_pred):.2f}")
print(f"Accuracy:  {accuracy_score(y_true, y_pred):.2f}")
print(f"F1:        {f1_score(y_true, y_pred):.2f}")
print(f"MCC:       {matthews_corrcoef(y_true, y_pred):.2f}")
