'''
Super simple script which just prints out the allowed value names for qncmbe.data_import
'''

import qncmbe.data_import.value_names as valnames

print("--- Allowed value names in qncmbe.data_import ---")
valnames.print_allowed_value_names()
print("-------------------------------------------------")