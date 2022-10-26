import numpy as np
from matplotlib import pyplot as plt



a = np.genfromtxt("rings.dat");
b = np.genfromtxt("fractured.dat");
print(a)
plt.plot(a[:,0],a[:,1])


plt.plot(b[:,0],b[:,1], c="r")

plt.show()
