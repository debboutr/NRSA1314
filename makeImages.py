# -*- coding: utf-8 -*-
"""
Created on Wed May 18 15:58:53 2016

Using NHD and output from SplitCatchments0.py to create images that can quickly 
be viewed to isolate problem sites that may need to be dealt with by hand.

@author: Rdebbout
"""

import sys
import os
import arcpy
import pandas as pd
from StreamCat_functions import makeVPUdict, findUpstreamNpy

NHD_dir ='D:/NHDPlusV21'
home = 'F:/NRSA13-14 Watersheds'
hrTbl = pd.read_csv('%s/sitesNHDPlus.csv' % home)
inputs = makeVPUdict(NHD_dir)
mxd = arcpy.mapping.MapDocument('F:/NRSA13-14 Watersheds/makeImages.mxd')
df = arcpy.mapping.ListDataFrames(mxd)[0]
outTable = '%s/Images' % home
for f in os.listdir(home):
    if '-' in f and 'ws' in f:
        print f[2:]
        zone = hrTbl.ix[hrTbl.NRSA_ID == f[2:]].HYDROREG.values[0]
        hr = inputs[zone]
#        print hr + '   ' + unit
#        print '%s/%s' % (home, f)
        addCatch = arcpy.mapping.Layer('%s/%s/catchment.shp' % (home, f))
        arcpy.ApplySymbologyFromLayer_management(addCatch, '%s/catchment.lyr' % home)
        arcpy.mapping.AddLayer(df, addCatch,"BOTTOM")
        addWshed = arcpy.mapping.Layer('%s/%s/wshed' % (home, f))
        arcpy.ApplySymbologyFromLayer_management(addWshed, '%s/wshed.lyr' % home)
        arcpy.mapping.AddLayer(df, addWshed,"TOP")
        addPpt = arcpy.mapping.Layer('%s/%s/snappnt' % (home, f))
        arcpy.ApplySymbologyFromLayer_management(addPpt, '%s/wshed.lyr' % home)
        arcpy.mapping.AddLayer(df, addPpt,"TOP")  
        
        addFL = arcpy.mapping.Layer('%s/NHDPlus%s/NHDPlus%s/NHDSnapshot/Hydrography/NHDFlowline.shp' % (NHD_dir, hr, zone))
        arcpy.ApplySymbologyFromLayer_management(addFL, '%s/NHDFlowline.lyr' % home)
        arcpy.mapping.AddLayer(df, addFL, "TOP") 
        
        addPt = arcpy.mapping.Layer('%s/%s/pointShape.shp' % (home, f))
        arcpy.ApplySymbologyFromLayer_management(addPt, '%s/pointShape.lyr' % home)
        arcpy.mapping.AddLayer(df, addPt,"TOP")
        
        arcpy.mapping.ExportToPDF(mxd, r"%s/%s.pdf" % (outTable, f[2:]), df,
                          df_export_width=1600,
                          df_export_height=1200,
                          resolution = 47)
        for lyr in arcpy.mapping.ListLayers(mxd):
            arcpy.mapping.RemoveLayer(df, lyr)

############################################################################################

#hold = findUpstreamNpy('01', 6118946, 'D:/Projects/ALL_FLOWLINE_NUMPY/bastards')
#
#8450122 in hold
#import numpy as np
#tbl = pd.read_csv('D:/Projects/Panoramio/flickPicsQuick_DUL.csv')
#
#numpy_dir = 'D:/Projects/ALL_FLOWLINE_NUMPY/bastards'
#zone = '06'
#com = 4364666 in comids
#type(com)
#    comids = np.load(numpy_dir + '/comids' + zone + '.npy')
#    lengths= np.load(numpy_dir + '/lengths' + zone + '.npy')
#    upStream = np.load(numpy_dir + '/upStream' + zone + '.npy')
#    itemindex = int(np.where(comids == com)[0])
#    n = lengths[:itemindex].sum()
#    arrlen = lengths[itemindex]
#    return upStream[n:n+arrlen]