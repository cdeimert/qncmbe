'''
Super simple script which just prints out the allowed value names for qncmbe.data_export
'''

import qncmbe.data_export.value_names as valnames

print("--- Allowed value names in qncmbe.data_export ---")
valnames.print_allowed_value_names()
print("-------------------------------------------------")