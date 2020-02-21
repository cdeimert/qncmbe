import datetime as datetime

from qncmbe.data_import.data_import_utils import parse_datetime_input

inputs = [
    '2020-02-06 11:53:00.0',
    '2020-02-06 11:53:20.2',
    '2020-02-06 11:53:20.0000002',
    '2020-02-06 11:53:20.0000006',
    '2020-02-06 11:53:20.9999999',
    '2020-02-06 11:53:00',
    '2020-02-06 11:53',
    '2020-02-31 11:53',
    '2020-02-06 11',
    '2020-02-06',
    '2020-02-06 24:53:00.0',
    datetime.date(2020, 2, 6),
    datetime.datetime(2020, 2, 6),
    datetime.datetime(2020, 2, 6, 3, 4, 5),
    1234,
]

for inp in inputs:

    if isinstance(inp, datetime.datetime):
        print(f'datetime object ({inp})', end='')
    elif isinstance(inp, datetime.date):
        print(f'date object ({inp})', end='')
    elif isinstance(inp, str):
        print(f'"{inp}"', end='')
    else:
        print(inp, end='')

    try:
        print(' --> ', parse_datetime_input(inp))
    except ValueError as e:
        print(' --> ', f'ValueError: "{str(e)}"')
