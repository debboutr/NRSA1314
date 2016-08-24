# NRSA1314
*Scripts used to do zonal statistics and append split-catchments to accumulated StreamCat data*

The .tab file we began with uses 'SITE_ID' as a unique ID for all points. Before processing, we need to create a 'UID' as integer and spatially join with VPUs and catchment FEATUREID for the accumulation with StreamCat data

The order of running these scripts is as follows:
* SplitCatchments0.py  -- this should be done once 'Uninitialized' flowlines are removed from the table of points, processed w/ StreamCat alone
* makeImages.py -- prepare images for quickly QAing the split-catchments that are created
* splitCat_ZStats_SITES.py -- use the NRSA control table to process each of the landscape layers for each split-cat
* getUninitialized.py -- take the sites that were identified as 'Uninitialized' and collect StreamCat Data for each
* stackLaterally.py -- combine tables made from both splitCats and Uninitialized
* NRSA13-14Watersheds.py -- make dissolved watersheds from splitCats
* makeUninitializedWatersheds.py -- make dissolved watersheds from uninitialized
