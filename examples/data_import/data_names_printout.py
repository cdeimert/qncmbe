'''
Super simple script which just prints out the allowed value names for
qncmbe.data_import
'''

from qncmbe.data_import.data_names import index

print("--- Allowed value names in qncmbe.data_import ---")
print('\n'.join(index.get_names_list()))
print("-------------------------------------------------")
