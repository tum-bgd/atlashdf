import h5py;
from matplotlib import pyplot as plt;
import sys
import random;
from tqdm import tqdm

class cfg:
    N=1000

if __name__=="__main__":
    f = h5py.File(sys.argv[1],"r");
    f = f["osm"]
    print(f["linestrings_idx"].shape)
    start = random.randint(0, f["linestrings_idx"].shape[0]-cfg.N-1)
    linestrings = f["linestrings_idx"][start:(start+cfg.N)][:]
    for s,e in tqdm(linestrings):
        coords = f["linestrings"][s:e][:]
        plt.plot(coords[:,0],coords[:,1])
    plt.show()
    
