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
        r"\\insitu1.nexus.uwaterloo.ca", "Documents", "QNC MBE Data",
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
                ti = self.get_interpolated_time()
                self.data[name] = self.data[name].step_interpolate(ti)

        return self.data

    def get_interpolated_time(self):
        if self.dt is None:
            return None
        else:
            tot_seconds = (self.end_time - self.start_time).total_seconds()
            return np.arange(0.0, tot_seconds, self.dt)

    def get_data_path(self, hour):
        '''
        Find the path for the Molly binary file and corresponding header file
        for a given hour.
        '''

        subfolder = hour.strftime("%Y")
        subsubfolder = hour.strftime("%m-%b")
        header_filename = hour.strftime("%dday-%Hhr.txt")
        binary_filename = hour.strftime("%dday-%Hhr-binary.txt")

        header_path = os.path.join(
            self.main_data_path, subfolder, subsubfolder, header_filename
        )
        binary_path = os.path.join(
            self.main_data_path, subfolder, subsubfolder, binary_filename
        )

        return header_path, binary_path

    def get_line_numbers(self, header_path):
        '''Searches the Molly header file for self.names and returns their
        location and size in the binary file as dictionaries.
        '''

        try:
            header = open(header_path, "r")
        except IOError:
            print("Warning: missing header file " + header_path)
            return -1, -1

        try:
            total_values = {}
            values_offset = {}
            local_name = {}
            found = {}
            regex = {}
            for name in self.names:
                total_values[name] = 0
                values_offset[name] = 0
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
                                print(
                                    f"Warning: duplicate entries for '{name}'."
                                )
                            else:
                                found[name] = True

            for name in self.names:
                if not found[name]:
                    print(f"Warning: could not find value '{name}'")

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

        header_path, binary_path = self.get_data_path(hour)

        total_values, values_offset = self.get_line_numbers(header_path)

        datetime0 = hour.replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            binary = open(binary_path, "rb")
        except IOError:
            print("Warning: missing binary file " + binary_path)

            data_hour = {
                name: DataElement(name, datetime0, index[name].units)
                for name in self.names
            }

        try:

            data_hour = {}
            for name in self.names:
                units = index[name].units

                if (total_values[name] < 0) or (values_offset[name] < 0):
                    print(
                        "Warning: Invalid total_values or values_offset for ",
                        name
                    )
                    data_hour[name] = DataElement(name, datetime0, units)
                    break

                data_hour[name] = DataElement(
                    name=name, datetime0=datetime0, units=units,
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
