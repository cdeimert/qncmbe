# Standard library imports (not included in setup.py)
import datetime
import os

# qncmbe imports
from .core import DataCollector, DataElement

# Non-standard library imports (included in setup.py)
import numpy as np


class SVTDataCollector(DataCollector):
    def __init__(self, start_time, end_time, names, savedir=None):
        '''See docstring for parent (DataCollector)'''

        super().__init__(start_time, end_time, names, savedir)

        self.check_names(location='SVT')

        self.main_data_path = "\\\\zw-xp1\\QNC_MBE_Data"

    def collect_data(self):

        # For speed. Skip collection process if no names are requested.
        if not self.names:
            self.data = {}
            return self.data

        self.data = {
            name: DataElement(name, self.start_time) for name in self.names
        }

        for fname in os.listdir(self.main_data_path):
            fpath = os.path.join(self.main_data_path, fname)
            if SVTDataCollector.is_SVT_folder(fpath):

                # Check if folder has data within the requested time span,
                # otherwise skip it

                t0, ts, te = self.get_SVT_folder_time_info(fpath)

                f_zero_time = t0
                f_start_time = ts
                f_end_time = te

                time_condition = (
                    (self.end_time >= f_start_time)
                    and (self.start_time <= f_end_time)
                )

                if time_condition:

                    for name in self.names:
                        postfix = self.parameters[name]['filename']
                        col = self.parameters[name]['column']
                        tcol = self.parameters[name]['time_column']

                        basename = None
                        for bn in os.listdir(fpath):
                            if bn.endswith(postfix):
                                basename = bn
                                break

                        f_arr = SVTDataCollector.read_SVT_data_file(
                            filepath=os.path.join(fpath, basename),
                            cols=[tcol, col],
                            try_increments=True
                        )

                        self.data[name].append(
                            DataElement(
                                name=name,
                                datetime0=f_zero_time,
                                time=f_arr[:, 0]*3600*24,
                                vals=f_arr[:, 1]
                            )
                        )

        for name in self.names:
            self.data[name].trim(self.start_time, self.end_time)

        return self.data

    @staticmethod
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
        except NotADirectoryError:
            pass

        return all([engine, temp, refl])

    @staticmethod
    def get_SVT_folder_time_info(folder):
        '''
        Looks at an SVT data ouput folder to figure out the timestamp of the
        data.

        Returns 3 datetime objects.
        - t_zero: date + time corresponding to t=0 in the data file
        - t_start: date + time of the first data point
        - t_end: date + time of the last data point
        '''

        time_file = os.path.join(folder, 'time_info.txt')

        fmt_string = "%Y-%m-%d %H:%M:%S.%f"

        line0 = (
            "(Generated by Python qncmbe data_import module. Do not modify.)\n"
        )
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
                    arr.append(
                        datetime.datetime.strptime(date_string, fmt_string)
                    )

                t_zero, t_start, t_end = arr

        except (FileNotFoundError, ValueError):
            # If the time_info.txt file has not been generated, generate it.

            engine_file = ''
            for name in os.listdir(folder):
                if name.endswith('Engine 1.txt'):
                    engine_file = os.path.join(folder, name)

            t = SVTDataCollector.read_SVT_data_file(
                            filepath=engine_file,
                            cols=[0],
                            try_increments=True
                        )

            # Times are just relative to midnight on some day.
            # So compare with the file creation date to figure out which day.

            creation_time = datetime.datetime.fromtimestamp(
                os.path.getctime(engine_file)
            )

            t_zero = creation_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            diff = (
                t_zero + datetime.timedelta(seconds=t[0]) - creation_time
            ).total_seconds()

            while abs(diff) > 86400/2:
                t_zero -= np.sign(diff)*datetime.timedelta(seconds=86400)

                diff = (
                    t_zero + datetime.timedelta(seconds=t[0]) - creation_time
                ).total_seconds()

            t_start = t_zero + datetime.timedelta(seconds=t[0])
            t_end = t_zero + datetime.timedelta(seconds=t[-1])

            with open(time_file, 'w') as tf:
                tf.write(line0)
                tf.write(line1)
                tf.write(f'Zero_time = {t_zero.strftime(fmt_string)}\n')
                tf.write(f'Data_start_time = {t_start.strftime(fmt_string)}\n')
                tf.write(f'Data_end_time = {t_end.strftime(fmt_string)}')

        return t_zero, t_start, t_end

    @staticmethod
    def read_SVT_data_file(filepath, cols, try_increments=True):
        '''
        Reads a single SVT data file. E.g., "G0123_IS4K Refl.txt".

        If try_increments is True, then will automatically search for
        incremented files like "G0123_IS4K Refm.txt" and get the data from them
        too. This is useful since the SVT software's default behaviour is to
        switch to a new file if the first one gets too long.

        Returns data as-is from the file. E.g., time is given in day fraction
        rather than seconds
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

            name = SVTDataCollector.increment_SVT_filename(name)

            if try_increments:
                keep_going = os.path.exists(name)
            else:
                keep_going = False

        return np.array(data)

    @staticmethod
    def increment_SVT_filename(filepath):

        basename = filepath.strip('.txt')
        lastchar = basename[-1]

        return basename[:-1] + chr(ord(lastchar) + 1) + '.txt'
