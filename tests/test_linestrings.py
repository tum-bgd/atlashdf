import sys
from pathlib import Path
import h5py
import random
from tqdm import tqdm
from matplotlib import pyplot as plt


class cfg:
    N = 1000


if __name__ == "__main__":
    infile = sys.argv[1] if len(sys.argv) == 2 else "../data/berlin.h5"
    if not Path(infile).exists():
        raise RuntimeError(f"H5 file not found {infile}")

    f = h5py.File(infile, "r")["osm"]
    print(f["linestrings_idx"].shape)

    start = random.randint(0, f["linestrings_idx"].shape[0] - cfg.N - 1)
    linestrings = f["linestrings_idx"][start : (start + cfg.N)][:]
    for s, e in tqdm(linestrings):
        coords = f["linestrings"][s:e][:]
        plt.plot(coords[:, 0], coords[:, 1])
    plt.show()
