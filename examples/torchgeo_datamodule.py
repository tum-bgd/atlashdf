from matplotlib import pyplot as plt
import torch
from torch.utils.data import DataLoader
from torchgeo.datasets import (
    RasterDataset,
    IntersectionDataset,
    stack_samples,
    unbind_samples,
)
from torchgeo.samplers import RandomGeoSampler
from torchgeo.datamodules import GeoDataModule
from torchgeo.trainers import SemanticSegmentationTask
from pytorch_lightning import Trainer


class Sentinel2(RasterDataset):
    filename_glob = "Oberbayer_10m_3035_4bands.tif"
    is_image = True
    separate_files = False
    all_bands = ["B01", "B02", "B03", "B04"]
    rgb_bands = ["B01", "B02", "B03"]

    def plot(self, sample):
        # Find the correct band index order
        rgb_indices = []
        for band in self.rgb_bands:
            rgb_indices.append(self.all_bands.index(band))

        # Reorder and rescale the image
        image = sample["image"][rgb_indices].permute(1, 2, 0)
        image = torch.clamp(image / 10000, min=0, max=1).numpy()

        # Plot the image
        fig, ax = plt.subplots()
        ax.imshow(image)

        return fig


class WaterMask(RasterDataset):
    filename_glob = "*mask.tif"
    is_image = False
    separate_files = False

    def plot(self, sample):
        image = sample["mask"][0].numpy()

        # Plot the image
        fig, ax = plt.subplots()
        ax.imshow(image)

        return fig


class CustomGeoDataset(IntersectionDataset):
    def __init__(self, split="train", download=False, **kwargs):
        self.sentinel = Sentinel2("../data/Sentinel-2", **kwargs)
        self.mask = WaterMask("../data", **kwargs)

        super().__init__(dataset1=self.sentinel, dataset2=self.mask)

    def plot(self, sample):
        # Find the correct band index order
        rgb_indices = []
        for band in self.sentinel.rgb_bands:
            rgb_indices.append(self.sentinel.all_bands.index(band))

        # Reorder and rescale the image
        image = sample["image"][rgb_indices].permute(1, 2, 0)
        image = torch.clamp(image / 10000, min=0, max=1).numpy()

        # # Get mask
        # mask = sample["mask"][0].numpy()

        # # Plot the image
        # fig, ax = plt.subplots(1, 2)
        # ax[0].imshow(image)
        # ax[0].set_title("Sentinel 2")
        # ax[1].imshow(mask)
        # ax[1].set_title("Mask")

        fig, ax = plt.subplots()
        ax.imshow(image)

        return fig


# torch.manual_seed(1)  # FIXME: errors in notebook

# plot some image and mask
dataset = CustomGeoDataset()
sampler = RandomGeoSampler(dataset, size=256, length=1)
dataloader = DataLoader(dataset, sampler=sampler, collate_fn=stack_samples)

for batch in dataloader:
    sample = unbind_samples(batch)[0]
    dataset.plot(sample)
    plt.show()


# stup datamodule
datamodule = GeoDataModule(
    dataset_class=CustomGeoDataset,
    batch_size=16,
    patch_size=64,
    length=50 * 16,
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