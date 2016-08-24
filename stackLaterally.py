# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 11:23:08 2016

@author: Rdebbout
"""
import os
import pandas as pd

others = ['awch','bdh', 'bedrock_perm', 'BFI','cti','et','fstfrz','kfact','lstfrz','omh','PerDun','PerHor','precip','PsumWs','PSUMPY_2013','PSUMPY_2014','rdh','rhmean','Runoff','tmax','tmean','TMEANPW_2013','TMEANPW_2014','tmeanss_2013','tmeanss_2014','tmeansy_2013','tmeansy_2014','tmin','wdmax','wdmin','wdsum', 'wtdph']

for csv in os.listdir('D:/Projects/chkNRSA_Watersheds/Output_08_16'):
    if '.csv' in csv:
        print csv
        tbl = pd.read_csv('D:/Projects/chkNRSA_Watersheds/Output_08_16/%s' % csv)        
        tbl2 = pd.read_csv('D:/Projects/chkNRSA_Watersheds/Uninit/%s' % csv)
        cols = tbl2.columns.tolist()

        tbl.columns = [c.upper() for c in tbl.columns]
        tbl2.columns = [c.upper() for c in tbl2.columns]
        tbl3 = pd.concat([tbl,tbl2])
        tbl3.columns = cols
        tbl3.to_csv('D:/Projects/chkNRSA_Watersheds/Output_08_18/%s' % csv, index=False)
        
out_dir = 'D:/Projects/chkNRSA_Watersheds/Output_08_18' 
count = 0     
for csv in os.listdir(out_dir):
    if '.csv' in csv and not 'permh' in csv:
        print csv
        tbl = pd.read_csv('%s/%s' % (out_dir, csv))
        if 'Elev' in csv:
            tbl = tbl[['SITE_ID','ELEV_WS','ELEV_WS_MIN','ELEV_WS_MAX','ELEV_WS_PctFull']]
        if 'nlcd' in csv:
            tbl = tbl[['SITE_ID'] + [ttl for ttl in tbl.columns if 'Pct' in ttl[:3]] + ['nlcd2011_WS_PctFull']]
        if 'geol' in csv:
            if 'reedbush' in csv:
                tbl['GEOL_REEDBUSH_DOM']= tbl.ix[:,37:-1].idxmax(axis=1)
                tbl['GEOL_REEDBUSH_DOM_PCT']= tbl.ix[:,37:-1].max(axis=1)
                tbl = tbl[['SITE_ID'] + ['GEOL_REEDBUSH_DOM', 'GEOL_REEDBUSH_DOM_PCT']]
            if 'hunt' in csv:
                tbl['GEOL_HUNT_DOM'] = tbl.ix[:,145:-1].idxmax(axis=1)
                tbl['GEOL_HUNT_DOM_PCT'] = tbl.ix[:,145:-1].max(axis=1)
                tbl = tbl[['SITE_ID'] + ['GEOL_HUNT_DOM', 'GEOL_HUNT_DOM_PCT']]
        if csv.split('.')[0] in others:
            tbl = tbl [['SITE_ID'] + tbl.columns[-2:].tolist()]
        print len(tbl)
        if count == 0:
            final = tbl.copy()
        if count > 0:
            final = pd.merge(final, tbl, on='SITE_ID', how='left')
        count += 1


tbl = pd.read_csv('%s/%s' % (out_dir, csv))
add = tbl[['SITE_ID', 'REACH_COMID', 'CAT_COMID', 'WsAreaSqKm']]
allAboard = pd.merge(add, final, on='SITE_ID')
allAboard.to_csv('D:/Projects/chkNRSA_Watersheds/allAboard.csv', index=False)





allcols = allAboard.columns.tolist()
old = pd.read_csv('L:/Priv/CORFiles/Geospatial_Library/Data/Project/StreamCat/NRSA13_14_FinalTables/NRSA13_14_Landscape_Metrics_20160801.csv')
oldcols = old.columns.tolist()
rmv = allcols[3:]

allAboard.columns = allAboard.columns[:30].tolist() + [b + '_WS' for b in allAboard.columns[30:46].tolist()] + allAboard.columns[46:].tolist()
allAboard.columns = allAboard.columns[:46].tolist() + ['NLCD_WS_PctFull'] + allAboard.columns[47:].tolist()

for x in rmv:
   if not 'BEDROCK' in x:
       old = old.drop(x, axis=1)

    if not x in oldcols:
        print x
allAboard = allAboard.drop('REACH_COMID', axis=1)
allAboard = allAboard.drop('CAT_COMID', axis=1)
zen = pd.merge(old, allAboard, on='SITE_ID')
zin = zen[nucols]
zin.to_csv('D:/Projects/chkNRSA_Watersheds/NRSA13_14_Landscape_Metrics_20160818.csv', index=False)
        
hold = allAboard.copy()

nucols = ['SITE_ID',
 'REACH_COMID',
 'CAT_COMID',
 'LAT_DD83',
 'LON_DD83',
 'WsAreaSqKm',
 'AWCH_WS',
 'AWCH_WS_PctFull',
 'BDH_WS',
 'BDH_WS_PctFull',
 'BEDROCK_PERM_WS',
 'BEDROCK_PERM_WS_PctFull',
 'BFI_WS',
 'BFI_WS_PctFull',
 'ELEV_PT',
 'ELEV_WS',
 'ELEV_WS_MIN',
 'ELEV_WS_MAX',
 'ELEV_WS_PctFull',
 'ET_WS',
 'ET_WS_PctFull',
 'FSTFRZ_WS',
 'FSTFRZ_WS_PctFull',
 'GEOL_HUNT_PT',
 'GEOL_HUNT_WS_DOM',
 'GEOL_HUNT_DOM_PCT',
 'GEOL_HUNT_DOM_DESC',
 'GEOL_REEDBUSH_PT',
 'GEOL_REEDBUSH_DOM',
 'GEOL_REEDBUSH_DOM_PCT',
 'KFACT_PT',
 'KFACT_WS',
 'KFACT_WS_PctFull',
 'LSTFRZ_PT',
 'LSTFRZ_WS',
 'LSTFRZ_WS_PctFull',
 'MAFLOWU',
 'MAST_2013',
 'MAST_2014',
 'MAVELU',
 'MSST_2013',
 'MSST_2014',
 'MWST_2013',
 'MWST_2014',
 'OMH_WS',
 'OMH_WS_PctFull',
 'PctOw2011_WS',
 'PctIce2011_WS',
 'PctUrbOp2011_WS',
 'PctUrbLo2011_WS',
 'PctUrbMd2011_WS',
 'PctUrbHi2011_WS',
 'PctBl2011_WS',
 'PctDecid2011_WS',
 'PctConif2011_WS',
 'PctMxFst2011_WS',
 'PctShrb2011_WS',
 'PctGrs2011_WS',
 'PctHay2011_WS',
 'PctCrop2011_WS',
 'PctWdWet2011_WS',
 'PctHbWet2011_WS',
 'NLCD_WS_PctFull',
 'PERDUN_WS',
 'PERDUN_WS_PctFull',
 'PERHOR_WS',
 'PERHOR_WS_PctFull',
 'PRECIP_WS',
 'PRECIP_WS_PctFull',
 'PSUMPY_2013_PT',
 'PSUMPY_2013_WS',
 'PSUMPY_2013_WS_PctFull',
 'PSUMPY_2014_PT',
 'PSUMPY_2014_WS',
 'PSUMPY_2014_WS_PctFull',
 'PSUM_PT',
 'PSUM_WS',
 'PSUM_WS_PctFull',
 'RDH_PT',
 'RDH_WS',
 'RDH_WS_PctFull',
 'RHMEAN_PT',
 'RHMEAN_WS',
 'RHMEAN_WS_PctFull',
 'RUNOFF_WS',
 'RUNOFF_WS_PctFull',
 'TMAX_WS',
 'TMAX_WS_PctFull',
 'TMEANPW_2013_PT',
 'TMEANPW_2013_WS',
 'TMEANPW_2013_WS_PctFull',
 'TMEANPW_2014_PT',
 'TMEANPW_2014_WS',
 'TMEANPW_2014_WS_PctFull',
 'TMEANSS_2013_PT',
 'TMEANSS_2013_WS',
 'TMEANSS_2013_WS_PctFull',
 'TMEANSS_2014_PT',
 'TMEANSS_2014_WS',
 'TMEANSS_2014_WS_PctFull',
 'TMEANSY_2013_PT',
 'TMEANSY_2013_WS',
 'TMEANSY_2013_WS_PctFull',
 'TMEANSY_2014_PT',
 'TMEANSY_2014_WS',
 'TMEANSY_2014_WS_PctFull',
 'TMEAN_WS',
 'TMEAN_WS_PctFull',
 'TMIN_PT',
 'TMIN_WS',
 'TMIN_WS_PctFull',
 'TOPWET_WS',
 'TOPWET_WS_PctFull',
 'WDMAX_PT',
 'WDMAX_WS',
 'WDMAX_WS_PctFull',
 'WDMIN_PT',
 'WDMIN_WS',
 'WDMIN_WS_PctFull',
 'WDSUM_PT',
 'WDSUM_WS',
 'WDSUM_WS_PctFull',
 'WTDH_PT',
 'WTDPH_WS',
 'WTDPH_WS_PctFull']
 
import os
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd)[0]
place = 'D:/Projects/NRSA13-14 Uninitialized Watersheds'
for f in os.listdir(place):  
    if '.shp' in f and not '.xml' in f:
        addLayer = arcpy.mapping.Layer('%s/%s' % (place, f))
        arcpy.mapping.AddLayer(df,addLayer,"BOTTOM")
count = 0
g = []      
for f in os.listdir(place):      
    if '.shp' in f and not '.xml' in f:
        if not f.split('.')[0].upper().replace('_','-') in sites_vpu.SITE_ID.values:
            print f
            print count
        count += 1
        
        
count = 0
g = []      
for f in os.listdir('D:/Projects/NRSA13-14 Watersheds/workSHPS'):      
    if '.shp' in f and not '.xml' in f:
        print f
        count += 1
place = 'L:/Priv/CORFiles/Geospatial_Library/Data/RESOURCE/PHYSICAL/WATERSHEDS/NRSA13-14/NRSA13-14_IndividualWatersheds.gdb'        
arcpy.ListFeatureClasses(place)