import h5py;
import numpy as np;
import sys
from tqdm import tqdm
import json

def is_street(x):
    obj = json.loads(x)
    return ("highway" in obj)

if __name__=="__main__":
    street_indices = None
    if len(sys.argv) != 2:
        print("Usage: streets_sequential input.h5")
        sys.exit(-1)

    # This with block deletes the table streets_idx 
    with h5py.File(sys.argv[1], "a") as f:
        if "streets_idx" in f["osm"]:
            print( "Deleting old table streets_idx")
            del f["osm"]["streets_idx"]

    # We vectorize the predicate function to use it over numpy arrays
    vpredicate = np.vectorize(is_street)
    # Open the file
    with h5py.File(sys.argv[1], "a") as f:
        lsi = f["osm"]["linestrings_idx"] # Line String Indices
        lsc = f["osm"]["linestrings"]     # Line String Coordinates
        attr = f["osm"]["ways_attr"]      # Attributes

        # Create a new index space
        f["osm"].create_dataset("streets_idx", (0,2), maxshape=(None, 2), chunks=(1024,2), dtype=np.uint32)
        streets_idx = f["osm"]["streets_idx"]
        
        for s in tqdm(attr.iter_chunks()): # for all blocks of attributes    
            attrib_block = attr[s][:,0]
            decision = vpredicate(attrib_block).nonzero()[0] # decide
            decision += s[0].start                           # turn indices from local array to global

            # Create or Append to street_indices
            if street_indices is None:
                street_indices = decision.astype(np.uint32).flatten() 
            else:
                street_indices = np.hstack([street_indices, decision.astype(np.uint32).flatten()])
            
        
        print( "Finding data for streets")
        lsi = lsi[:]                  # Materialize linestrings
        lsi = lsi[street_indices,:]   # Apply selection
        streets_idx.resize(lsi.shape) # Prepare Storage
        streets_idx[:] = lsi          # Store
        # The End
            
