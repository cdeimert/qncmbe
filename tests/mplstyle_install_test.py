from qncmbe.plotting import load_plot_style

import matplotlib.pyplot as plt
import numpy as np

load_plot_style('qncmbe', update_style_files=False)

x = np.linspace(0, 10, 1000)
y = np.sin(x)

plt.plot(x, y)
plt.show()
