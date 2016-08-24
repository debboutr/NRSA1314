# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 13:54:27 2016

Purpose: Create watershed shapefile for split catchment NRSA sites

This script was originally written to use geopandas and Shapely's unary_union 
tool to dissolve all of the geometries to make individual watershed shapefiles.
The output of this method withheld small skeleton fragments of catchment
boundary lines within the finished polygon. Arcpy was used to eliminate this 
problem.  This script creates the split-cat shapefiles from the .tif rasters
that are used in the zonal stats processing.  The upcatchments are selected from
the proper NHD zone and then, if another zone accumulates into it, that shape 
will also be appended before dissolving all of the combined polygons. Handling 
could be developed for reach_comids that have no associated catchmentID, but 
accumulate other catchments, there was only one case of this, MTSS-1272.

@author: mweber
"""

import os, sys
import arcpy
import pandas as pd
import numpy as np
sys.path.append('D:/Projects/StreamCat')
#from StreamCat_functions import dbf2DF, bastards, UpcomDict, findUpstreamNpy
from StreamCat_functions import findUpstreamNpy
#import geopandas as gpd
#import shapely

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

NHD_dir = 'D:/NHDPlusV21'
# NOTE that bastards are used with splitcats, not children as is used in the
# uninitialized watershed creation
numpydir = 'D:/NHDPlusV21/StreamCat_npy/bastards'
L_drive = 'L:/Priv/CORFiles/Geospatial_Library/Data/Project'
#array of each COMID with it's associated VPU
zone = np.load('%s/StreamCat/QA/FlowlineComidsZone.npy' % L_drive)
# this array allows us to find the VPU for each COMID
coms = zone[:,0].astype(int)
# read in the InterVPU table to find connections
intervpu_tbl = pd.read_csv("%s/SSWR1.1B/InterVPUtable/InterVPU.csv" % L_drive) 
# this csv was built by reading in the dbf from the NRSA sites shapefile and 
# then writing out as csv,
csv = 'StreamCat/NRSA13-14LandscapeRasters/NRSA1314_Sites_VPU.csv' 
sites_vpu = pd.read_csv('%s/%s' % (
                L_drive, csv))[['SITE_','DrainageID','UnitType','UnitID']]
# the shapefile had already been spatially joined with the global BoundaryUnits
# so we can do watersheds by VPU
sites_vpu = sites_vpu[sites_vpu['UnitType']=='VPU']
# this file properly identifies REACH_COMID and CAT_COMID, we need CAT_COMID
# for use with findUpstreamNpy
mets = 'StreamCat/NRSA13_14_FinalTables/NRSA13_14_Landscape_Metrics_20160801.csv'
nrsa_sites = pd.read_csv('%s/%s' % (L_drive, mets))\
                                    [['SITE_ID', 'REACH_COMID', 'CAT_COMID']]
sites_vpu = pd.merge(sites_vpu, nrsa_sites, left_on='SITE_', right_on='SITE_ID')

ras_dir = 'D:/Projects/chkNRSA_Watersheds/Watersheds_08_16'
splits = 'D:/Projects/splitSample'
upStream_dir = '%s/SSWR1.1B/InterVPUtable' % L_drive
out = 'D:/Projects/WsTEST'
cat =  'NHDPlusCatchment/Catchment.shp'
dict_store = 'C:/Users/Rdebbout/Desktop'

# Create split catchment shapefiles
for splitcats in [x for x in os.listdir(ras_dir) if x.count('.tif') and 
    not x.count('.cpg') and not x.count('.dbf') and not x.count('.xml')]:
    if splitcats.split('.')[0][2:] in nrsa_sites[['SITE_ID']].values:
        inras = "%s/%s" % (ras_dir,splitcats)
        splitf = splitcats.split('.')[0].replace('-','_')
        outshape = "%s/%s.shp" % (splits, splitf)
        if not arcpy.Exists(outshape):
            arcpy.RasterToPolygon_conversion(inras, outshape, "NO_SIMPLIFY",
                                             "Value")
            arcpy.AddField_management(outshape, "FEATUREID", "LONG")
            arcpy.CalculateField_management(outshape, "FEATUREID", "!GRIDCODE!",
                                            expression_type="PYTHON")
            arcpy.AddField_management(outshape, "SOURCEFC", "TEXT", 20)
            arcpy.AddField_management(outshape, "AreaSqKM", "DOUBLE", 19)
            arcpy.DeleteField_management(outshape, "ID")

# This can also be performed using gdal in the following fashion:
#>>gdal_polygonize wsALLS-1038.tif -f "ESRI Shapefile" ALLS-1038.shp "" "UID"

################################################################################


UpComs = dict()
# get all the upstream catchments for a particular site in it's hydro-region
# key is COMID, value is all upstream
for cat_com in nrsa_sites['CAT_COMID']:
    if cat_com in coms:
        vpu = zone[np.where(coms == cat_com)][:,1][0]
        UpComs[cat_com] = findUpstreamNpy(vpu, cat_com, numpydir).tolist() 
    else:
        UpComs[cat_com] = []

# find any watersheds that extend between VPUs
connectors_dict = dict()
tos = intervpu_tbl.thruCOMIDs.values
for cats in UpComs.keys():
    connectors_dict[cats] = [x for x in tos if x in UpComs[cats]] 
# get rid of empty items    
connectors_dict = {k:v for k,v in connectors_dict.items() if v}
################################################################################


# Dictionaries were saved when testing, due to long creation times

#np.save('%s/UpComs.npy' % dict_store, UpComs)       
#UpComs = np.load('%s/UpComs.npy' % dict_store).item()
#np.save('%s/connectors_dict.npy' % dict_store, connectors_dict)
#connectors_dict = np.load('%s/connectors_dict.npy' % dict_store).item()

################################################################################


# create watersheds by selecting catchments in each VPU
vpu_com = dict()
for coms in nrsa_sites['CAT_COMID']:
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
        if len(UpComs[com]) > 0:
            if len(UpComs[com]) == 1:
                feat = str(UpComs[com]).replace('[','(').replace(']',')')
                catQuery = '"FEATUREID" IN %s' % feat 
            if len(UpComs[com]) > 1:
                catQuery = '"FEATUREID" IN ' + str(tuple(UpComs[com]))    
            catchments = arcpy.MakeFeatureLayer_management(
                '%s/NHDPlus%s/NHDPlus%s/%s' % (NHD_dir, hr, vpu, cat),
                'catchments', catQuery)
            sites = nrsa_sites.loc[nrsa_sites['CAT_COMID']==com,'SITE_ID'].values
            for site in sites:
                sitef = site.replace('-','_').lower()
                if not arcpy.Exists('%s/%s.shp' % (out, sitef)):
                    localcat = arcpy.MakeFeatureLayer_management(
                    '%s/ws%s.shp' % (splits, sitef))
                    arcpy.Append_management(catchments, localcat)
                    if com in connectors_dict.keys():
                        for upCom in connectors_dict[com]:
                            upPoly = arcpy.MakeFeatureLayer_management(
                            '%s/%s.shp' % (upStream_dir, upCom))
                            arcpy.Append_management(upPoly, localcat)
                    arcpy.Dissolve_management(localcat,
                                              '%s/%s.shp' % (out, sitef))
                    arcpy.Delete_management(localcat)
            arcpy.Delete_management(catchments)
        if len(UpComs[com]) == 0:
            sites = nrsa_sites.loc[nrsa_sites['CAT_COMID']==com,'SITE_ID'].values
            for site in sites:
                site = site.replace('-','_').lower()
                if not arcpy.Exists('%s/%s.shp' % (out, site)):
                    arcpy.Copy_management('%s/ws%s.shp' % (splits, site), 
                    '%s/%s.shp' % (out, site))                
###############################################################################################
# Below is the sandbox we were trying to make watersheds using geopandas                 
#for vpu in vpu_com.keys():
#    hr = sites_vpu.loc[sites_vpu['UnitID'] == vpu,'DrainageID'].values[0]
#    catchments = gpd.GeoDataFrame.from_file(NHD_dir + '/NHDPlus' + hr +  '/NHDPlus' + vpu + '/NHDPlusCatchment/Catchment.shp')
#    for com in vpu_com[vpu]:
#        upcats = catchments[catchments['FEATUREID'].isin(UpComs[com])]
#        upcats = upcats.drop(upcats.columns[[0,2,3]], axis=1)
#        upcats = upcats.rename(columns=({ 'FEATUREID' : 'COMID'}))
#        sites =  nrsa_sites.loc[nrsa_sites['CAT_COMID']==com, 'SITE_ID'].values
#        for site in sites:
#            sitef = site.replace('-','_').lower()            
#            localcat = gpd.GeoDataFrame.from_file('%s/ws%s.shp' % (splits, sitef))
#            # make same projection
#            upcats = upcats.to_crs(localcat.crs)
#            localcat['SITE_ID'] = site
#            upcats['SITE_ID'] = site
#            
#            if com in connectors_dict.keys():
#                print 'adding inter-VPU catchment for ' + str(com)
#                for upVPU in connectors_dict[com]:
#                    upVPUcat = gpd.GeoDataFrame.from_file('L:/Priv/CORFiles/Geospatial_Library/Data/Project/SSWR1.1B/InterVPUtable/' + upVPU + '.shp')
#
#            # append upstream catchments to adjusted local cat
#            watershed = gpd.GeoDataFrame(localcat.append(upcats))
#            # dissolve
#            watershed2 = watershed.groupby('SITE_ID')
#            watershed.set_index('SITE_ID', inplace=True)
#            watershed['geometry'] = watershed2.geometry.apply(shapely.ops.unary_union)
#            watershed.reset_index(inplace=True)
#            watershed=watershed.drop_duplicates('SITE_ID')
#            watershed.crs = upcats.crs
#            # Check if we need to add upstream VPU connection
#                
#            watershed.to_file('D:/Projects/NRSA1314_Watersheds/' + site + '.shp', driver = 'ESRI Shapefile')    
#                
            # delete null geometry
###############################################################################################
# Below is scrap code for creating and testing either of the methods arcpy OR geopandas
#def combineBorders(*geoms):
#    return shapely.ops.unary_union([geom if geom.is_valid else geom.buffer(0) for geom in geoms])
#    
#polyC = combineBorders(watershed2.geometry)
###############################################################################################
#
#localcat = arcpy.MakeFeatureLayer_management('%s/temp/wsazr9_0901.shp' % splits)
#
#arcpy.CopyFeatures_management(localcat, '%s/temp/upCat.shp' % splits)    
#
#if arcpy.Exists('%s/temp/wsazr9_0901.shp' % splits):
#    arcpy.Delete_management('%s/temp/wsazr9_0901.shp' % splits)
#
#com = 20736507     
#arcpy.Append_management(catchments, localcat)
#[field.name for field in arcpy.ListFields(old)]
#fields = arcpy.ListFields(localcat)
#for field in fields:
#    print("{0} is a type of {1} with a length of {2}"
#          .format(field.name, field.type, field.length))
#          
#          
#here = 'L:/Priv/CORFiles/Geospatial_Library/Data/Project/SSWR1.1B/InterVPUtable'          
#for f in os.listdir(here):
#    if '.shp' in f and not '.xml' in f:
#        
#        old = arcpy.MakeFeatureLayer_management('{}/{}'.format(here, f))
#
#        arcpy.AddField_management(old, "FEATUREID", "LONG")
#        arcpy.CalculateField_management(old, "FEATUREID", "!Id!", expression_type="PYTHON")
#        arcpy.AddField_management(old, "GRIDCODE", "LONG")
#        arcpy.AddField_management(old, "SOURCEFC", "TEXT", 20)
#        #arcpy.CalculateField_management(outshape, "SOURCEFC", 'NHDFlowline')
#        arcpy.AddField_management(old, "AreaSqKM", "DOUBLE", 19)
#        arcpy.DeleteField_management(old, "Id")
        
        
# testing below
###############################################       
#vpu_com = dict()
#for cat_com in nrsa_sites ['CAT_COMID']:
#    if cat_com > 0:
#        vpu = zone[np.where(coms == cat_com)][:,1][0]
#        if not vpu_com.has_key(vpu):
#            vpu_com[vpu] = []
#        if not cat_com in vpu_com[vpu]:
#            vpu_com[vpu].append(cat_com)
#    else:
#        pass
#
#
#
#for keys in Full_COMs.keys():
#    if not keys <= 0:
#        print 'working on ' + str(keys)
#        COM_length = len(Full_COMs[keys])
#        COMlist = str(Full_COMs[keys]).strip('[]')
#        COMlist = COMlist.replace("u",'')
#        COMlist = str(literal_eval(COMlist))
#        #build the query string to pass to Arc..
#        if COM_length == 1:
#            string = '"FEATUREID"  IN ' +  '(' + "%s"%COMlist + ')'
#        elif COM_length > 1:
#            string = '"FEATUREID"  IN ' +  "%s"%COMlist   
#        arcpy.MakeFeatureLayer_management(mergedcats, 'MergedCats', string)
#
## unary union with geopandas
#df2=df.groupby('continent')
#df.set_index('continent', inplace=True)
#df['geometry']=df2.geometry.apply(shapely.ops.unary_union)
#df.reset_index(inplace=True)
#df=df.drop_duplicates('continent')
#       
## unary union idea from here: http://gis.stackexchange.com/questions/149959/dissolve-polygons-based-on-attributes-with-python-shapely-fiona
#from shapely.geometry import shape, mapping
#from shapely.ops import unary_union
#import fiona
#import itertools
#with fiona.open('cb_2013_us_county_20m.shp') as input:
#    # preserve the schema of the original shapefile, including the crs
#    meta = input.meta
#    with fiona.open('dissolve.shp', 'w', **meta) as output:
#        # groupby clusters consecutive elements of an iterable which have the same key so you must first sort the features by the 'STATEFP' field
#        e = sorted(input, key=lambda k: k['properties']['STATEFP'])
#        # group by the 'STATEFP' field 
#        for key, group in itertools.groupby(e, key=lambda x:x['properties']['STATEFP']):
#            properties, geom = zip(*[(feature['properties'],shape(feature['geometry'])) for feature in group])
#            # write the feature, computing the unary_union of the elements in the group with the properties of the first element in the group
#            output.write({'geometry': mapping(unary_union(geom)), 'properties': properties[0]})
#
#    
    

