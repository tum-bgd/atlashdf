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
from pytorch_lightning import Trainer


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


# import atlashdf_rs
# class DynamicMask(GeoDataset):
#     def __init__(self, atlashdf=None, ds=None, transforms=None):
#         super().__init__(transforms)
#         self.atlashdf = atlashdf
#         self._crs = ds.crs
#         self.res = ds.res
#         self.index = ds.index

#     def __getitem__(self, query):
#         width = round((query.maxx - query.minx) / self.res)
#         height = round((query.maxy - query.miny) / self.res)

#         mask = atlashdf_rs.get_mask(
#             width=width,
#             height=height,
#             bbox=[query.minx, query.miny, query.maxx, query.maxy],
#             bbox_crs=self.crs.to_string(),
#             collections=[
#                 f"{self.atlashdf}/osm/ways_triangles",
#                 f"{self.atlashdf}/osm/relations_triangles",
#             ],
#             crs=self.crs.to_string(),
#         )

#         mask = np.resize(mask, (1, height, width))
#         mask = torch.tensor(mask.astype(np.int32)).long()

#         sample = {"crs": self.crs, "bbox": query, "mask": mask}

#         if self.transforms is not None:
#             sample = self.transforms(sample)

#         return sample


class CustomDataset(IntersectionDataset):
    """Custom instersetion dataset with hardcoded dataset intialization."""

    def __init__(self, split="train", download=False, **kwargs):
        sentinel = Sentinel2("../data/Sentinel-2", **kwargs)
        mask = WaterMask("../data", **kwargs)
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
        mask = mask.reshape((*mask.shape, 1)) # make torch lightning pass soundness checks

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


# torch.manual_seed(76)


# --------------------------------------------------------------------------- #
# dataloader
# --------------------------------------------------------------------------- #

# setup datamodule
datamodule = CustomDataModule(
    dataset_class=CustomDataset,
    batch_size=64,
    patch_size=64,
    length=4000,
    num_workers=6,
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
    model="unet",
    backbone="resnet34",
    weights="imagenet",
    in_channels=4,
    num_classes=2,
    loss="ce",
    ignore_index=None,
    learning_rate=0.1,
    learning_rate_schedule_patience=5,
)

# setup trainer
trainer = Trainer(
    accelerator="gpu",
    devices=1,
    max_epochs=50,
    default_root_dir="../data",
    log_every_n_steps=10,
)

# train
trainer.fit(model=task, datamodule=datamodule)


# --------------------------------------------------------------------------- #
# inference
# --------------------------------------------------------------------------- #

# make predictions
predictions = trainer.predict(datamodule=datamodule)

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

plt.subplot()
plt.imshow(pred)
plt.show()

# save prediction
import rasterio


with rasterio.open(
    "../data/prediction.tif",
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype=pred.dtype,
    crs=ds.crs,
    transform=rasterio.Affine(
        ds.res, 0.0, ds.bounds.minx, 0.0, -ds.res, ds.bounds.maxy
    ),
    # compress="JPEG", // FIXME: generates pseudo classes which break the training task
) as dst:
    dst.write(pred, 1)


# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #
import rasterio as rio
import geopandas as gp
from shapely.geometry import box
from sklearn.metrics import f1_score


# load predicion
pred = rio.open("../data/prediction.tif")
values = pred.read(1)
bounds = box(*pred.bounds)

# load validation
df = gp.read_file("../data/Validation_Bavaria/validations.shp")

# extract predition values
df["pred"] = df.geometry.to_crs(pred.crs).centroid.apply(
    lambda p: values[pred.index(p.x, p.y)] if bounds.contains(p) else None
)

df = df[df["pred"].notnull()]  # filter

# calculate f1 score
y_true = df["ValValue"].apply(lambda x: 1 if x == "5" else 0)
y_pred = df["pred"]

f1_score(y_true, y_pred)
