#!/usr/bin/env python3
import sys
from pathlib import Path
from tqdm import tqdm
import numpy as np
import h5py

"""
This exports all triangles into an OGC-compatible WKT file that can be read with QGIS.
"""


def triangle_iterator(f, key):
    p = f[f"{key}_triangles"][:]  # all points
    i = f[f"{key}_triangles_idx"][:]  # indices
    for j, (s, e) in tqdm(enumerate(i)):
        if (e - s) % 3 != 0:
            print("WARNING: This bug should have been closed")
            continue
        # check the others for not containing a zero
        p2 = p[s:e, :]
        x = np.linalg.norm(p2, axis=1)
        if np.any(x < 0.001):
            print("Fatal bad triangles at %d" % (j))

        for a, b, c, d, e, f in p2.reshape(-1, 6):
            yield "POLYGON ((%f %f, %f %f, %f %f))" % (a, b, c, d, e, f)


# Setup input and output path
infile = sys.argv[1] if len(sys.argv) == 2 else "../data/bayern-water.h5"
if not Path(infile).exists():
    raise RuntimeError(f"H5 file not found {infile}")

outfile = Path(infile).with_suffix(".csv")
print("Converting %s => %s" % (infile, outfile))

# Convert data
f = h5py.File(infile)["osm"]
out = open(outfile, "w")

for x in triangle_iterator(f, "relations"):
    print(x, file=out)
for x in triangle_iterator(f, "ways"):
    print(x, file=out)
