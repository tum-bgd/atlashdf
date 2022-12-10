import h5py

"""
Currently, quite a few triangles have zero coordinates. 
In fact, the first two of them had the following degeneracy in addition:
they consisted of only two points according to the index table.

Let us see whehter this holds for all:

"""
from tqdm import tqdm
import h5py
import numpy as np

f = h5py.File("../berlin.h5")["osm"]
out = open("triangles.csv","w");
p = f["triangles"][:] # all points
i = f["triangles_idx"][:] # indices

for j,(s,e) in tqdm(enumerate(i)):
    if (e-s)%3 != 0:
        continue
    # check the others for not containing a zero
    p2 = p[s:e,:]
    x = np.linalg.norm(p2,axis=1)
    if np.any(x<0.001):
        print("Fatal bad triangles at %d" %(j))
    # for complete debug, let us spell out all triangles as WKT
    for a,b,c,d,e,f in p2.reshape(-1,6):
        
        print("POLYGON ((%f %f, %f %f, %f %f))" %(a,b,c,d,e,f),file=out)
    
