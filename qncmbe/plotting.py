'''
Useful functions for plotting with matplotlib

Also installs the mplstyle files which can then be used by calling,
e.g., plt.style.use('qncmbe')
'''

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as clrs
import os
import numpy as np
from distutils.dir_util import copy_tree


def check_installation():

    stylelib_dir = os.path.join(mpl.get_configdir(), 'stylelib')

    this_dir = os.path.dirname(os.path.abspath(__file__))
    qncmbe_styles_dir = os.path.join(this_dir, 'plt_stylelib')

    for name in os.listdir(qncmbe_styles_dir):
        if not os.path.exists(os.path.join(stylelib_dir, name)):
            return False

    return True


def install_mpl_styles():

    stylelib_dir = os.path.join(mpl.get_configdir(), 'stylelib')

    this_dir = os.path.dirname(os.path.abspath(__file__))
    qncmbe_styles_dir = os.path.join(this_dir, 'plt_stylelib')

    print(f'Copying matplotlib styles to "{stylelib_dir}"')
    print("Python may need to be restarted for styles to work correctly.")

    copy_tree(qncmbe_styles_dir, stylelib_dir)


def get_mpl_colors():
    return plt.rcParams['axes.prop_cycle'].by_key()['color']


def darken(c, f=2):
    '''Darken color by factor. E.g., factor=2 returns color half as bright.'''
    return tuple([v/f for v in clrs.to_rgb(c)])


def lighten(c, f=2):
    '''Lighten color by factor.'''

    return tuple([1 - (1-v)/f for v in clrs.to_rgb(c)])


def greyscale(c):
    (r, g, b) = clrs.to_rgb(c)
    return (r + g + b)/3


def scale_figure(fig, scale):
    ''' Return figure rescaled by the given scale factor.

    Arguments:
        fig     matplotlib Figure object
        scale   Scale factor. Either list (width, height) or scalar.
    '''

    size = fig.get_size_inches()
    try:
        fig.set_size_inches(*[s*z for s, z in zip(scale, size)])
    except TypeError:
        fig.set_size_inches(*[scale*z for z in size])
    return fig


def plot_periodic(ax, x, y, nper=[0.2, 0.2], reset_zero=False, **kwargs):
    '''Plot function, and extend it periodically.

    Arguments:
        ax          matplotlib Axes object
        x,y         x and y data (numpy arrays. x must be evenly spaced)
        nper        Number of periods by which to extend the plot left and
                    right. E.g. nper=[0.5,0.25] will plot the function plus 0.5
                    periods to the left and 0.25 periods to the right. If nper
                    is a scalar, left and right extensions will be the same.
        reset_zero  If True, will set the leftmost x value to zero
        kwargs      Passed directly to ax.plot() function

    returns xp, xy: the periodically-extended plot values.
    '''

    if np.isscalar(nper):
        nper_left = nper
        nper_right = nper
    else:
        nper_left = nper[0]
        nper_right = nper[1]

    dx = np.average(np.diff(x))
    if np.abs(np.std(np.diff(x))/dx) > 1e-10:
        raise ValueError("x array must be evenly spaced")

    x_per = (len(x) + 1)*dx

    N_left = int(nper_left*x_per/dx)+1
    N_right = int(nper_right*x_per/dx)+1

    xp = np.linspace(
        x[0]-N_left*dx,
        x[-1]+N_right*dx,
        N_left + N_right + len(x)
    )

    if reset_zero:
        xp -= xp[0]

    left_pad = y[-(np.arange(N_left) % len(y))-1]
    left_pad = np.flip(left_pad)
    right_pad = y[np.arange(N_right) % len(y)]

    yp = np.concatenate([left_pad, y, right_pad])

    ax.plot(xp, yp, **kwargs)
    ax.set_xlim([xp[0], xp[-1]])

    return xp, yp


# Run installation code
if not check_installation():
    print("WARNING: qncmbe matplotlib styles not installed yet!")
    print("Attempting to install now...")
    install_mpl_styles()
