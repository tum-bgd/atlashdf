from matplotlib import pyplot as plt
import torch
from torch.utils.data import DataLoader
from torchgeo.datasets import RasterDataset, stack_samples, unbind_samples
from torchgeo.samplers import RandomGeoSampler


class Sentinel2(RasterDataset):
    filename_glob = "Oberbayer_10m_3035_4bands.tif"
    is_image = True
    separate_files = False
    all_bands = ["Band 01", "Band 02", "Band 03", "Band 04"]
    rgb_bands = ["Band 01", "Band 02", "Band 03"]

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
    filename_glob = "mask.tif"
    is_image = False
    separate_files = False

    def plot(self, sample):
        image = sample["mask"][0].numpy()

        # Plot the image
        fig, ax = plt.subplots()
        ax.imshow(image)

        return fig


torch.manual_seed(1)

# assemble dataset & dataloader
sentinel = Sentinel2("/home/balthasar/git/atlashdf/data/Sentinel-2")
mask = WaterMask("/home/balthasar/git/atlashdf/data")

dataset = sentinel & mask

sampler = RandomGeoSampler(dataset, size=4096, length=3)
dataloader = DataLoader(dataset, sampler=sampler, collate_fn=stack_samples)

# plot some images and masks
for batch in dataloader:
    sample = unbind_samples(batch)[0]
    sentinel.plot(sample)
    plt.axis("off")
    plt.show()
    mask.plot(sample)
    plt.axis("off")
    plt.show()
