import warnings

# qncmbe imports
from .growths import GrowthDataCollector


warnings.warn("data_import_utils.get_data() is no longer maintained.")


def get_data(start_time, end_time, value_names_list, delta_t=-1, interp=False):
    '''DEPRECATED: use the GrowthDataCollector class instead.
    
    Primary function for getting data from various computers in the
    QNC-MBE lab.

    - start_time and end_time should be datetime objects.
    - value_names_list should be a list of strings. They must correspond to
      entries in the first column of data_names_data_names_index.csv
    - delta_t should be the desired time resolution of Molly data in seconds.
    - interp is a bool determining whether to linearly interpolate (True) or
      step interpolate (False) the data

    Returns 'data': a dictionary of numpy arrays, with keys corresponding to
    the value_names_list

    SPECIAL CASE:
    If delta_t == -1, raw Molly data is returned.

    Molly data is stored only when the value changes.
    Molly checks each signal for changes every 2s, and if the value doesn't
    change, it doesn't store anything. (Mostly...) Every time the value does
    change, we get a new pair of values: the time it changed, and the value it
    changed to.

    So, for raw Molly data, each data array has its own time array, which is a
    list of all the times Molly detected a change in that signal.

    In this case "Molly time" is not returned as a separate array.
    Rather, each Molly data signal is now a dictionary with two numpy arrays:
    one for 'time' and one for 'vals'

    So, e.g., suppose you are looking at 'Ga1 tip measured'.
    If delta_t = 2.0, then your time array would be data['Molly time']
    (equally spaced at 2s), and your values array would be
    data['Ga1 tip measured'].
    If delta_t = -1, then your time array would be
    data['Ga1 tip measured']['time'] and your values array would be
    data['Ga1 tip measured']['vals'].
    '''

    warnings.warn(
        "Deprecated. Use the GrowthDataCollector class instead.",
        DeprecationWarning
    )

    pass  # TODO: implement for backwards compatibility

    # local_value_names = {
    #     "Molly": [],
    #     "BET": [],
    #     "SVT": []
    # }
    # for val in value_names_list:
    #     if val not in data_names_index:
    #         raise Exception(
    #             f'Invalid value "{val}" in value_names_list. Not found in '
    #             'data_names_index'
    #         )
    #     local_value_names[data_names_index[val]['Location']].append(
    #         data_names_index[val]['Local value name']
    #     )

    # # Generate dictionary of data for each location

    # Molly_data = get_Molly_data(
    #     start_time, end_time, local_value_names["Molly"], delta_t, interp
    # )
    # BET_data = get_BET_data(start_time, end_time, local_value_names["BET"])
    # SVT_data = get_SVT_data(start_time, end_time, local_value_names["SVT"])

    # # Generate dictionary of all data
    # data = {**Molly_data, **BET_data, **SVT_data}

    # # Convert from local value names to readable value names
    # for val in value_names_list:
    #     data[val] = data.pop(data_names_index[val]['Local value name'])

    # return data

