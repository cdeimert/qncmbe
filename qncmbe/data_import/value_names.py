'''Included for backwards compatibility'''

import warnings
from .data_names import index

warnings.warn("value_names is deprecated. Use data_names module instead.")

value_names_database = index
