from collections import OrderedDict

def space_to_underscore(str_in):
    return str_in.replace(" ", "_")

def to_camel_case(str_in):
    return str_in.title().replace(" ", "")

def last_word(str_in):
    return str_in.split()[-1]

value_names_database = OrderedDict()

value_names_database["Molly time"] = {
    "Location": "Molly",
    "Local value name": "Time",
    "Measurement type": "Time",
    "Units": "s"
}

control_points = [  'Ga1 tip', 'Ga1 base',
                    'Ga2 tip', 'Ga2 base',
                    'Al1 tip', 'Al1 base',
                    'In1 tip', 'In1 base',
                    'In2 tip', 'In2 base',
                    'Si1 base',
                    'C1',
                    'GaTe1 tip', 'GaTe1 base',
                    'As1 valve', 'As1 crack', 'As1 bulk',
                    'Sb1 valve', 'Sb1 crack', 'Sb1 bulk', 'Sb1 cond',
                    'GM1 subs center', 'GM1 subs rot',
                    'PM1 subs']


valve_vals = [{'name': 'measured',         'local name': '.Measured',        'type': 'Valve position', 'units': 'mil'},
              {'name': 'working setpoint', 'local name': '.WorkingSetpoint', 'type': 'Valve position', 'units': 'mil'},
              {'name': 'setpoint',         'local name': '.Setpoint',        'type': 'Valve position', 'units': 'mil'},
              {'name': 'ramp rate',        'local name': '.RampRate',        'type': 'Ramp rate',      'units': 'mil/s'}]

temp_vals = [{'name': 'measured',         'local name': '.Measured',        'type': 'Temperature',    'units': '°C'},
             {'name': 'working setpoint', 'local name': '.WorkingSetpoint', 'type': 'Temperature',    'units': '°C'},
             {'name': 'setpoint',         'local name': '.Setpoint',        'type': 'Temperature',    'units': '°C'},
             {'name': 'ramp rate',        'local name': '.RampRate',        'type': 'Ramp rate',      'units': '°C/s'},
             {'name': 'output percent',   'local name': '.OutputPercent',   'type': 'Output percent', 'units': '% of max voltage'}]

shutter_vals = [{'name': 'shutter status', 'local name': '.ShutterStatus', 'type': 'Status', 'units': '0 = open'}]

ps_vals = [{'name': 'voltage',        'local name': '_Voltage.Reading',     'type': 'Voltage', 'units': 'V'},
           {'name': 'current',        'local name': '_Current.Reading',     'type': 'Current', 'units': 'A'},
           {'name': 'max current',    'local name': '_MaxCurrent.Reading',  'type': 'Current', 'units': 'A'},
           {'name': 'operation mode', 'local name': '_OperationMode.Value', 'type': 'Status',  'units': '0 = CC'}]

rot_vals = [{'name': 'measured',         'local name': '.Measured',        'type': 'Angle',         'units': '°'},
            {'name': 'working setpoint', 'local name': '.WorkingSetpoint', 'type': 'Angle',         'units': '°'},
            {'name': 'ramp rate',        'local name': '.RampRate',        'type': 'Rotation rate', 'units': 'rpm'}]

carbon_vals = [{'name': 'base measured',            'local name': '_base.Measured',           'type': 'Temperature', 'units': '°C'},
               {'name': 'current measured',         'local name': '_Current.Measured',        'type': 'Current', 'units': 'A'},
               {'name': 'current working setpoint', 'local name': '_Current.WorkingSetpoint', 'type': 'Current', 'units': 'A'},
               {'name': 'current setpoint',         'local name': '_Current.Setpoint',        'type': 'Current', 'units': 'A'},
               {'name': 'voltage measured',         'local name': '_Voltage.Measured',        'type': 'Voltage', 'units': 'V'},
               {'name': 'voltage working setpoint', 'local name': '_Voltage.WorkingSetpoint', 'type': 'Voltage', 'units': 'V'},
               {'name': 'voltage setpoint',         'local name': '_Voltage.Setpoint',        'type': 'Voltage', 'units': 'V'},
               {'name': 'operation mode',           'local name': '_PS_OperationMode.Value',  'type': 'Status', 'units': '0 = CC'},
               {'name': 'shutter status',           'local name': '_Current.ShutterStatus',   'type': 'Status', 'units': '0 = open'}]


for cp in control_points:

    if last_word(cp) == 'valve':
        vals = valve_vals
    elif last_word(cp) == 'rot':
        vals = rot_vals
    elif cp == 'C1':
        vals = carbon_vals
    else:
        vals = temp_vals + ps_vals

    if (last_word(cp) in ['valve', 'tip']) or (cp == 'Si1 base'):
        vals += shutter_vals


    for val in vals:
        value_name = cp + ' ' + val['name']
        loc = 'Molly'
        local_value_name = 'Instances.{}{}'.format(space_to_underscore(cp), val['local name'])
        meas_type = val['type']
        units = val['units']

        value_names_database[value_name] = {
            "Location": loc,
            "Local value name": local_value_name,
            "Measurement type": meas_type,
            "Units": units
        }

vals = ['main shutter closed', 'main shutter control', 'cryo1 gate', 'cryo1 gate closed', 'ion pump1 gate', 'ion pump1 gate closed']

lvals = ['MainShutter_Closed', 'MainShutter_Control', 'Cryo1_Gate', 'Cryo1_Gate_Closed', 'IonPump1_Gate', 'IonPump1_Gate_Closed']

for val, lval in zip(vals, lvals):
    value_names_database['GM1 ' + val] = {
        "Location": "Molly",
        "Local value name": 'Instances.GM1_' + lval + '.Value',
        "Measurement type": 'Status',
        "Units": '0 = open'
    }

for i in ['1', '2', '3', '4']:
    value_names_database['BF shutter ' + i] = {
        "Location": "Molly",
        "Local value name": 'Instances.BF_Shutter_' + i + '.Value',
        "Measurement type": 'Status',
        "Units": '0 = open'
    }

    value_names_database['BF shutter ' + i + ' status'] = {
        "Location": "Molly",
        "Local value name": 'Instances.BF_Shutter_' + i + '_Status.Value',
        "Measurement type": 'Status',
        "Units": '0 = open'
    }


vals = ['CT1 vacuum', 'GM1 vacuum', 'GM1 BFM', 'GM1 SRS vacuum', 'PM1 vacuum']

lvals = ['CT1_Vacuum', 'GM1_Vacuum', 'GM1_BFM', 'GM1_SRS_Vacuum', 'PM1_Vacuum']

for val, lval in zip(vals, lvals):
    value_names_database[val] = {
        "Location": "Molly",
        "Local value name": 'Instances.' + lval + '.Reading',
        "Measurement type": 'Pressure',
        "Units": 'Torr'
    }

value_names_database['GM1 BFM arm control'] = {
        "Location": "Molly",
        "Local value name": 'Instances.GM1_BFM_Arm_Control.Value',
        "Measurement type": 'Status',
        "Units": '0 = in'
}

value_names_database['GM1 BFM arm status'] = {
        "Location": "Molly",
        "Local value name": 'Instances.GM1_BFM_Arm_Status.Value',
        "Measurement type": 'Status',
        "Units": '0 = in'
}

for val in ['GM1', 'PM1', 'LL1']:
    value_names_database[val + ' recipe running status'] = {
        "Location": "Molly",
        "Local value name": 'Instances.' + val + '_RecipeRunning.Status',
        "Measurement type": 'Status',
        "Units": '0 = running'
    }

value_names_database["SVT time Robo MBE engine 1"] = {
    "Location": "SVT",
    "Local value name": "SVT Time (RoboMBE Engine 1)",
    "Measurement type": "Time",
    "Units": "s"
}
value_names_database["Pyro intensity 950"] = {
    "Location": "SVT",
    "Local value name": "PI 950",
    "Measurement type": "Pyrometer reading",
    "Units": ""
}
value_names_database["Pyro intensity 850"] = {
    "Location": "SVT",
    "Local value name": "PI 850",
    "Measurement type": "Pyrometer reading",
    "Units": ""
}
value_names_database["Refl uncalib 950"] = {
    "Location": "SVT",
    "Local value name": "Refl 950",
    "Measurement type": "Reflectance (unnormalized)",
    "Units": ""
}
value_names_database["Refl uncalib 470"] = {
    "Location": "SVT",
    "Local value name": "Refl 470",
    "Measurement type": "Reflectance (unnormalized)",
    "Units": ""
}
value_names_database["SVT time Robo MBE IS4K temp"] = {
    "Location": "SVT",
    "Local value name": "SVT Time (RoboMBE IS4K Temp)",
    "Measurement type": "Time",
    "Units": "s"
}
value_names_database["Emiss temp"] = {
    "Location": "SVT",
    "Local value name": "Emiss Temp",
    "Measurement type": "Temperature",
    "Units": "°C"
}
value_names_database["Ratio temp"] = {
    "Location": "SVT",
    "Local value name": "Ratio Temp",
    "Measurement type": "Temperature",
    "Units": "°C"
}
value_names_database["SVT time Robo MBE IS4K refl"] = {
    "Location": "SVT",
    "Local value name": "SVT Time (RoboMBE IS4K Refl)",
    "Measurement type": "Time",
    "Units": "s"
}
value_names_database["Refl calib 950"] = {
    "Location": "SVT",
    "Local value name": "Calib 950",
    "Measurement type": "Reflectance (normalized)",
    "Units": ""
}
value_names_database["Refl calib 470"] = {
    "Location": "SVT",
    "Local value name": "Calib 470",
    "Measurement type": "Reflectance (normalized)",
    "Units": ""
}
value_names_database["BET time"] = {
    "Location": "BET",
    "Local value name": "BET Time",
    "Measurement type": "Time",
    "Units": "s"
}
value_names_database["BET temp"] = {
    "Location": "BET",
    "Local value name": "BET Temp",
    "Measurement type": "Temperature",
    "Units": "°C"
}
value_names_database["ISP time"] = {
    "Location": "BET",
    "Local value name": "ISP Time",
    "Measurement type": "Time",
    "Units": "s"
}
value_names_database["ISP temp"] = {
    "Location": "BET",
    "Local value name": "ISP Temp",
    "Measurement type": "Temperature",
    "Units": "°C"
}
value_names_database["ISP integral"] = {
    "Location": "BET",
    "Local value name": "ISP Integral",
    "Measurement type": "Time",
    "Units": "s"
}


if __name__ == "__main__":
    ##### Output to csv file

    headers = ['Value name', 'Location', 'Local value name', 'Measurement type', 'Units']

    csv_str = 'Value name'

    for header in headers[1:]:
        csv_str += ',' + header

    csv_str += '\n'

    for vn in value_names_database:
        csv_str += vn 
        for header in headers[1:]:
            csv_str += ',' + value_names_database[vn][header]
        csv_str += '\n'

    with open("value_names_database.csv", 'w') as out_file:
        out_file.write(csv_str)