# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 10:47:36 2016

This script gathers StreamCat Comids that are on uninitialized flowlinesin the
NRSA survey and processes to match the tables that are output from the 
splitCat_ZStats_SITES.py process, they can be appened together to create final
tables for the survey data.


@author: Rdebbout
"""

import sys
import numpy as np
import pandas as pd
ctl = pd.read_csv(sys.argv[1])  
#ctl = pd.read_csv('L:/Priv/CORFiles/Geospatial_Library/Data/Project/SSWR1.1B/ControlTables/ControlTable_NRSA_RD.csv')
out_dir = ctl.DirectoryLocations.values[7]  
NHD_dir = ctl.DirectoryLocations.values[4]
upDir = ctl.DirectoryLocations.values[5]      
uninit = pd.read_csv(ctl.DirectoryLocations.values[6])
inputs = np.load('%s/StreamCat_npy/zoneInputs.npy' % NHD_dir).item()
      
for line in range(len(ctl.values)):
    if ctl.run[line] == 1:
        print 'running ' + str(ctl.FullTableName[line])
        metric = str(ctl.FullTableName[line])
        accum_type = ctl.accum_type[line]
        conversion = float(ctl.Conversion[line])
        for zone in inputs:
            add = pd.read_csv('%s/%s_%s.csv' %(upDir, metric, zone))
            add = add.ix[add.COMID.isin(uninit.CAT_COMID)]
            if zone == '06':
                addFinal = add.copy()
            else:
                addFinal = pd.concat([addFinal,add])
        addFinal.WsPctFull = addFinal.WsPctFull.fillna(0)
        final = pd.merge(uninit, addFinal, left_on='CAT_COMID', right_on='COMID')
        final = final.drop('COMID', axis=1)
        if accum_type == 'Continuous':
            metricName = ctl.MetricName[line]
            final[metricName.upper() + '_WS'] = (final['WsSum'] / final['WsCount']) / conversion
            if ctl.ByRPU[line] == 1:
                final['ELEV_WS_MAX']= final.ix[:,['CatMAX','UpCatMAX']].max(axis=1) / conversion
                final['ELEV_WS_MIN']= final.ix[:,['CatMIN','UpCatMIN']].min(axis=1) / conversion
            final[metricName.upper() + '_WS_PctFull'] = final['WsPctFull']           
        if accum_type == 'Categorical':
            lookup = pd.read_csv(ctl.MetricName[line])
            for idx in range(len(lookup)):
                final['Pct' + lookup.final_val[idx]] = ((final['Ws' + lookup.raster_val[idx]] * 1e-6) / final['WsAreaSqKm']) * 100
            final[ctl.FullTableName[line] + '_WS_PctFull'] = final['WsPctFull']       
        final.to_csv('%s/%s.csv' % (out_dir, ctl.FullTableName[line]), index=False)
        