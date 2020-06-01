from qncmbe.plotting import styles

import matplotlib.pyplot as plt
import numpy as np

styles.use('qncmbe')

x = np.linspace(0, 10, 1000)
y = np.sin(x)

plt.plot(x, y)
plt.show()
