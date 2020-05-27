'''Most commonly needed data_import functions, for the end user.'''

from .data_names import index
from .growths import GrowthDataCollector


def get_growth_data(
    start, end, names, savedir=None, molly_dt=None, force_reload=False
):
    '''Main function for getting growth data.

    Note, this is a simple wrapper for the GrowthDataCollector class in
    qncmbe.data_import.growths. The class may provide fuller functionality in
    some cases.

    Inputs:
        start, end
            Start and end times for data collection. These should be either
            datetime objects or strings like "2020-05-23 03:03" or
            "8:00 am February 20, 2020". Strings will be parsed with the
            dateutil.parser library
        names
            List of data names, such as "Al1 tip measured" or "Refl calib 950".
            Use data_import.core.print_names_list() for a full list of allowed
            names. You can use different cases/whitespace, e.g., 
            "Al1_tip_measured" or "Refl Calib 950"
        savedir
            A full path to a folder. If provided, data will be saved here.
            Then, if get_growth_data is run again with the same names and
            start/end time, it will reload the data from savedir. Typically
            this is much quicker than loading from the remote servers.
        molly_dt
            If provided, the data collector will interpolate Molly data so that
            the time spacing is equal. (This uses a very simple step
            interpolation to be consistent with how Molly stores data.)
            molly_dt has units of seconds.
        force_reload
            If savedir is provided, this can be used to ignore any previously
            saved data and force a reload from the lab servers.

    Output:
        data
            A dictionary of DataElement objects, with keys equal to the names
            input. DataElements have members "time" and "vals" which are arrays
            corresponding to the time (in sec) and the data values. These can
            be accessed by, e.g., data["Al1 tip measured"].time,
            data["Al1 tip measured"].vals
    '''

    collector = GrowthDataCollector(start, end, names, savedir, molly_dt)

    data = collector.get_data(force_reload=force_reload)
    
    return data


def get_names_list():
    return index.get_names_list()


def print_names_list():
    string = '\n'.join(get_names_list())
    print(string)
    return string
