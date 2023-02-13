import atlashdf_rs
from PIL import Image

print(atlashdf_rs.proj_info())

h5file = "/home/balthasar/git/atlashdf/data/oberbayern-water-earcut.h5"
tiff = "/home/balthasar/git/atlashdf/data/oberbayern_S2_10m_subset.tiff"

mask = atlashdf_rs.get_mask(h5file, tiff)
Image.fromarray(mask)