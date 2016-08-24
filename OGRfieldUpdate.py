# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from osgeo import ogr

here = 'C:/Users/Rdebbout/Desktop/polygonize'
# Open a Shapefile, and get field names
source = ogr.Open('%s/ALLS-1037.shp' % here, update=True)
layer = source.GetLayer()
layer_defn = layer.GetLayerDefn()
field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
print len(field_names), 'UID' in field_names

# Add a new field
new_field = ogr.FieldDefn('CAT_COMID', ogr.OFTInteger)
layer.CreateField(new_field)
new_field2 = ogr.FieldDefn('SITE_ID', ogr.OFTString)
new_field2.SetWidth(16)
layer.CreateField(new_field2)
shp = source.GetLayer()

for feature in shp:
    feature.SetField('CAT_COMID', 474747)
    feature.SetField('SITE_ID', 'ALLS-1037') 
    shp.SetFeature(feature)

# Close the Shapefile
source = None
