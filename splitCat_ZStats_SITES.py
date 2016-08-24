# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 11:49:24 2016

@author: Rdebbout
"""
import sys
import os
import arcpy
import numpy as np
import pandas as pd
import georasters as gr 
import geopandas as gpd
from geopandas.tools import sjoin
#ctl = pd.read_csv('L:/Priv/CORFiles/Geospatial_Library/Data/Project/SSWR1.1B/ControlTables/ControlTable_NRSA_RD.csv') #
ctl = pd.read_csv(sys.argv[1]) #'L:/Priv/CORFiles/Geospatial_Library/Data/Project/SSWR1.1B/ControlTables/ControlTable_NRSA_RD.csv'
sys.path.append('D:/Projects/StreamCat')
from StreamCat_functions import dbf2DF, chkColumnLength
arcpy.CheckOutExtension("spatial")
from arcpy.sa import TabulateArea, ZonalStatisticsAsTable
arcpy.env.cellSize = "30"  

WsRasterPath = ctl.DirectoryLocations.values[0] 
ingrid_dir = ctl.DirectoryLocations.values[1]
out_dir = ctl.DirectoryLocations.values[2]  
NHD_dir = ctl.DirectoryLocations.values[4]
upDir = ctl.DirectoryLocations.values[5]
#########################################################################################
##convert to tifs from the GRIDs that are made with the SplitCatchments).py script
#home = 'L:/Priv/CORFiles/Geospatial_Library/Data/Project/StreamCat/NRSA13-14Watersheds'
#uid = pd.read_csv('D:/Projects/chkNRSA_Watersheds/sitesUID.csv')
#for index, row in uid.iterrows():
#    wsID = 'ws' + row['SITE_ID']
#    if not os.path.exists('D:/Projects/chkNRSA_Watersheds/Watersheds_08_16/' + wsID):
#        print wsID
#        comid = row['UID']
#        print comid
#        r = gr.from_file('{}/{}/wshed'.format(home, wsID))
#        r.datatype=4
##        r.nodata_value = 4294967295.0  works for some but not all....
#        r = r*comid
#        r.to_tiff('D:/Projects/chkNRSA_Watersheds/Watersheds_08_16/' + wsID)
#########################################################################################
for line in range(len(ctl.values)):
    if ctl.run[line] == 1:
        count = 0
        print 'running ' + str(ctl.FullTableName[line])
        accum_type = ctl.accum_type[line]
        inputs = np.load('%s/StreamCat_npy/zoneInputs.npy' % NHD_dir).item()
        join = pd.read_csv('D:/Projects/chkNRSA_Watersheds/sitesUID.csv')
        if ctl.ByRPU[line] == 1:
            zones = gpd.GeoDataFrame.from_file('D:/NHDPlusV21/NHDPlusGlobalData/BoundaryUnit.shp')
            zones = zones.ix[zones.UnitType == 'RPU']
            rpuinputs = np.load('%s/StreamCat_npy/rpuInputs.npy' % NHD_dir).item()
            pts  = gpd.GeoDataFrame.from_file('D:/Projects/chkNRSA_Watersheds/NRSA13_14_SiteData.shp')            
        for f in os.listdir(WsRasterPath):
            if '.tif' in f and not '.vat' in f and not '.xml' in f and not '.ovr' in f:  #USED WITH RASTERS!
                inZoneData = '%s/%s' % (WsRasterPath, f)
                uid = f.split('.')[0][2:]
                conversion = float(ctl.Conversion[line])
                outTables = {} # this was established for multiple rpus, not needed anymore, but won't hold anything up
                if ctl.ByRPU[line] == 1:                                      
                    pt = pts.ix[pts.SITE_ == uid]
                    joined = sjoin(pt, zones)                    
                    rpus = joined.UnitID.tolist()
                    for unit in rpus:
                        reg = [rpu for rpu in rpuinputs if unit in rpuinputs[rpu]][0]
                        hr = inputs[reg]
                        valras = '%s/NHDPlus%s/NHDPlus%s/NEDSnapshot/ned%s/elev_cm' % (NHD_dir, hr, reg, unit)
                        out = '%s/Zstats_%s_%s_%s.dbf' % (out_dir, ctl.FullTableName[line], uid, unit)
                        outTables[out] = valras
                if ctl.ByRPU[line] == 0:   
                    valras = '%s/%s' % (ingrid_dir, ctl.LandscapeLayer[line])
                    out = '%s/Zstats_%s_%s.dbf' % (out_dir, ctl.FullTableName[line], uid)
                    outTables[out] = valras
                for outTable in outTables:
                    if not os.path.exists(outTable):
                        if accum_type == 'Categorical':
                            TabulateArea(inZoneData, 'Value', outTables[outTable], 'Value', outTable, "30")
                        if accum_type == 'Continuous':
                            ZonalStatisticsAsTable(inZoneData, 'Value', outTables[outTable], outTable, "DATA", "ALL")
                        os.remove(outTable +'.xml')
                        os.remove(outTable.split('.')[0] + '.cpg')
                if len(outTables) > 1:
                    count = 0
                    for outTable in outTables:
                        tbl2 = dbf2DF(outTable)
                        if count == 0:
                            t = tbl2.copy()
                        if count > 0:
                            t = pd.concat([tbl2, t])
                        count += 1
                    tbl = pd.DataFrame({'VALUE' : t.VALUE.values[0], 'SUM' : sum(t.SUM), \
                    'COUNT' : sum(t.COUNT), 'MAX' : t.MAX.max(), 'MIN' : t.MIN.min()}, index=[0])
                if len(outTables) == 1:
                    tbl = dbf2DF(outTable)
                ras = gr.from_file(inZoneData)
                AreaSqKM = (ras.count() * 900) * 1e-6
                if accum_type == 'Categorical':
                    tbl = chkColumnLength(tbl, valras)
                    tbl.insert(1, 'AreaSqKm', [AreaSqKM])
                    cols = tbl.columns.tolist()[2:]
                    tbl['TotCount'] = tbl[cols].sum(axis=1)
                    tbl['PctFull'] = (((tbl.TotCount * 1e-6) / AreaSqKM) * 100) #work here
                    tbl = tbl[['VALUE','AreaSqKm'] + cols + ['PctFull']]
                    tbl.columns = ['UID','CatAreaSqKm'] + ['Cat' + y for y in cols] + ['CatPctFull']
                if accum_type == 'Continuous':
                    metricName = ctl.MetricName[line]
                    tbl.insert(1, 'AreaSqKm', [AreaSqKM])
                    tbl['PctFull'] = ((tbl.COUNT / ras.count()) * 100)
                    if ctl.ByRPU[line] == 1:                        
                        tbl = tbl[['VALUE', 'AreaSqKm', 'COUNT', 'SUM', 'MAX', 'MIN', 'PctFull']]
                        cols = tbl.columns.tolist()[1:]
                        tbl.columns = ['UID'] +['Cat' + y[0] + y[1:].lower() for y in cols]  #.lower() to match names with StreamCat
                    if ctl.ByRPU[line] == 0:
                        tbl = tbl[['VALUE','AreaSqKm','COUNT','SUM','PctFull']]
                        cols = tbl.columns.tolist()[1:]
                        tbl.columns = ['UID'] + ['Cat' + y[0] + y[1:].lower() for y in cols]  #.lower() to match names with StreamCat
                if np.isnan(tbl['UID'][0]):
                    tbl['UID'] = join.ix[join.SITE_ID == uid].UID.values[0]  # retain UID if there was no coverage
                #stack to complete table and add pct full with areas
                if count == 0:
                    final = tbl.copy()
                if count > 0:
                    final = pd.concat([final, tbl])
                count += 1
        final['CatPctFull'] = final['CatPctFull'].fillna(0)
        final = pd.merge(join, final, on='UID')
        for zone in inputs:
            add = pd.read_csv('%s/%s_%s.csv' %(upDir, ctl.FullTableName[line], zone))
            add = add.ix[add.COMID.isin(final.CAT_COMID)]
            columns = [x for x in add.columns if 'Up' in x]
            add = add[['COMID'] + columns]
            if zone == '06':
                addFinal = add.copy()
            else:
                addFinal = pd.concat([addFinal,add])
        addFinal.UpCatPctFull = addFinal.UpCatPctFull.fillna(0)        
        print 'final length %s : %s' % (ctl.FullTableName[line],str(len(final)))
        r = pd.merge(final, addFinal, left_on='CAT_COMID', right_on='COMID')
        print 'r length %s : %s' % (ctl.FullTableName[line],str(len(r)))
        r = r.drop('COMID',axis=1)
        r['WsAreaSqKm'] = r.CatAreaSqKm + r.UpCatAreaSqKm.fillna(0)
        if accum_type == 'Continuous':
            r['WsCount'] = r.CatCOUNT.fillna(0) + r.UpCatCount.fillna(0)
            r['WsSum'] = r.CatSUM.fillna(0) + r.UpCatSum.fillna(0)
            if ctl.ByRPU[line] == 1:
                r['WsMAX']= r.ix[:,['CatMAX','UpCatMAX']].max(axis=1)
                r['WsMIN']= r.ix[:,['CatMIN','UpCatMIN']].min(axis=1)
            r['UpCatAreaSqKm'] = r['UpCatAreaSqKm'].fillna(0)
            r['UpCatPctFull'] = r['UpCatPctFull'].fillna(0)
            r['WsPctFull'] = ((r['CatAreaSqKm'] *  r['CatPctFull']) + (r['UpCatAreaSqKm'] *  r['UpCatPctFull'])) /  (r['CatAreaSqKm'] +  r['UpCatAreaSqKm'])
            r.loc[r.loc[:,('WsPctFull')] == 0,('WsCount')] = np.nan
            r.loc[r.loc[:,('WsPctFull')] == 0,('WsSum')] = np.nan
            r['UpCatPctFull'] = r['UpCatPctFull'].fillna(0)
            r[metricName.upper() + '_WS'] = (r['WsSum'] / r['WsCount']) / conversion
            if ctl.ByRPU[line] == 1:
                r['ELEV_WS_MAX']= r.ix[:,['CatMAX','UpCatMAX']].max(axis=1) / conversion
                r['ELEV_WS_MIN']= r.ix[:,['CatMIN','UpCatMIN']].min(axis=1) / conversion
            r[metricName.upper() + '_WS_PctFull'] = r['WsPctFull']
        if accum_type == 'Categorical':
            lookup = pd.read_csv(ctl.MetricName[line])
            for name in lookup.raster_val.values:
                r['Ws' + name] = r['Cat' + name].fillna(0) + r['UpCat' + name].fillna(0)
            columns = ['Ws' + g for g in lookup.raster_val]    
            r['TotCount'] = r[columns].sum(axis=1) * 1e-6        
            r['WsPctFull'] = (r['TotCount'] / r['WsAreaSqKm']) * 100
            r = r.drop('TotCount', axis=1)
            for idx in range(len(lookup)):
                r['Pct' + lookup.final_val[idx]] = ((r['Ws' + lookup.raster_val[idx]] * 1e-6) / r['WsAreaSqKm']) * 100
            r[ctl.FullTableName[line] + '_WS_PctFull'] = r['WsPctFull']
        r.to_csv('%s/%s.csv' % (out_dir, ctl.FullTableName[line]), index=False)    
        
############################################################################################
# Stack all of the metrics into one file !!Make sure PermH is out of the csv list!!
#others = ['awch','bdh','BFI','cti','et','fstfrz','kfact','lstfrz','omh','PerDun','PerHor','precip','PsumWs','PSUMPY_2013','PSUMPY_2014','rdh','rhmean','Runoff','tmax','tmean','TMEANPW_2013','TMEANPW_2014','tmeanss_2013','tmeanss_2014','tmeansy_2013','tmeansy_2014','tmin','wdmax','wdmin','wdsum', 'wtdph']
#count = 0
#for csv in os.listdir(out_dir):
#    if '.csv' in csv:
#        print csv
#        tbl = pd.read_csv('%s/%s' % (out_dir, csv))
#        if 'Elev' in csv:
#            tbl['ELEV_WS_MIN'] =  tbl.WsMIN / 100
#            tbl['ELEV_WS_MAX'] =  tbl.WsMAX / 100
#            tbl = tbl[['CatCOMID','ELEV_WS','ELEV_WS_MIN','ELEV_WS_MAX','ELEV_WS_PctFull']]
#        if 'nlcd' in csv:
#            tbl = tbl[['CatCOMID'] + [ttl for ttl in tbl.columns if 'Pct' in ttl[:3]] + ['nlcd2011_WS_PctFull']]
#        if 'bedrock' in csv:
#            tbl = tbl[['CatCOMID'] + [ttl for ttl in tbl.columns if 'Pct' in ttl[:3]] + ['bedrock_perm_WS_PctFull']]
#        if 'geol' in csv:
#            continue
#        if csv.split('.')[0] in others:
#            tbl = tbl [['CatCOMID'] + tbl.columns[-2:].tolist()]
#        print len(tbl)
#        if count == 0:
#            final = tbl.copy()
#        if count > 0:
#            final = pd.merge(final, tbl, on='CatCOMID', how='left')
#        count += 1
#for col in final.columns:
#    if 'WS_PctFull' in col:
#        final[col] = final[col].fillna(0)
#final.to_csv('%s/final_84.csv' % ('/'.join(out_dir.split('/')[:-1])),index=False) 
#split and join are used so that the csv doesn't end up in the same directory where 
# we are searching and merging above
###########################################################################################        
#t1 = pd.read_csv('D:/Projects/chkNRSA_Watersheds/FINAL_RUN_WSHEDS_84/final_84.csv')
#t2 = pd.read_csv('D:/Projects/chkNRSA_Watersheds/FINAL_RUN_WSHEDS_14/final_14.csv')
#t3 = pd.read_csv('D:/Projects/chkNRSA_Watersheds/FINAL_RUN_WSHEDS_3/final_3.csv')
#
#t4 = pd.concat([t1,t2,t3])
#t4 = t4[t1.columns]
#t4.to_csv('D:/Projects/chkNRSA_Watersheds/final_101.csv', index=False)
#            
#for x in final.columns:
#    print x       
#total = pd.read_csv('//Aa/ord/COR/Data/Priv/CORFiles/Geospatial_Library/Data/Project/StreamCat/NRSA13_14_FinalTables/NRSA13_14_Landscape_Metrics_20160711.csv')
#s = total.ix[total.REACH_COMID.isin(t4.CatCOMID)]
#out_dir = 'D:/Projects/chkNRSA_Watersheds/tryScript'
#csv = 'bedrock_perm.csv'

#allComs = np.load('D:/Projects/chkNRSA_Watersheds/FlowlineComidsZone.npy')
#temp = allComs[:,0].astype(int)
#
#x = 15410047
#
#allComs[np.where(temp == x)]

#################################################################################
# add MIN/MAX to Elevation files


#for zone in inputs:
#    tbl1 = pd.read_csv('D:/Projects/chkNRSA_Watersheds/minmaxElev/UPElev_%s.csv' % zone)
#    tbl1.columns = ['COMID','CatMAX','CatMIN','UpCatMAX','UpCatMIN']
#    tbl2 = pd.read_csv('L:/Priv/CORFiles/Geospatial_Library/Data/Project/StreamCat/Allocation_and_Accumulation/Elev_%s.csv' % zone)
#    tbl3 = pd.merge(tbl1,tbl2, on='COMID')
#    tbl3 = tbl3[['COMID','CatAreaSqKm', 'CatCount', 'CatSum', 'CatMAX', 'CatMIN', \
#        'CatPctFull', 'UpCatAreaSqKm','UpCatCount', 'UpCatSum', 'UpCatMAX', 'UpCatMIN',\
#        'UpCatPctFull', 'WsAreaSqKm', 'WsCount', 'WsSum', 'WsPctFull']]   
#    tbl3.to_csv('L:/Priv/CORFiles/Geospatial_Library/Data/Project/StreamCat/Allocation_and_Accumulation/Elev_%s.csv' % zone)
#    
#for zone in inputs:
#    fu = pd.read_csv('L:/Priv/CORFiles/Geospatial_Library/Data/Project/StreamCat/Allocation_and_Accumulation/Elev_%s.csv' % zone)
#    fu = fu.drop('Unnamed: 0', axis=1)
#    fu.to_csv('L:/Priv/CORFiles/Geospatial_Library/Data/Project/StreamCat/Allocation_and_Accumulation/Elev_%s.csv' % zone,index=False)