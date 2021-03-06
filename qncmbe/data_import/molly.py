# Standard library imports (not included in setup.py)
import datetime
import os
import re
import struct

# qncmbe imports
from .utils import DataCollector, DataElement
from .data_names import index

# Non-standard library imports (included in setup.py)
import numpy as np


class MollyDataCollector(DataCollector):

    default_data_path = os.path.join(
        r"\\insitu1", "Documents", "QNC MBE Data",
        "Production Data", "Molly data"
    )

    def __init__(self, start_time, end_time, names, savedir=None, dt=None):
        '''See docstring for parent (DataCollector)

        Additional parameter dt allows you to set the timestep, in case
        you want uniformly-spaced and/or sparse data. Interpolation is done
        step-wise, since this is how Molly data is collected. (Linear
        interpolation will give poor results for signals that don't change
        frequently.)

        If dt = None, raw data is supplied.
        '''

        super().__init__(start_time, end_time, names, savedir)

        self.dt = dt

        if dt is not None:
            if dt <= 0:
                raise ValueError("Invalid dt. Must be None or >0.")

        self.check_names(location='Molly')

        self.main_data_path = self.default_data_path

    def find_bad_data_paths(self):

        if os.path.exists(self.main_data_path):
            return []
        else:
            return [self.main_data_path]

    def collect_data(self):

        self.initialize_data()

        if not os.path.exists(self.main_data_path):
            self.logger.error(
                f'Cannot find/access data path "{self.main_data_path}"'
            )
            return self.data

        # For speed. Skip collection process if no names are requested.
        if not self.names:
            return {}

        delta = datetime.timedelta(hours=1)

        hour = self.start_time.replace(minute=0, second=0, microsecond=0)

        '''
        Start with the previous hour to be safe.

        In principle, this shouldn't be necessary, but there are weird edge
        cases because Molly only stores a value every time the value
        *changes*. E.g., if you're loading the data for hour 02:00:00, and
        the last time the value changed was at 01:59:57, then Molly might not
        include that in the 02:00:00 hour data file. However, if the last
        time the value changed was a long time before, then Molly *does*
        include it in the data file (sometimes as a negative time). I don't
        really get the logic, but it seems that including the extra hour
        makes things safer. I hope.
        '''
        hour -= delta

        first = {name: True for name in self.names}

        while(hour <= self.end_time + delta):

            data_hour = self.get_data_from_binary(hour)

            # Add data from each element
            # Have to skip the first data element on all except the first
            # hour or there will be duplicates

            if first:
                for name in self.names:
                    if first[name]:
                        self.data[name].add_data(data_hour[name])
                        if (len(data_hour[name]) != 0):
                            first[name] = False
                    else:
                        if len(data_hour[name]) != 0:
                            self.data[name].add_data(data_hour[name][1:])

            hour += delta

        # Cleanup data based on start time and end time
        for name in self.names:
            self.data[name].set_datetime0(self.start_time)

            if self.dt is None:
                self.data[name].trim(
                    self.start_time, self.end_time, include_endpoints=True
                )
            else:
                t = self.generate_regular_time(self.dt)
                self.data[name] = self.data[name].step_interpolate(t)

        return self.data

    def get_header_path(self, hour):
        '''Find the path for a Molly header file for a given hour (datetime
        object).'''

        subfolder = hour.strftime("%Y")
        subsubfolder = hour.strftime("%m-%b")
        filename = hour.strftime("%dday-%Hhr.txt")

        return os.path.join(
            self.main_data_path, subfolder, subsubfolder, filename
        )

    def get_binary_path(self, hour):
        '''Find the path for a Molly binary file for a given hour (datetime
        object).'''

        subfolder = hour.strftime("%Y")
        subsubfolder = hour.strftime("%m-%b")
        filename = hour.strftime("%dday-%Hhr-binary.txt")

        return os.path.join(
            self.main_data_path, subfolder, subsubfolder, filename
        )

    def get_line_numbers(self, hour):
        '''Searches the Molly header file from a given hour for self.names and
        returns their location and size in the binary file as dictionaries.

        Returns None, None if opening the header file leads to an IOError
        (usually means the file is missing or inaccessible.)
        '''

        header_path = self.get_header_path(hour)

        total_values = {name: 0 for name in self.names}
        values_offset = {name: 0 for name in self.names}

        try:
            header = open(header_path, "r")
        except IOError:
            self.logger.warning(
                "Missing Molly header file for "
                f"{hour.strftime('%Y-%m-%d')} {hour.strftime('%H')}:00"
            )
            return None, None

        try:
            local_name = {}
            found = {}
            regex = {}
            for name in self.names:
                local_name[name] = self.parameters[name]['local_name']
                found[name] = False
                regex[name] = re.compile(
                    r"^DataItem=Name:"
                    + local_name[name] + ".*?" +
                    r"TotalValues:([0-9].*?);ValueOffset:([0-9].*?)\s*?\n"
                )

            for line in header:
                for name in self.names:
                    if local_name[name] in line:  # (Redundant, but faster)
                        match = regex[name].search(line)
                        if (match):
                            total_values[name] = int(match.group(1))
                            values_offset[name] = int(match.group(2))
                            if found[name]:
                                self.logger.error(
                                    f"Duplicate entries for '{name}'"
                                    f"{hour.strftime('%Y-%m-%d')} "
                                    f"{hour.strftime('%H')}:00"
                                )
                            else:
                                found[name] = True

            for name in self.names:
                if not found[name]:
                    self.logger.debug(
                        f"Missing '{name}' for "
                        f"{hour.strftime('%Y-%m-%d')} {hour.strftime('%H')}:00"
                    )

        finally:
            header.close()

        return total_values, values_offset

    def get_data_from_binary(self, hour):
        '''
        Gets data from Molly binary files for a single hour.
        'hour' should be a datetime object.

        Returns a dictionary of DataElement objects (keys are self.names)

        Explanation:
        Molly data is stored in one hour chunks, sorted by date.
        E.g. /2019/08-Aug/16day-21hr-binary.txt
        There is a corresponding header file in plaintext
        E.g. /2019/08-Aug/16day-21hr.txt
        This tells you how to read the binary file.

        Values are only stored when they change. (And it checks for changes
        every ~2s) So, e.g., when Molly detects an Al base temperature changes,
        it adds a pair of values: the time it changed (relative to midnight
        that day) and the value it changed to.

        So every hour, each data signal ends up with its own list of times and
        values. The header file essentially tells you what order the values are
        in, and how many values there were that hour. Then you can go through
        the binary file sequentially to get the values.
        '''

        binary_path = self.get_binary_path(hour)

        total_values, values_offset = self.get_line_numbers(hour)

        datetime0 = hour.replace(hour=0, minute=0, second=0, microsecond=0)

        data_hour = {
            name: DataElement(name, datetime0, index[name].units)
            for name in self.names
        }

        if (total_values is None) and (values_offset is None):
            return data_hour

        try:
            binary = open(binary_path, "rb")
        except IOError:
            self.logger.warning(
                "Missing Molly binary file for "
                f"{hour.strftime('%Y-%m-%d')} {hour.strftime('%H')}:00"
            )
            return data_hour

        try:
            for name in self.names:
                if (total_values[name] < 0) or (values_offset[name] < 0):
                    self.logger.error(
                        f'Invalid total_values or values_offset for "{name}"'
                    )
                    break

                data_hour[name].set_data(
                    time=np.zeros(total_values[name]),
                    vals=np.zeros(total_values[name])
                )

                binary.seek((values_offset[name]+1)*8)

                for n in range(total_values[name]):
                    data_hour[name].time[n] = struct.unpack(
                        'f', binary.read(4))[0]*86400
                    data_hour[name].vals[n] = struct.unpack(
                        'f', binary.read(4)
                    )[0]

        finally:
            binary.close()

        return data_hour
