from setuptools import setup

setup(
    name='qncmbe',
    version='0.1',
    description='Python tools for the QNC-MBE lab at the University of Waterloo',
    url='https://github.com/cdeimert/multipass',
    author='Chris Deimert',
    author_email='cdeimert@uwaterloo.ca',
    license='MIT',
    packages=['qncmbe'],
    install_requires=[
        'cycler',
        'matplotlib',
        'numpy',
        'openpyxl',
        'OriginExt<=1.0.6', # Version 1.0.7 seems to be buggy and not load correctly
        'PyQt5',
        'scipy'
    ],
    include_package_data = True,
    zip_safe = False
)