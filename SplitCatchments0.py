# Name: SplitCatchment_01-watersheds.py
# Description: Split catchment (via "watershed calculation") based on sites
# Author: tad larsen
# Date: 12/2013

import os, sys, fileinput, string, shutil, arcpy
from datetime import datetime
from arcpy.sa import Watershed, SnapPourPoint, Times, Con, Divide, EucDistance
arcpy.env.overwriteOutput = True
from Tkinter import *
from tkFileDialog import askopenfilename
from tkFileDialog import askdirectory
import tkMessageBox
Tk().withdraw()

# Data requirements:
# - Site(s) [csv or shapefile]
# - NationalWBDSnapshot [NHDPlus2 - vector]
# - Catchment shapefile [NHDPlus2 - vector]
# - featureidgridcode.dbf [NHDPlus2 - table]
# - Flow direction [NHDPlus2 - raster]
# - Flow accumulation [NHDPlus2 - raster]

# General Process:
# - Find COMID from Catchments.shp/site intersection
# - Select catchment
# - Export selected
# - Export by mask (fdr)
# - Export by mask (fac)
# - Find largest accumulation cell in area [100m]
# - Snap point to largest accumulation cell
# - Create watershed
# - Get count and calculate area

#####################################################################################################################
# variables
siteIdField = "SITE_ID"
nhdDictionary = {'01':'NHDPlusNE','02':'NHDPlusMA','03N':'NHDPlusSA','03S':'NHDPlusSA','03W':'NHDPlusSA','04':'NHDPlusGL','05':'NHDPlusMS','06':'NHDPlusMS','07':'NHDPlusMS','08':'NHDPlusMS','09':'NHDPlusSR','10L':'NHDPlusMS','10U':'NHDPlusMS','11':'NHDPlusMS','12':'NHDPlusTX','13':'NHDPlusRG','14':'NHDPlusCO','15':'NHDPlusCO','16':'NHDPlusGB','17':'NHDPlusPN','18':'NHDPlusCA'}
nhdRootDir = "F:\\NHDv21" #"L:/Priv/CORFiles/Geospatial_Library/Data/RESOURCE/PHYSICAL/HYDROLOGY/NHDPlusV21"
global workspaceDir
workspaceDir = "F:\\NRSA13-14 Watersheds\\QA"
boundaryUnit = nhdRootDir + "/NHDPlusGlobalData/BoundaryUnit.shp"
outRef = "GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision"
rasterRef = "PROJCS['NAD_1983_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-96.0],PARAMETER['Standard_Parallel_1',29.5],PARAMETER['Standard_Parallel_2',45.5],PARAMETER['Latitude_Of_Origin',23.0],UNIT['Meter',1.0]]"

#####################################################################################################################
fieldValues = {}
# functions
def getLatField(filename):
    sampSite = open(filename, 'r')
    row = sampSite.readline()
    row = row.rstrip('\n')
    rowCells = row.split(",")

    global tkLat
    tkLat = Tk()
    label = Label(tkLat, text="Latitude Field:")
    label.pack()
    scrollbar = Scrollbar(tkLat)
    scrollbar.pack(side=RIGHT, fill=Y)
    global fieldBoxLat
    fieldBoxLat = Listbox(tkLat)
    fieldBoxLat.pack()
    for field in rowCells:
        fieldBoxLat.insert(END, field)

    fieldBoxLat.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=fieldBoxLat.yview)

    btnOK = Button(tkLat, text="OK", command=callbackLat)
    btnOK.pack()
    
    tkLat.mainloop()
    
def callbackLat():
    selection = fieldBoxLat.get(fieldBoxLat.curselection())
    fieldValues['latitude'] = selection
    tkLat.quit()
    tkLat.destroy()

def getLongField(filename):
    sampSite = open(filename, 'r')
    row = sampSite.readline()
    row = row.rstrip('\n')
    rowCells = row.split(",")

    global tkLong
    tkLong = Tk()
    label = Label(tkLong, text="Longitude Field:")
    label.pack()
    scrollbar = Scrollbar(tkLong)
    scrollbar.pack(side=RIGHT, fill=Y)
    global fieldBoxLong
    fieldBoxLong = Listbox(tkLong)
    fieldBoxLong.pack()
    for field in rowCells:
        fieldBoxLong.insert(END, field)

    fieldBoxLong.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=fieldBoxLong.yview)

    btnOK = Button(tkLong, text="OK", command=callbackLong)
    btnOK.pack()
    
    tkLat.mainloop()
    
def callbackLong():
    selection = fieldBoxLong.get(fieldBoxLong.curselection())
    fieldValues['longitude'] = selection
    tkLong.quit()
    tkLong.destroy()

#####################################################################################################################

# main script

arcpy.env.workspace = workspaceDir
arcpy.CheckOutExtension("Spatial")

# Keep track of sites (with associated catchment hydroregion and ComID) and metrics
# to loop through later getting upstream info

# keep running tally of siteID as key with list of hydroreg and comid as value
siteDict = {}
siteOutPath = workspaceDir + "\\sitesNHDPlus.csv"
siteOutFile = open(siteOutPath, 'w')
siteOutFile.write("NRSA_ID,HYDROREG,RPU,FEATUREID \n")

# get site file
siteFile = askopenfilename(title='Select site file',filetypes=[('Comma delimited file','.csv'),('Shapefile','.shp')],initialdir=workspaceDir)

# if it's a csv file, need to convert it to shapefile
if (siteFile[-3:] == 'csv'):
    # get lat/long field names
    lat = getLatField(siteFile)
    lon = getLongField(siteFile)
    
    # make point layerrasterRef
    outLayer = "xyEvents.shp"
    outShape = "xyLayer.shp"
    arcpy.MakeXYEventLayer_management(siteFile,fieldValues['longitude'],fieldValues['latitude'],outLayer,outRef)
    if os.path.exists(workspaceDir + "\\" + outShape):
        print "Overwriting previous coordinate shapefile"
        arcpy.Delete_management(outShape)
    arcpy.FeatureClassToFeatureClass_conversion(outLayer, workspaceDir, outShape)
    siteShape = workspaceDir + "\\" + outShape
else:
    siteShape = siteFile

arcpy.MakeFeatureLayer_management(boundaryUnit,'boundaryLayer')
shapeField = arcpy.Describe(siteShape).ShapeFieldName
cursor = arcpy.SearchCursor(siteShape)
for row in cursor:
    try:
        startTime = datetime.now()
        # Make new directory
        siteID = row.getValue(siteIdField)
        print str(siteID)
        newDirectory = workspaceDir + "\\ws" + str(siteID)
        if os.path.exists(newDirectory):
            if not os.path.exists(newDirectory + "\\wshed"):
                print "Did not find watershed grid in " + newDirectory + " - removing directory and trying again"
                shutil.rmtree(newDirectory)
    
        if not os.path.exists(newDirectory):
            os.makedirs(newDirectory)
            arcpy.env.scratchWorkspace = newDirectory
            #reselect site point and copy into Albers projection
            pointQuery = '"' + siteIdField + '" = ' + "'" + str(siteID) + "'"
            arcpy.MakeFeatureLayer_management(siteShape,'pointLayer',pointQuery)
            arcpy.Describe('pointLayer').FIDset
            if not arcpy.Exists(newDirectory + "\\pointShape.shp"):
                arcpy.Project_management('pointLayer',newDirectory + "\\pointShape.shp",rasterRef)
    
            # Identify hydroregion and rpu
            arcpy.SelectLayerByLocation_management('boundaryLayer','intersect','pointLayer')
            boundaryRows = arcpy.SearchCursor('boundaryLayer')
            boundaryRow = boundaryRows.next()
            while boundaryRow:
                if boundaryRow.UnitType == 'VPU':
                    hydroreg = boundaryRow.UnitID
                if boundaryRow.UnitType == 'RPU':
                    rpu = boundaryRow.UnitID
                boundaryRow = boundaryRows.next()
            
            # Create catchment layer from unique hydroreg
            nhdHregDir = nhdRootDir + "\\" + nhdDictionary[hydroreg] + "\\NHDPlus" + hydroreg
            arcpy.MakeFeatureLayer_management(nhdHregDir + "\\NHDPlusCatchment\\Catchment.shp",'catchLayer')
          
            # Export catchment for masking
            arcpy.SelectLayerByLocation_management('catchLayer','intersect','pointLayer')            
            newCatch = newDirectory + "\\catchment.shp"
            arcpy.CopyFeatures_management('catchLayer',newCatch)
            featID = arcpy.SearchCursor('catchLayer').next().getValue("FEATUREID")
            arcpy.Delete_management('pointLayer')
            
            # Update the siteDict
            siteDict[siteID] = [hydroreg,rpu,featID]
    
            # Use subregion id to get/export masks for flow direction and accumulation
            #gdbDirectory = '\\\\Aa.ad.epa.gov\\ord\\COR\\Users\\M-Z\\Rdebbout\\Net MyDocuments\\ArcGIS\\Default.gdb'
            rasterPath = nhdHregDir + "\\NHDPlusFdrFac" + rpu
            arcpy.Clip_management("%s\\fdr" % rasterPath, "#", "%s\\fdr" % newDirectory, newCatch, "", "ClippingGeometry")
            arcpy.Clip_management("%s\\fac" % rasterPath, "#", "%s\\fac" % newDirectory, newCatch, "", "ClippingGeometry")
            
            #set environment variables            
            arcpy.env.snapRaster = "%s\\fdr" % newDirectory            
            arcpy.env.extent = "%s\\fac" % newDirectory
    
            # Snap pour point - alternative method that does not push valid points downstream
            arcpy.PointToRaster_conversion(newDirectory + "\\pointShape.shp",siteIdField, newDirectory + "\\point","","",30)
            outDist = EucDistance(newDirectory + "\\point", 300, 30) 
            outDivide = Divide(1, outDist)  # arcpy.MosaicToNewRaster_management(["outDivide","pointRasOrig"],
            both = arcpy.MosaicToNewRaster_management([outDivide,newDirectory + "\\point"],newDirectory,"tagetha","","32_BIT_FLOAT","30",1)
            outCon = Con(newDirectory + "\\fac",1, "",'"VALUE" > 100')
            outTimes = Times(both, outCon)
            outTimes.save(newDirectory + "\\times")
            outSnap = SnapPourPoint(newDirectory + "\\point",newDirectory + "\\times",200)
            outSnap.save(newDirectory + "\\snappnt")
            arcpy.ClearEnvironment("extent")
    
            # Create watershed and calculate area
            outWatershed = Watershed(newDirectory + "\\fdr",outSnap)
            outWatershed.save(newDirectory + "\\wshed")
            
            print ' - ' + str((datetime.now()-startTime))
        else:
            print newDirectory + " exists - moving on..."
    except:
        print siteID + ": problem processing - moving on..."
for key, value in siteDict.items():
    siteOutFile.write(key + ',' + str(value[0]) + ',' + str(value[1]) + ',' + str(value[2]) + '\n')

siteOutFile.close()

