#!/usr/bin/env python3
import h5py

"""
This exports all triangles into an OGC-compatible WKT file that can be read with QGIS.
"""
from tqdm import tqdm
import h5py
import numpy as np
import sys

def triangle_iterator(f,key):
    p = f["%s_triangles"%(key)][:] # all points
    i = f["%s_triangles_idx" %(key)][:] # indices
    for j,(s,e) in tqdm(enumerate(i)):
        if (e-s)%3 != 0:
            print("WARNING: This bug should have been closed")
            continue
        # check the others for not containing a zero
        p2 = p[s:e,:]
        x = np.linalg.norm(p2,axis=1)
        if np.any(x<0.001):
            print("Fatal bad triangles at %d" %(j))
    
        for a,b,c,d,e,f in p2.reshape(-1,6):
            yield "POLYGON ((%f %f, %f %f, %f %f))" %(a,b,c,d,e,f)
    


if len(sys.argv) != 2:
    raise RuntimeError("Give the filename to convert")

infile = sys.argv[1]
if not infile.endswith(".h5"):
    raise RuntimeError("H5 file expected")
outfile = infile.rsplit(".",1)[0] + ".csv"
print("Converting %s => %s" %(infile,outfile))


f = h5py.File(infile)["osm"]
out = open(outfile,"w");

for i,x in enumerate(triangle_iterator(f,"relations")):
    print(x, file=out)
for i,x in enumerate(triangle_iterator(f,"ways")):
    print(x,file=out)
    
    
