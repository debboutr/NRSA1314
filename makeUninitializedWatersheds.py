# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 21:13:00 2016

This script was run in a python console inside spyder, the Ipython console seems
to crash sporadically when using arcpy.  This is one of 2 scripts to create all 
watersheds for NRSA,in this script the watersheds can be composed solely of NHD 
Catchments, so all that is done is finding the right zone for each pointand then
selecting it's catchment with all of it's upstream catchments to then merge 
together with the Dissolve tool in Arc. Using the childrendirectory for the 
numpy files used in the 'findUpstreamNpy' function returns all upstream plus the
local catchment, with the exception of sinks, which is remedied in lines 63-65, 
so there are no values of length 0 in the UpComs dictionary. Uninitialized sites
need to be identified and joined with the VPU as is seen in the 2 tables, 
sites_vpu and uninit, which are merged and used for processing. Unitialized has 
the REACH_COMID and the corresponding CAT_COMID to be selected out of catchments

@author: Rdebbout
"""

import sys
import arcpy
import pandas as pd
import numpy as np
sys.path.append('D:/Projects/StreamCat')
from StreamCat_functions import findUpstreamNpy
# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
L_drive = 'L:/Priv/CORFiles/Geospatial_Library/Data/Project'
NHD_dir = 'D:/NHDPlusV21'
numpydir = 'D:/NHDPlusV21/StreamCat_npy/children'
zone = np.load('{}/StreamCat/QA/FlowlineComidsZone.npy'.format(L_drive))
arr = zone[:,0].astype(int)
intervpu_tbl = pd.read_csv('%s/SSWR1.1B/InterVPUtable/InterVPU.csv' % L_drive)
csv = 'StreamCat/NRSA13-14LandscapeRasters/NRSA1314_Sites_VPU.csv'
sites_vpu = pd.read_csv('{}/{}'.format(L_drive, csv))[['SITE_', 'UnitID', 
                                                'UnitType','DrainageID']]
sites_vpu = sites_vpu[sites_vpu['UnitType']=='VPU']
uninit_sites = pd.read_csv('D:/Projects/chkNRSA_Watersheds/uninitialized.csv')
sites_vpu = pd.merge(sites_vpu, uninit_sites, left_on='SITE_',
                     right_on='SITE_ID', how='right')
dict_store = 'C:/Users/Rdebbout/Desktop'
out = 'D:/Projects/NRSA13-14 Uninitialized Watersheds2'
cat =  'NHDPlusCatchment/Catchment.shp'
exp = "!SHAPE.AREA@SQUAREKILOMETERS!"
################################################################################


# Make dictionaries to run by zone, this was originally done to work with 
# geopandas so we would only have to load the catchment.shp file into memory
# one time for each zone.
UpComs = dict()
# get all the upstream catchments for a particular site
for cat_com in uninit_sites['CAT_COMID']:
    if cat_com in arr:
        vpu = zone[np.where(arr == cat_com)][:,1][0]
        UpComs[cat_com] = findUpstreamNpy(vpu, cat_com, numpydir).tolist() 
    else:
        UpComs[cat_com] = []
# Sinks aren't included in numpy files and need to be added to the 
# value where the key is negative so that all values have a length
# of at least 1
for j in UpComs:
    if j < 0:
        UpComs[j] = [j]
        
# find any watersheds that extend between VPUs to append dissolved polys
connectors_dict = dict()
tos = intervpu_tbl.thruCOMIDs.values
for cats in UpComs.keys():
    connectors_dict[cats] = [x for x in tos if x in UpComs[cats]] 
# get rid of empty items    
connectors_dict = {k:v for k,v in connectors_dict.items() if v}
################################################################################


# Dictionaries were saved when testing, due to long creation times
     
#np.save('{}/UpComs_uninit.npy'.format(dict_store), UpComs)       
#UpComs = np.load('{}/UpComs_uninit.npy'.format(dict_store)).item()
#np.save('{}/connectors_dict_uninit.npy'.format(dict_store), connectors_dict)
#connectors_dict = np.load('%s/connectors_dict_uninit.npy' % dict_store).item()
################################################################################
     
     
# create watersheds by selecting catchments in each VPU for porcessing by VPU
vpu_com = dict()
for coms in uninit_sites['CAT_COMID']:
    print coms
    vpu = sites_vpu.loc[sites_vpu['CAT_COMID'] == coms,'UnitID'].values[0]
    print vpu
    if not vpu_com.has_key(vpu):
        vpu_com[vpu] = []
    vpu_com[vpu].append(coms)
    
#Process
################################################################################
for vpu in vpu_com.keys():
    print vpu
    hr = sites_vpu.loc[sites_vpu['UnitID'] == vpu,'DrainageID'].values[0]
    for com in vpu_com[vpu]: 
        print com
        if len(UpComs[com]) == 1:
            feat = str(UpComs[com]).replace('[','(').replace(']',')')
            catQuery = '"FEATUREID" IN %s' % feat 
        if len(UpComs[com]) > 1:
            catQuery = '"FEATUREID" IN ' + str(tuple(UpComs[com]))    
        catchments = arcpy.MakeFeatureLayer_management(
        '%s/NHDPlus%s/NHDPlus%s/%s' % (NHD_dir, hr, vpu, cat),
        'catchments' , catQuery)
        # use a list of sites for site_ids that share a catchment
        sites =  sites_vpu.loc[sites_vpu['CAT_COMID']==com,'SITE_ID'].values
        for site in sites:
            sitef = site.replace('-','_').lower()
            if not arcpy.Exists('%s/%s.shp' % (out, sitef)):
                if com in connectors_dict.keys():
                    for upCom in connectors_dict[com]:
                        upPoly = arcpy.MakeFeatureLayer_management(
                        '{}/SSWR1.1B/InterVPUtable/{}.shp'.format(L_drive, 
                        upCom))
                        arcpy.Append_management(upPoly, catchments)
                arcpy.Dissolve_management(catchments, 
                                          '%s/%s.shp' % (out, sitef))
            shp = arcpy.MakeFeatureLayer_management('%s/%s.shp' % (out, sitef))
            arcpy.AddField_management(shp, "SITE_ID", "TEXT")
            arcpy.AddField_management(shp, "CAT_COMID", "LONG")
            arcpy.AddField_management(shp, "AreaSqKM", "DOUBLE")
            arcpy.CalculateField_management(shp, "AreaSqKM", exp, "PYTHON_9.3")
            arcpy.DeleteField_management(shp, ["Id"])
            rows = arcpy.da.UpdateCursor(shp, ["SITE_ID","CAT_COMID"])
            for row in rows:
                row[0] = site
                row[1] = com
                rows.updateRow(row) 
            del rows
            arcpy.Delete_management(shp)
        arcpy.Delete_management(catchments)
