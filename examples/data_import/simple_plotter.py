'''
Example script for plotting QNCMBE data.

You must first install the qncmbe python module (see README).
Also, your computer must have access to
\\insitu1.nexus.uwaterloo.ca and \\zw-xp1
'''

from qncmbe.data_import.growths import GrowthDataCollector
import matplotlib.pyplot as plt

from qncmbe.plotting import load_plot_style

load_plot_style('qncmbe', update_style_files=False)


def main():

    start_time = "2019-09-24 17:30"
    end_time = "2019-09-24 20:30"

    names = [
        "Al1 base measured",
        "Al1 tip measured"
    ]

    simple_plot(start_time, end_time, names)

    plt.show()


def simple_plot(start_time, end_time, names):

    collector = GrowthDataCollector(start_time, end_time, names)

    data = collector.get_data()

    fig, ax = plt.subplots()

    for name in names:
        data[name].plot(fig, ax)

    return fig, ax


if __name__ == "__main__":
    main()
