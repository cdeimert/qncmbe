'''
Useful functions for plotting with matplotlib
'''

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as clrs
import numpy as np
import scipy.interpolate as interpolate


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


def generate_colormap(color_low=None, color_high=None, num_colors=256):

    vals = np.ones((num_colors, 4))

    mpl_colors = get_mpl_colors()
    if color_low is None:
        C0 = clrs.to_rgb(mpl_colors[0])
    else:
        C0 = clrs.to_rgb(color_low)

    if color_high is None:
        C1 = clrs.to_rgb(mpl_colors[1])
    else:
        C1 = clrs.to_rgb(color_high)

    for i in range(3):
        vals[:, i] = np.linspace(C0[i], C1[i], num_colors)

    return mpl.colors.ListedColormap(vals)


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


def interpolate_2D_grid(x, y, z, Nx, Ny=None, **kwargs):
    '''Simple function to interpolate 2D data assuming x and y form a
    rectangular grid. Interpolates to an Nx by Ny grid.
    If Ny is not given, it defaults as equal to Nx.

    Remaining kwargs are passed to scipy.interpolate.griddata. Also 'rescale'
    default value is changed to True.

    Returns interpolated arrays xi, yi, zi. These are flat 1D arrays of length
    Nx*Ny'''

    if Ny is None:
        Ny = Nx

    X = np.linspace(np.min(x), np.max(x), Nx)
    Y = np.linspace(np.min(y), np.max(y), Ny)

    XX, YY = np.meshgrid(X, Y)

    xi = XX.flatten()
    yi = YY.flatten()

    if 'rescale' not in kwargs:
        kwargs['rescale'] = True

    zi = interpolate.griddata(
        (x, y), z, (xi, yi), **kwargs
    )

    return xi, yi, zi


def plot_2D_color(ax, x, y, c, **kwargs):
    '''Wrapper for matplotlib's tripcolor function.
    Difference is that this  one scales the variables before breaking the grid
    into triangles, to give better results when x and y have different units.

    ax should be a matplotlib Axes object
    Remaining arguments are the same as tripcolor

    '''

    if 'triangles' not in kwargs:
        x_rel = x/np.ptp(x)
        y_rel = y/np.ptp(y)

        kwargs['triangles'] = mpl.tri.Triangulation(x_rel, y_rel).triangles

    return ax.tripcolor(x, y, c, **kwargs)
