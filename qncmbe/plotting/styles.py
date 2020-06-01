'''Functions for installing and using the qncmbe style files.
(Located in qncmbe/qncmbe/plotting/stylelib/*.mplstyle)

Will install the *.mplstyle files to the local matplotlib style folder.
Typically this folder is something like C:/Users/myname/.matplotlib/stylelib,
but it can be found by calling matplotlib.get_configdir()
'''

import os
import logging

import matplotlib as mpl
import matplotlib.pyplot as plt


logger = logging.getLogger(__name__)


def use(name):
    '''Wrapper for matplotlib.pyplot.style.use(). Applies the given matplotlib
    style.

    Includes an additional check for qncmbe style files to make sure they are
    installed first.
    '''

    if name in get_qncmbe_styles():
        install(name)

    plt.style.use(name)


def get_qncmbe_stylelib_dir():
    this_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_dir, 'stylelib')


def get_qncmbe_styles():

    stylelib_dir = get_qncmbe_stylelib_dir()

    styles = []

    for fname in os.listdir(stylelib_dir):
        styles.append(os.path.splitext(fname)[0])

    return styles


def install(name):
    '''Check installation of the given style. Installs it if safe.'''

    if name not in get_qncmbe_styles():
        logger.error(f'"{name}" is not a qncmbe matplotlib style.')
        return False

    local_file = os.path.join(
        mpl.get_configdir(), 'stylelib', f'{name}.mplstyle'
    )

    if not os.path.exists(local_file):
        logger.info(
            f'Installing style "{name}".'
        )
        write_style_file(name)
        return True

    with open(local_file, 'r') as lf:
        # Confirm that the header is correct
        for header_line in get_header().split('\n'):
            if lf.readline().rstrip() != header_line.rstrip():
                logger.warning(
                    'Unexpected header in matplotlib style file:'
                    f'\n  "{local_file}"'
                )
                return False
        local_contents = lf.read()

    package_file = os.path.join(
        get_qncmbe_stylelib_dir(), f'{name}.mplstyle'
    )

    with open(package_file, 'r') as pf:
        package_contents = pf.read()

    if local_contents != package_contents:
        logger.warning(
            f'Style "{name}" is installed but appears to be modified or'
            f' out of date. Updating now.'
        )
        write_style_file(name)

    return True


def write_style_file(name):

    local_stylelib_dir = os.path.join(mpl.get_configdir(), 'stylelib')

    os.makedirs(local_stylelib_dir, exist_ok=True)

    local_file = os.path.join(
        local_stylelib_dir, f'{name}.mplstyle'
    )

    package_file = os.path.join(
        get_qncmbe_stylelib_dir(), f'{name}.mplstyle'
    )

    with open(local_file, 'w') as lf:
        lf.write(get_header() + '\n')

        with open(package_file, 'r') as pf:
            lf.write(pf.read())

    logger.info(f'Wrote to style file:\n  "{local_file}"')
    plt.style.reload_library()


def get_header():
    header = '# This mplstyle is from the qncmbe python package'
    header += '\n# WARNING: modifications to this file may be overwritten by'
    header += ' the qncmbe package!'

    return header


def install_all():

    success = True
    for name in get_qncmbe_styles():
        if not install(name):
            success = False

    if success:
        logger.info("qncmbe plot styles are up to date.")
    else:
        logger.warning("qncmbe plot styles installation was unsuccessful.")
