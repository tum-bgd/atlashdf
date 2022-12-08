import sys
import h5py;
import numpy as np
from matplotlib import pyplot as plt

with h5py.File(sys.argv[1]) as f:
    trp = f["osm"]["triangles"][:]
    tri = f["osm"]["triangles_idx"][:]

    ts = tri[42,:]
    p = trp[ts[0]:ts[1],:]
    print(p.shape)
    p = p.reshape(-1,6)
    for row in p:
        t=row.reshape(-1,2)
        plt.plot(t[:,0],t[:,1])
    plt.show()
#    plt.plot(p[:,0],p[:,1])
#    plt.show()
