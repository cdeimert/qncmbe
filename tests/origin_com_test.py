'''
Page names: SVTData,LabViewData, MollyData
'''


import numpy as np
import os
import random

thisdir = os.path.dirname(os.path.abspath(__file__))
template_file = os.path.join(thisdir, "Origin_digest_template.opj")

if True:
    import OriginExt as O
    app = O.Application()
    app.Visible = app.MAINWND_SHOW

    app.Load(template_file)
    
    wks = app.FindWorksheet("LabViewData")

    #wks = app.FindWorksheet("SVTData")
    wks.SetData([[1,2,3,4,5,6]],4,1) # row, col # Note SetData replaces the entire column, not just where there's overlap
    wks.SetData([[4,5,6]],0,2) # row, col
    wks.SetData([None],0,1) # row, col


    columns = wks.GetColumns()
    for n in range(5):
        col = next(columns)
        col.PutComments("test")

    wks = app.FindWorksheet("LabViewData")
    ncols = wks.GetColumns().GetCount()

    app.Save(template_file[:-4]+"_mod.opj")

    #wks.ClearData()
    #for col in wks.GetColumns():
    #    col.PutComments("Fuck you, Origin")

    #wks.Columns(0).SetLongName("TEST SVT time Robo MBE engine 1")
    #print(wks.GetColumns()[0].GetLongName())

else:
    import win32com.client

    origin = win32com.client.Dispatch("Origin.ApplicationSI")

    origin.Visible=1
    # #page_name = origin.CreatePage(2, "Python", "origin")

    origin.Execute(f'load "{template_file}"')
    print(origin.FindWorksheet("SVTData"))
    origin.PutWorksheet("SVTData",[1,2,3],0,0)
    #for col in wks.Columns:
    #    col.PutComments("test")

    #origin.PutWorksheet("SVTData", [1,2,3], 0,0)


    #wks.SetData([np.ones(4)], 0,0)
    #print(wks.Columns(0).GetLongName())
    # print(wks)
    # #origin.Execute("open Origin_digest_template.opj")


