
# Standard library imports (not included in setup.py)
import datetime as dt
import os
import re
import struct

# qncmbe imports
from .value_names import value_names_database

# Non-standard library imports (included in setup.py)
import numpy as np


def get_data(start_time, end_time, value_names_list, delta_t=-1, interp=False):
    '''Primary function for getting data from various computers in the
    QNC-MBE lab.

    - start_time and end_time should be datetime objects.
    - value_names_list should be a list of strings. They must correspond to
      entries in the first column of value_names_database.csv
    - delta_t should be the desired time resolution of Molly data in seconds.
    - intrp is a bool determining whether to linearly interpolate (True) or
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

    local_value_names = {
        "Molly": [],
        "BET": [],
        "SVT": []
    }
    for val in value_names_list:
        if val not in value_names_database:
            raise Exception(
                f'Invalid value "{val}" in value_names_list. Not found in '
                'value_names_database'
            )
        local_value_names[value_names_database[val]['Location']].append(
            value_names_database[val]['Local value name']
        )

    # Generate dictionary of data for each location

    Molly_data = get_Molly_data(
        start_time, end_time, local_value_names["Molly"], delta_t, interp
    )
    BET_data = get_BET_data(start_time, end_time, local_value_names["BET"])
    SVT_data = get_SVT_data(start_time, end_time, local_value_names["SVT"])

    # Generate dictionary of all data
    data = {**Molly_data, **BET_data, **SVT_data}

    # Convert from local value names to readable value names
    for val in value_names_list:
        data[val] = data.pop(value_names_database[val]['Local value name'])

    return data


def get_value_names_list(location="all"):
    '''Gets a list of all value names from the value names database if
    location == "all"

    Otherwise, only returns value names from a particular location (either
    "Molly", "SVT", or "BET")
    '''

    value_names_list = []
    for val in value_names_database:
        if (
            (location == "all") or
            (location == value_names_database[val]["Location"])
        ):
            value_names_list.append(val)

    return value_names_list


def get_raw_Molly_data(start_time, end_time, value_names):
    '''Gets raw Molly data (uneven timesteps, unique time array for each value)
    Since the files are stored in one-hour chunks, it loops through hour
    by hour.

    This function returns all the one-hour chunks necessary to cover start_time
    to end_time.
    It also includes an extra hour buffer on each end for safety.

    Return value is a dictionary with keys equal to value names.
    Each dictionary element is another dictionary with two keys: 'time'
    (containing a numpy time array) and 'vals' (containing a numpy value array)
    '''

    delta = dt.timedelta(hours=1)

    hour = start_time.replace(minute=0, second=0, microsecond=0)

    # Start with the previous hour to be safe.
    #
    # In principle, this shouldn't be necessary, but there are weird edge cases
    # because Molly only stores a value every time the value *changes*.
    # E.g., if you're loading the data for hour 02:00:00, and the last time the
    # value changed was at 01:59:57, then Molly might not include that in the
    # 02:00:00 hour data file. However, if the last time the value changed was
    # a long time before, then Molly *does* include it in the data file
    # (sometimes as a negative time). I don't really get the logic, but it
    # seems that including the extra hour makes things safer. I hope.
    hour -= delta

    # Since Molly time is relative to midnight, need to manually keep track of
    # the days
    start_day = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day = hour.replace(hour=0, minute=0, second=0, microsecond=0)

    data = {}

    while(hour <= end_time + delta):

        data_hour = get_raw_Molly_data_hour(hour, value_names)

        num_days = (day - start_day).days

        for name in value_names:

            # if data_hour[name]['time'][0]

            data_hour[name]['time'] += num_days*86400

            if (name not in data):
                data[name] = {'time': [], 'vals': []}

            data[name]['time'].append(data_hour[name]['time'])
            data[name]['vals'].append(data_hour[name]['vals'])

        hour += delta

        day = hour.replace(hour=0, minute=0, second=0, microsecond=0)

    # Concatenate so that all the data is in one list
    for name in value_names:
        data[name]['time'] = np.concatenate(data[name]['time'])
        data[name]['vals'] = np.concatenate(data[name]['vals'])

    return data


def get_Molly_data(start_time, end_time, value_names, delta_t, interp=False):

    if not value_names:
        return {}  # Redundant, but increases speed.

    # Create list of values with "Time" excluded.
    raw_value_names = list(value_names)
    while "Time" in raw_value_names:
        raw_value_names.remove("Time")

    # Get raw values (not interpolated)
    raw_data = get_raw_Molly_data(start_time, end_time, raw_value_names)

    # Shift raw data time so that zero corresponds to start time.
    # (Time vectors from get_raw_Molly_data() are in "Molly time", zero is
    # midnight on the first day.)
    molly_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

    for name in raw_value_names:
        raw_data[name]['time'] = raw_data[name]['time'] - \
            (start_time - molly_time).total_seconds()

    # Find total number of seconds between start and end time
    tot_seconds = (end_time - start_time).total_seconds()

    if delta_t == -1:
        # If delta_t is -1, then return the raw data without interpolating
        # In this case, there will be a separate time array associated with
        # each value

        data = {}
        for name in raw_value_names:

            inds = (raw_data[name]['time'] >= 0) & (
                raw_data[name]['time'] <= tot_seconds)
            data[name] = {
                'time': raw_data[name]['time'][inds],
                'vals': raw_data[name]['vals'][inds]
            }

        return data

    # Create interpolated time vector so that all values share the same time.
    # arange excludes the endpoint by default. The 1e-3*delta_t buffer is a
    # "safety" for that
    time_interp = np.arange(0.0, tot_seconds + 1e-3*delta_t, delta_t)

    data = {}
    for name in raw_value_names:

        if raw_data[name]['vals'].size == 0:
            # If the value was not found, return a list of NaNs.
            data[name] = np.empty_like(time_interp)
            data[name][:] = np.nan

        else:
            # interp decides whether the data should be linearly interpolated
            # or step interpolated
            if interp:
                data[name] = np.interp(
                    time_interp, raw_data[name]['time'], raw_data[name]['vals']
                )
            else:
                # Have to sort the raw data so that the times are
                # monotonically-increasing... They should be monotonically-
                # increasing anyway, but it seems like rounding error sometimes
                # screws this up.
                sort_inds = np.argsort(raw_data[name]['time'])
                raw_data[name]['time'] = raw_data[name]['time'][sort_inds]
                raw_data[name]['vals'] = raw_data[name]['vals'][sort_inds]

                # Now, for each time in the interpolated data, find the last
                # time in the raw data that the value was changed, and use the
                # corresponding value.
                inds = np.digitize(time_interp, raw_data[name]['time']) - 1
                data[name] = raw_data[name]['vals'][inds]

    if "Time" in value_names:
        data["Time"] = time_interp

    return data


def get_raw_Molly_data_hour(import_time, value_names):
    '''
    Converts the binary Molly data files into numpy arrays.

    Molly data is stored in one hour chunks, sorted by date.
    E.g. /2019/08-Aug/16day-21hr-binary.txt
    There is a corresponding header file in plaintext
    E.g. /2019/08-Aug/16day-21hr.txt
    This tells you how to read the binary file.

    Values are only stored when they change. (And it checks for changes every
    ~2s) So, e.g., when Molly detects an Al base temperature changes, it adds a
    pair of values: the time it changed (relative to midnight that day) and the
    value it changed to.

    So every hour, each data signal ends up with its own list of times and
    values. The header file essentially tells you what order the values are in,
    and how many values there were that hour. Then you can go through the
    binary file sequentially to get the values.

    This function does that for a single hour chunk, outputting a dictionary.
    The dictionary contains one entry for each value requested. Each entry of
    the output dictionary is itself a dictionary with two keys: "val" and
    "time", corresponding to the time and value sequence in the Molly data.
    '''

    header_path, binary_path = get_filepaths(import_time)

    total_values, values_offset = get_line_numbers(header_path, value_names)

    data_hour = get_data_from_binary(
        binary_path, total_values, values_offset, value_names
    )

    return data_hour


def get_filepaths(import_time):
    '''
    Find the path for the Molly binary file for a given hour.

    Mostly used in get_raw_Molly_data_hour()
    '''
    path = "\\\\insitu1.nexus.uwaterloo.ca\\Documents\\QNC MBE Data"
    path += "\\Production Data\\Molly data"

    subfolder = import_time.strftime("%Y")
    subsubfolder = import_time.strftime("%m-%b")
    header_filename = import_time.strftime("%dday-%Hhr.txt")
    binary_filename = import_time.strftime("%dday-%Hhr-binary.txt")

    header_path = os.path.join(path, subfolder, subsubfolder, header_filename)
    binary_path = os.path.join(path, subfolder, subsubfolder, binary_filename)

    return header_path, binary_path


def get_line_numbers(header_path, value_names):
    '''Searches the header file for the given value_names and returns their
    location and size in the binary file.

    The output is used in get_data_from_binary(), and mostly used in
    get_raw_Molly_data_hour()
    '''

    try:
        header = open(header_path, "r")
    except IOError:
        print("Warning: missing header file " + header_path)
        return -1, -1

    try:
        total_values = {}
        values_offset = {}
        found = {}
        regex = {}
        for name in value_names:
            total_values[name] = 0
            values_offset[name] = 0
            found[name] = False
            regex[name] = re.compile(
                r"^DataItem=Name:"
                + name + ".*?" +
                "TotalValues:([0-9].*?);ValueOffset:([0-9].*?)\s*?\n"
            )

        for line in header:
            for name in value_names:
                if name in line:  # (Redundant, but increases speed)
                    match = regex[name].search(line)
                    if (match):
                        total_values[name] = int(match.group(1))
                        values_offset[name] = int(match.group(2))
                        if found[name]:
                            print(f"Warning: duplicate entries for '{name}'.")
                        else:
                            found[name] = True

        for name in value_names:
            if not found[name]:
                print(f"Warning: could not find value '{name}'")

    finally:
        header.close()

    return total_values, values_offset


def get_data_from_binary(
    binary_path, total_values, values_offset, value_names
):
    '''Reads the binary data for value_names from the given binary
    file (binary_path). total_values, values_offset are essentially the size
    and location of the data in the binary file. Returned by get_line_numbers()

    This is used in get_raw_Molly_data_hour()
    '''

    try:
        binary = open(binary_path, "rb")
    except IOError:
        print("Warning: missing binary file " + binary_path)
        data = {}
        for name in value_names:
            data[name] = {"time": np.zeros(0), "vals": np.zeros(0)}
        return data

    try:

        data = {}
        for name in value_names:
            if (total_values[name] < 0) or (values_offset[name] < 0):
                print(
                    "Warning: Invalid total_values or values_offset for ", name
                )
                data[name] = {"time": np.zeros(0), "vals": np.zeros(0)}
                break

            data[name] = {"time": np.zeros(
                total_values[name]), "vals": np.zeros(total_values[name])}

            binary.seek((values_offset[name]+1)*8)
            for n in range(total_values[name]):
                data[name]["time"][n] = struct.unpack(
                    'f', binary.read(4))[0]*86400
                data[name]["vals"][n] = struct.unpack('f', binary.read(4))[0]

    finally:
        binary.close()

    return data


def import_to_csv(value_names, data, file_name, delimiter=','):

    out_file = open(file_name, 'wb')

    try:
        header_str = ""
        for name in value_names:
            header_str += name + delimiter
        # Replace last delimiter with newline
        header_str = header_str[:-len(delimiter)] + '\n'

        out_file.write(bytes(header_str, 'utf8'))

        out_data = np.zeros((len(data[next(iter(data))]), len(value_names)))
        for ind, name in enumerate(value_names):
            out_data[:, ind] = data[name]

        np.savetxt(out_file, out_data, delimiter=delimiter, fmt='%.8g')

    finally:
        out_file.close()


def get_BET_data(start_time, end_time, value_names):
    '''Only allowed value names are:
    'ISP Time', 'ISP Integral', 'ISP Temp', 'BET Time', 'BET Temp'

    Values starting with 'ISP' are stored in a different file than values
    starting with 'BET', so have to separate them.
    '''
    if not value_names:
        return {}  # Redundant, but increases speed.

    base_dir = "\\\\insitu1.nexus.uwaterloo.ca\\Documents\\QNC MBE Data"
    base_dir += "\\Production Data"

    # Information about which file (sublocation) and column each value is in.
    info = {
        'ISP Time': {'subloc': 'ISP', 'col': 0},
        'ISP Integral': {'subloc': 'ISP', 'col': 1},
        'ISP Temp': {'subloc': 'ISP', 'col': 2},
        'BET Time': {'subloc': 'BET', 'col': 0},
        'BET Temp': {'subloc': 'BET', 'col': 1}
    }

    sublocs = []
    for name in value_names:
        subloc = info[name]['subloc']
        if info[name]['subloc'] not in sublocs:
            sublocs.append(subloc)

    path = {}
    files = {}
    for subloc in sublocs:
        path[subloc] = os.path.join(base_dir, subloc + " data")
        files[subloc] = []

        dir_files = os.listdir(path[subloc])

        for dir_file in dir_files:
            full_filepath = os.path.join(path[subloc], dir_file)
            ctime = dt.datetime.fromtimestamp(os.path.getctime(full_filepath))
            mtime = dt.datetime.fromtimestamp(os.path.getmtime(full_filepath))

            time_condition = (start_time < mtime) and (end_time > ctime)

            name_condition = (dir_file.startswith(subloc)) and (
                dir_file.endswith('.dat')
            )
            if time_condition and name_condition:
                offset = (ctime - start_time).total_seconds()
                files[subloc].append({'name': full_filepath, 'offset': offset})

    # Get data from each file, and apply time offsets
    raw_data = {}
    for subloc in sublocs:
        raw_data[subloc] = []
        for file in files[subloc]:
            try:
                file_data = np.loadtxt(file['name'], skiprows=1)
            except:  # noqa E722
                print("Error loading file " + file['name'])

            # Apply time offset
            file_data[:, 0] += file['offset']

            raw_data[subloc].append(file_data)

        if (len(raw_data[subloc]) != 0):
            raw_data[subloc] = np.concatenate(raw_data[subloc], axis=0)
            sorted_inds = np.argsort(raw_data[subloc][:, 0])
            raw_data[subloc] = raw_data[subloc][sorted_inds, :]

            total_time = (end_time - start_time).total_seconds()
            trimmed_inds = np.logical_and(
                0.0 < raw_data[subloc][:, 0],
                raw_data[subloc][:, 0] < total_time
            )
            raw_data[subloc] = raw_data[subloc][trimmed_inds, :]
        else:
            raw_data[subloc] = np.zeros((0, 4))

    data = {}
    for name in value_names:
        subloc = info[name]['subloc']
        col = info[name]['col']

        data[name] = raw_data[subloc][:, col]

    return data


def get_SVT_data(start_time, end_time, value_names):
    '''
    Only allowed value names are:
        SVT Time (RoboMBE Engine)
        PI 950
        PI 850
        Refl 950
        Refl 470
        SVT Time (RoboMBE IS4K Temp)
        Emiss Temp
        Ratio Temp
        SVT Time (RoboMBE IS4K Refl)
        Calib 950
        Calib 470
    '''
    if not value_names:
        return {}  # Redundant, but increases speed.

    path = "\\\\zw-xp1\\QNC_MBE_Data"

    data = {val: [] for val in value_names}

    for name in os.listdir(path):
        full_name = os.path.join(path, name)
        if is_SVT_folder(full_name):

            # Check if folder has data within the requested time span,
            # otherwise skip it

            t0, ts, te = get_SVT_folder_time_info(full_name)

            folder_zero_time = t0
            folder_start_time = ts
            folder_end_time = te

            if (
                (end_time >= folder_start_time)
                and (start_time <= folder_end_time)
            ):

                t_min = (start_time - folder_zero_time).total_seconds()
                t_max = (end_time - folder_zero_time).total_seconds()

                folder_data = get_SVT_data_from_folder(
                    full_name, [t_min, t_max])

                for val in value_names:
                    data[val].append(folder_data[val])

    # Merge everything into a single numpy array.
    for val in data:
        data[val] = np.concatenate(data[val])

    return data


def is_SVT_folder(folder):
    '''
    Checks if the given folder is a valid SVT data folder
    '''

    if os.path.exists(os.path.join(folder, 'time_info.txt')):
        return True

    engine = False
    temp = False
    refl = False

    try:
        for name in os.listdir(folder):
            if name.endswith('Engine 1.txt'):
                engine = True
            if name.endswith('IS4K Temp.txt'):
                temp = True
            if name.endswith('IS4K Refl.txt'):
                refl = True
    except:  # noqa E722
        pass

    return all([engine, temp, refl])


def get_SVT_folder_time_info(folder):

    time_file = os.path.join(folder, 'time_info.txt')

    fmt_string = "%Y-%m-%d %H:%M:%S.%f"

    line0 = "(Generated by Python qncmbe data_import module. Do not modify.)\n"
    line1 = f'Parent folder = "{folder}"\n'

    try:
        with open(time_file) as tf:
            if tf.readline() != line0:
                raise ValueError
            if not tf.readline().startswith('Parent folder = '):
                raise ValueError

            arr = []
            for n in range(3):
                date_string = tf.readline().split(' = ')[-1].strip('\n')
                arr.append(dt.datetime.strptime(date_string, fmt_string))

            t_zero, t_start, t_end = arr
    except:  # noqa E722
        data = get_SVT_data_from_folder(folder)

        t = data['SVT Time (RoboMBE Engine)']

        engine_file = ''
        for name in os.listdir(folder):
            if name.endswith('Engine 1.txt'):
                engine_file = os.path.join(folder, name)

        # Times are just relative to midnight on some day.
        # So compare with the file creation date to figure out which day.

        creation_time = dt.datetime.fromtimestamp(
            os.path.getctime(engine_file))

        t_zero = creation_time.replace(
            hour=0, minute=0, second=0, microsecond=0)

        diff = (
            t_zero + dt.timedelta(seconds=t[0]) - creation_time
        ).total_seconds()

        while abs(diff) > 86400/2:
            t_zero -= np.sign(diff)*dt.timedelta(seconds=86400)

            diff = (
                t_zero + dt.timedelta(seconds=t[0]) - creation_time
            ).total_seconds()

        t_start = t_zero + dt.timedelta(seconds=t[0])
        t_end = t_zero + dt.timedelta(seconds=t[-1])

        with open(time_file, 'w') as tf:
            tf.write(line0)
            tf.write(line1)
            tf.write(f'Zero_time = {t_zero.strftime(fmt_string)}\n')
            tf.write(f'Data_start_time = {t_start.strftime(fmt_string)}\n')
            tf.write(f'Data_end_time = {t_end.strftime(fmt_string)}')

    return t_zero, t_start, t_end


def get_SVT_data_from_folder(folder, time_limits=None):

    col_info = {
        'Engine 1.txt': {
            'SVT Time (RoboMBE Engine)': 0,
            'PI 950': 1,
            'PI 850': 2,
            'Refl 950': 3,
            'Refl 470': 4
        },
        'IS4K Temp.txt': {
            'SVT Time (RoboMBE IS4K Temp)': 0,
            'Emiss Temp': 3,
            'Ratio Temp': 2
        },
        'IS4K Refl.txt': {
            'SVT Time (RoboMBE IS4K Refl)': 0,
            'Calib 950': 1,
            'Calib 470': 2
        }
    }

    data = {}
    for name in os.listdir(folder):
        full_name = os.path.join(folder, name)

        for basename in col_info:
            if name.endswith(basename):

                keys = []
                cols = []

                for k, c in col_info[basename].items():
                    keys.append(k)
                    cols.append(c)

                fdata = read_SVT_data_file(full_name, cols, True)

                for n, k in enumerate(keys):
                    data[k] = fdata[:, n]

    for key in data:
        if 'Time' in key:
            data[key] *= 3600*24

    if time_limits is not None:
        t_min = time_limits[0]
        t_max = time_limits[1]
        for basename in col_info:
            for key in col_info[basename]:
                if 'Time' in key:
                    time_key = key

                t = data[time_key]

            mask = (t >= t_min) & (t <= t_max)
            for key in col_info[basename]:
                data[key] = data[key][mask]

            data[time_key] -= t[0]

    return data


def read_SVT_data_file(filepath, cols, try_increments=True):
    '''
    Reads a single SVT data file. E.g., "G0123_IS4K Refl.txt".

    If try_increments is True, then will automatically search for incremented
    files like "G0123_IS4K Refm.txt" and get the data from them too.
    This is useful since the SVT software's default behaviour is to switch to a
    new file if the first one gets too long.
    '''

    data = []
    name = filepath
    keep_going = True
    while keep_going:
        with open(name) as f:
            for line in f:
                try:
                    data.append([float(line.split()[i]) for i in cols])
                except (ValueError, IndexError):
                    continue

        name = increment_SVT_filename(name)

        if try_increments:
            keep_going = os.path.exists(name)
        else:
            keep_going = False

    return np.array(data)


def increment_SVT_filename(filepath):

    basename = filepath.strip('.txt')
    lastchar = basename[-1]

    return basename[:-1] + chr(ord(lastchar) + 1) + '.txt'
