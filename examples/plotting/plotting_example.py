import matplotlib.pyplot as plt
import numpy as np
from numpy import cos, pi

from qncmbe.plotting import styles

styles.use('qncmbe')
styles.use('paper-aip')

x = np.linspace(0, 2*pi, 1000)

N = 8

fig, ax = plt.subplots()
for n in range(N):
    y = cos(x - 2*pi*n/N)
    ax.plot(x, y)

plt.show()
