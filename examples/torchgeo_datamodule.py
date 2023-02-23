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
    RandomGeoSampler,
    RandomBatchGeoSampler,
    get_random_bounding_box,
)
from torchgeo.datamodules import GeoDataModule
from torchgeo.trainers import SemanticSegmentationTask
from pytorch_lightning import Trainer

import atlashdf_rs


class Sentinel2(RasterDataset):
    filename_glob = "Oberbayer_10m_3035_4bands.tif"
    is_image = True
    separate_files = False
    all_bands = ["B01", "B02", "B03", "B04"]
    rgb_bands = ["B01", "B02", "B03"]


class WaterMask(RasterDataset):
    filename_glob = "*mask.tif"
    is_image = False
    separate_files = False


class DynamicMask(GeoDataset):
    def __init__(self, atlashdf=None, ds=None, transforms=None):
        super().__init__(transforms)
        self.atlashdf = atlashdf
        self._crs = ds.crs
        self.res = ds.res
        self.index = ds.index

    def __getitem__(self, query):
        width = round((query.maxx - query.minx) / self.res)
        height = round((query.maxy - query.miny) / self.res)

        mask = atlashdf_rs.get_mask(
            width=width,
            height=height,
            bbox=[query.minx, query.miny, query.maxx, query.maxy],
            bbox_crs=self.crs.to_string(),
            collections=[
                f"{self.atlashdf}/osm/ways_triangles",
                f"{self.atlashdf}/osm/relations_triangles",
            ],
            crs=self.crs.to_string(),
        )

        mask = np.resize(mask, (1, height, width))
        mask = torch.tensor(mask.astype(np.int32)).long()

        sample = {"crs": self.crs, "bbox": query, "mask": mask}

        if self.transforms is not None:
            sample = self.transforms(sample)

        return sample


class CustomDataset(IntersectionDataset):
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
        image = sample["image"][rgb_indices].permute(1, 2, 0)
        image = torch.clamp(image / 10000, min=0, max=1).numpy()

        # Get mask
        cmap = plt.get_cmap("Set1")
        mask = sample["mask"][0].numpy()
        mask = np.delete(cmap(mask), 3, 2)

        # Plot the image
        fig, ax = plt.subplots(1, 2)
        ax[0].imshow(image)
        ax[0].set_title("Sentinel 2")
        ax[1].imshow(mask)
        ax[1].set_title("Mask")

        return fig


class CustomSampler(RandomGeoSampler):
    def __init__(self, dataset, size, length, max_trials=100, threshold=0.01, **kwargs):
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
                mask = dataset.datasets[1].__getitem__(bounding_box)["mask"]
                if torch.count_nonzero(mask) / torch.numel(mask) > self.threshold:
                    break

            yield bounding_box


class CustomBatchSampler(RandomBatchGeoSampler):
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
                    mask = dataset.datasets[1].__getitem__(bounding_box)["mask"]
                    if torch.count_nonzero(mask) / torch.numel(mask) > self.threshold:
                        break

                batch.append(bounding_box)
            yield batch


class CustomDataModule(GeoDataModule):
    def setup(self, stage: str):
        if stage in ["fit"]:
            self.train_dataset = self.dataset_class(  # type: ignore[call-arg]
                split="train", **self.kwargs
            )
            self.train_batch_sampler = CustomBatchSampler(
                self.train_dataset, self.patch_size, self.batch_size, self.length
            )
        if stage in ["fit", "validate"]:
            self.val_dataset = self.dataset_class(  # type: ignore[call-arg]
                split="val", **self.kwargs
            )
            self.val_sampler = CustomSampler(
                self.val_dataset,
                self.patch_size,
                100,
                1000,
                0.1,
            )
        if stage in ["test"]:
            self.test_dataset = self.dataset_class(  # type: ignore[call-arg]
                split="test", **self.kwargs
            )
            self.test_sampler = CustomSampler(
                self.test_dataset, self.patch_size, 100, 1000, 0.1
            )


# torch.manual_seed(76)  # FIXME: errors in notebook

# plot some image and mask
dataset = CustomDataset()
sampler = CustomSampler(dataset, size=256, length=1, max_trials=100, threshold=0.01)
dataloader = DataLoader(dataset, sampler=sampler, collate_fn=stack_samples)

for batch in dataloader:
    sample = unbind_samples(batch)[0]
    dataset.plot(sample)
    plt.show()


# setup datamodule
datamodule = CustomDataModule(
    dataset_class=CustomDataset,
    batch_size=16,
    patch_size=64,
    length=50 * 64,
    num_workers=6,
)

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
    learning_rate_schedule_patience=6,
)

# train
trainer = Trainer(
    accelerator="gpu",
    devices=1,
    max_epochs=10,
    default_root_dir="../data",
)
trainer.fit(model=task, datamodule=datamodule)  # FIXME: cuda is not happy in notebook
