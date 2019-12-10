import win32com.client
import os
import numpy as np

this_dir = os.path.dirname(os.path.abspath(__file__))

in_file = os.path.join(this_dir, 'Origin_digest_template.opj')
out_file = os.path.join(this_dir, 'Origin_digest_template_mod.opj')
out_file.capitalize()

origin = win32com.client.Dispatch("Origin.Application")

origin.Visible = 1

origin.Execute(f'doc -o {in_file}') # Short for "document -open" (https://www.originlab.com/doc/LabTalk/guide/Managing-the-Project#Open.2FSave_a_project)



# https://www.originlab.com/doc/LabTalk/guide
# Note, can test commands out directly in Origin terminal (launch from Origin with Alt+3)
# Still need to figure out how to set the column names. Maybe: https://www.originlab.com/doc/LabTalk/ref/Set-cmd
# Looks like there is a wks object which can call things. https://www.originlab.com/doc/LabTalk/ref/Wks-obj
# But need to activate the worksheet. Maybe get <worksheet name>? https://www.originlab.com/doc/LabTalk/ref/Get-cmd#Specifying_Worksheet.2C_Dataset_or_Data_Plot

worksheet_name = 'LabViewData'
origin.Execute(f'win -a {worksheet_name}') # Activate the given worksheet
ncols = 10
origin.Execute(f'wks.ncols={ncols}') # Set the number of columns in the active worksheet
for n in range(ncols):
    origin.Execute(f'col({n+1})[C]$ = Fuck you, Origin.') # C = Comment, U = Units, L = Long name

arrs = []
for n in range(ncols):
    arrs.append(np.array([1,2,3]) + n)

arr2d = np.stack(arrs).transpose()

origin.PutWorksheet("LabViewData",arr2d.tolist(),0,0)
origin.Execute(f'save {out_file}')
