
'''

Purpose: The purpose is to output a updated VRI

Date: January 18, 2012

Created by: Graham MacGregor Thompson Okanagan Region (FLNRO)
            with Revisions by Sasha Lees

Arguments: ([Area of interest feature class],[Data connection to LRDW],[Output Directory],[Filegeodatabase name in that directory],[Field with list of AOI to extract out VRI and update it])
             
Outputs: 1.Output and updated VRI layer that uses RESULTS and FTEN to capture additional forest activities.
        2. Also required in Arccatalog r"Database Connections\\LRDW.sde
        3. Will generate a new file geodatabase if it does not exist based on the name input
        3. Add two fields to output
                Projage_r which is a modified age if any RESULTS blocks affect the age.
                Seral_source which is the source for each age.
 Some data is maintained from the RESULTS coverage's if the user wants to use the attributes
  Attributes maintained
  RESULTS Openings
  (Opening_idopen,Map_label,opening_category_code,denudation_1_disturbance_code,denudation_1_silv_system_code,denudation_2_disturbance_code,denudation_2_silv_system_code)
  RESULTS FC
  (Opening_IDFC,Stocking_status_code,silv_reserve_code,I_species_code_1,I_species_percent_1,I_species_age_1,I_species_height_1)
  FTEN
  (Cut_block_id)
  
  TSA Results can be combined together manually using MERGE.
  
Dependencies: LRDW (VRI Rank 1 poly and RESULTS Openings and Forest cover, FTEN licencee logging complete blocks.
                -Extracts data from LRDW VRI

Approx Run Time:  2-5 hrs / TSA (depending on TSA size)

History: Modified from some original programming created by Mark McGirr and Will Burt
Feb 2012- Added polygon counter for LRDW extractions to test selection to actual output.

May 2013 - Reviewed process and created version 3 of programming
- Added overlap module checker

13-June-2014  salees
    Added criteria for Estimated age and height calcs. Refined attribute calculations. Refined Disturbance Date calculations.

2023 04 14
    Script was updated from python 2 to python 3, preformed by C.Folkers, updated some rater calculations

-----------------------------------------------------------------------------------------------
'''

import sys, os, os.path, sys, arcpy, time, datetime, math

import overlapmod_py3  # Must be in same directory as script


class VRI2:
    def __init__(self, wtrshdname, Bfold):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold

        #user Variables
        WatershedName=self.wtrshdname
        BaseFolder=self.Bfold

        #
        namedwatershed=WatershedName.replace(' ','_')
        inputgdb=namedwatershed+'_Input_Data.gdb'
        vrifolder=os.path.join(BaseFolder,r'1_SpatialData\3_VRI_Update')
        sOutputLoc = os.path.join(vrifolder,r"data")
        sAOI_GDB = os.path.join(vrifolder,r"Python_Geodatabase.gdb")
        input_data=os.path.join(BaseFolder,r'1_SpatialData\1_InputData')
        print(sAOI_GDB)

        #could change to list feature class with wildcard
        VRI = os.path.join( sAOI_GDB, r"VEG_R1_PLY")
        rslt_openings = os.path.join( sAOI_GDB, r"RSLT_OPENING_SVW")
        rslt_fc = os.path.join( sAOI_GDB,r"RSLT_FOREST_COVER_INV_SVW")
        ften_cutblocks = os.path.join( sAOI_GDB, r"FTEN_CUT_BLOCK_POLY_SVW")
        rslt_open_vw = os.path.join( sAOI_GDB,r"RSLT_OPENING_VW")  # Table w flattened view of ATUs most current activity only
        GBDTemp = os.path.join(vrifolder,'tempvri.gdb') 
        startTime = time.time()
        START_TIME = time.ctime(time.time())
        print ('   Starting : '), START_TIME

        arcpy.env.overwriteOutput = True
        arcpy.QualifiedFieldNames = "UNQUALIFIED"

        today = str(datetime.date.today())
        # dateVar = today.replace("-","")
        dateVar = time.strftime("%Y%m%d")  # Date in the format of year, month, day  eg. 20131121
        stimePeriod = str(datetime.date.today().year) # This year is used as the baseline date to calculate estimated ages etc.

        print (dateVar)

        # the location of the boundary for which VRI data will be extracted. This can be tiled or a single tile. Each tile must be uniquely namedTKA_bnd_split
        # sAOI_GDB = r"T:\Python_Geodatabase.gdb"

        # SET AOI
        verAOI = 'AOI'
        sAOIfeat = os.path.join(sAOI_GDB, verAOI)
        print( sAOIfeat)
        # sets the database connection variable to the datawarehouse
        # sDATAconnect = r"Database Connections\BCGW.sde"  #LRDW data connection
        # sDATAconnect = r'Database Connections\BCGW4Scripting.sde'  #Connection with built in password - you must have created this connection (eg. in ArcCatalog)
        # the output location folder where the VRI data will extracted and stored
        # sOutputLoc = r"T:\data"
        # the name of the output file geodatabase
        # sOutputFGDB = r"VRI2_TLI_BUF_2014_V4_20140428_101" #VRITKA_BUF_APR_2014   smaller_testAPR2014_4
        sOutputFGDB = 'VRI2_' + verAOI + '_' + stimePeriod
        # the field delineating the tiling of extracted can be one or multiple tiles.
        sField = r"WATERSHED_KEY"  # TSA_CODE_Exp   DATA_SOURCE_CODE
        # The variable on whether all tile data will be merged or kept in seperate tile units.
        # sCreateMerge = r'1'

        '''.
        #the location of the boundary for which VRI data will be extracted. This can be tiled or a single tile. Each tile must be uniquely named
        sAOIfeat = r"oj\CumulativeEffects\dataInputs\Base\THOK_Boundaries.gdb\TME_bnd_buf"
        #sets the database connection variable to the datawarehouse
        sDATAconnect = r"Database Connections\\BCGW.sde"  #LRDW data connection
        #the output location folder where the VRI data will extracted and stored
        sOutputLoc = r"\ksc_proj\CumulativeEffects\dataInputs\VRI_FC\2013"
        #the name of the output file geodatabase
        sOutputFGDB = r"VRIESNOV2018"
        #the field delineating the tiling of extracted can be one or multiple tiles.
        sField = r"TSA_CODE_EXP"
        #The variable on whether all tile data will be merged or kept in seperate tile units.
        sCreateMerge = r'1'
        '''

        # create area of interest variable
        # Input variables
        '''
        sAOIfeat= sys.argv[1] #Input Area of Interest. Provide full directory root.
        sDATAconnect = sys.argv[2]  #LRDW data connection
        sOutputLoc = sys.argv[3]  #Output directory location
        sOutputFGDB = sys.argv[4]  #uniquename of sample field
        sField = sys.argv[5]  #uniquename of sample field
        sCreateMerge = sys.argv[6] #asks if all the VRI files need to be merged together.
        '''

        # Make output location
        sExtractLoc = os.path.join(sOutputLoc, sOutputFGDB) + ".gdb"

        # Script Datasources - directed to local extraction to take shorter amount of time
        # Alternatively can use bcgw connection
        # lrdw_rslt_tu = sDATAconnect + "\WHSE_FOREST_VEGETATION.RSLT_ACTIVITY_TREATMENT_SVW"
        # VRI = r"T:\Python_Geodatabase.gdb\VEG_R1_PLY"
        # rslt_openings = r"T:\Python_Geodatabase.gdb\RSLT_OPENING_SVW"
        # rslt_fc = r"T:\Python_Geodatabase.gdb\RSLT_FOREST_COVER_INV_SVW"
        # ften_cutblocks = r"T:\Python_Geodatabase.gdb\FTEN_CUT_BLOCK_POLY_SVW"
        # rslt_open_vw = r"T:\Python_Geodatabase.gdb\RSLT_OPENING_VW"  # Table w flattened view of ATUs most current activity only

        # create list
        aoiList = []


        # Creates field list of AOI's that need to be extracted for the analysis


        # checks selected records to output records. Sometimes ESRI exporters or the BCGW do not export out all features.
        def polygoncounter(selectedFeat, outputFeat):
            resultselfeat = arcpy.GetCount_management(selectedFeat)
            countselfeat = int(resultselfeat.getOutput(0))
            resultoutfeat = arcpy.GetCount_management(selectedFeat)
            countoutfeat = int(resultoutfeat.getOutput(0))
            if countselfeat == countoutfeat:
                print ("input and outputfeatures are equal no need to worry")
            if countselfeat != countoutfeat:
                print( "Warning inputfeatures does not equal output features")
                valid_inputs = ('Y', 'N')
                while True:
                    choice = input("Do you wish to continue the program Y or N")
                    if choice == 'Y':
                        return True
                    if choice == 'N':
                        sys.exit
                        return True
                    else:
                        print ('invalid choice try again Y or N capitalized')


        # extracts features out based on an area of interest.
        def extract_by_area(inFeatureClass, AOI, outFeatureClass):
            # Extract by area - Clips inFeatureCLass to AOI and writes output to outFeatureClass
            tempGDB = GBDTemp
            # Clean up if existing
            if arcpy.Exists("featLyr"):
                arcpy.Delete_management("featLyr")
            # Create Feature Layer
            if arcpy.Exists(inFeatureClass):
                arcpy.MakeFeatureLayer_management(inFeatureClass, "featLyr")
            else:
                sys.exit("Feature Class Does not exist: " + inFeatureClass)
            # prepare temp geodatabase if it does not exist
            if arcpy.Exists(tempGDB):
                tempGDB = tempGDB[0:-4] + "_1" + ".gdb"
            # arcpy.CreateFileGDB_management(os.path.split(tempGDB)[0], os.path.split(tempGDB)[1])
            # Manually create tempvri.gdb
            arcpy.env.workspace = tempGDB
            print ("Select by location for..")
            arcpy.SelectLayerByLocation_management("featLyr", 'INTERSECT', AOI)
            # get count of number selected
            print ("\t done")
            arcpy.CopyFeatures_management("featLyr", "inFeatureIntersect")
            # checks that selected features output to a feature are equal.
            polygoncounter("featLyr", "inFeatureIntersect")
            # clips data to temp file geodatabase
            arcpy.Clip_analysis("inFeatureIntersect", AOI, outFeatureClass)
            arcpy.Delete_management(tempGDB)


        # end extract by area


        def create_dict_from_fields(inFeatureClass, inField, keyField, SQLWhere):
            theDict = {}
            with arcpy.da.SearchCursor(inFeatureClass, (inField, keyField), SQLWhere) as cursor:
                for row in cursor:
                    inFieldRow = row[0]
                    keyFieldRow = row[1]
                    if inFieldRow not in theDict:
                        theDict[inFieldRow] = keyFieldRow
            return theDict


        def Populate_table_withdictionary(inTable, fieldtopopulate, keyfield, inDictionary, Checkfield=None):
            cursor = arcpy.UpdateCursor(inTable)
            for row in cursor:
                keyvalue = row.getValue(keyfield)
                if keyvalue != None:
                    if keyvalue in inDictionary:
                        if Checkfield == None:
                            row.setValue(fieldtopopulate, inDictionary[keyvalue])
                        if Checkfield != None:
                            keyvalue = row.getValue(Checkfield)
                            if Checkfield is None:
                                row.setValue(fieldtopopulate, inDictionary[keyvalue])
                        cursor.updateRow(row)


        def Delete_row_withdictionary(inTable, keyfield, inDictionary):
            cursor = arcpy.UpdateCursor(inTable)
            for row in cursor:
                keyvalue = row.getValue(keyfield)
                if keyvalue != None:
                    if keyvalue in inDictionary:
                        cursor.deleteRow(row)

        def cleanup(inputfolder,outputfolder):
            print('CLEAN UP')
            # os.remove(os.path.join(vrifolder,'temp_data.gdb'))
            # os.remove(sAOI_GDB)

            # arcpy.env.workspace=outputfolder
            # VRI2FC=arcpy.ListFeatureClasses('VRI2*')
            # print (VRI2FC)
            # for fc in VRI2FC:
            #     print(fc)
            #     outputpath=os.path.join(input_data,fc)
            #     arcpy.CopyFeatures_management(fc,outputpath)
            #     print('FC copied to iunput gdb')
            print(inputfolder)
            print(outputfolder)
            arcpy.Copy_management(inputfolder,outputfolder)
            print('final gdb copied')

            #after copied delete entire folder... eventaully on T drive 

        # ------------------------------------------------------------------------------
        # Main
        print ("Checking to see if File Geodatabase " + sOutputFGDB + " exists")
        if not arcpy.Exists(sExtractLoc):
            print ("File geodatabase does not exist")
            arcpy.CreateFileGDB_management(sOutputLoc, sOutputFGDB)
            arcpy.env.workspace = sExtractLoc
            # debuging
        else:
            print ("File geodatabase exists. Not recreating")
            arcpy.env.workspace = sExtractLoc

        # AOI Units.
        print ('Listing AOI units')
        rows = arcpy.SearchCursor(sAOIfeat)
        row = rows.next()
        while row:
            aoiList.append(row.getValue(sField))
            row = rows.next()
        del row, rows

        print ("This many VRI areas will be extracted " + str(len(aoiList)))
        for aoiNumber in aoiList:
            print(aoiNumber)
            # extracts out Area of interest tile
            if aoiNumber == None:
                aoiNumber==1
            varSQL = str(aoiNumber)
            varName = f"a_{str(aoiNumber)}"
            # selText = f"{sField} = {varSQL}"
            print(sAOIfeat)
            # print(selText)
            arcpy.MakeFeatureLayer_management(sAOIfeat, "LuLyr") #selText
            print(f"{varName}_bnd")
            aoiBnd = arcpy.CopyFeatures_management("LuLyr", f"{varName}_bnd")
            arcpy.MakeFeatureLayer_management(f"{varName}_bnd", "luAOI")
            arcpy.Delete_management("LuLyr")

            # dictionary to create outputs of fourmain files to create VRI output
            covDict = {VRI: 'VRI', rslt_fc: 'RSLTFC', rslt_openings: 'RSLTOPEN',
                    ften_cutblocks: 'FTENBLKS'}  # , lrdw_rslt_tu : 'RSLTACT'}
            # covDict = {VRI : 'VRI'}  #, lrdw_rslt_tu : 'RSLTACT'}
            fcList = []
            delList = []

            for cov in covDict:
                DfcName = covDict[cov]
                print ('\nNow processing ', DfcName)
                extractfcName = sExtractLoc + "\\" + varName + '_' + DfcName + '_orig'
                wrkfcName = sExtractLoc + "\\" + varName + '_' + DfcName + '_wrk'
                if not arcpy.Exists(extractfcName):
                    print( 'Extracting BCGW data...')
                    extract_by_area(cov, "luAOI", extractfcName)
                # take the extract name and run the overlap checker on it.
                # Make a copy of the original because the originals will have features Deleted
                arcpy.env.workspace = sExtractLoc
                if not arcpy.Exists(wrkfcName):
                    # Rename or Copy VRI Orig to VRI work  for consistency.  Others will be renamed below
                    # arcpy.Rename_management(varName +'_VRI_orig',varName +'_VRI_wrk')
                    if DfcName == 'VRI':
                        arcpy.CopyFeatures_management(varName + '_VRI_orig', varName + '_VRI_wrk')
                    if DfcName in ['FTENBLKS', 'RSLTOPEN', 'RSLTFC']:
                        # arcpy.CopyFeatures_management(extractfcName,origfcName)

                        # Remove Self Overlaps
                        print( 'Removing Self Overlaps')
                        deleteFields = '1'  # 1 means overlap tracking fields will be removed in final copy, blank is not removed (or leave out)
                        # Set date sort field
                        if DfcName == 'FTENBLKS':
                            sortVariable = r"BLOCK_STATUS_DATE D"
                        if DfcName == 'RSLTOPEN':
                            sortVariable = r"OPENING_WHEN_UPDATED D"
                        if DfcName == 'RSLTFC':
                            sortVariable = r"FOREST_COVER_WHEN_UPDATED D"
                        obj = overlapmod_py3.featureClass(extractfcName,BaseFolder)
                        obj.findoverlap(sAOIfeat, DfcName, sortVariable, deleteFields)
                        # rename output from 'fixed' to 'wrk'
                        arcpy.Rename_management(DfcName + "fixed", wrkfcName)

                print ('The following file has been extracted ' + wrkfcName)
                fcList.append(wrkfcName)
                delList.append(wrkfcName)

                # TEMP DropFields in VRI wrk
                # if DfcName == 'VRI':
                #   dropList = ['VRI2_SOURCE','VRI2_OPENING_ID','VRI2_ATT_SOURCE_DISTURB','VRI2_ATT_SOURCE_SPECIES','VRI2_DISTURB_CODE','VRI2_DISTURB_DATE','VRI2_DISTURB_YR',\
                #      'VRI2_HARVESTED','VRI2_SITE_INDEX','VRI2_SPECIES','VRI2_SPECIES_PERCENT','VRI2_AGE','VRI2_HEIGHT',\
                #     'VRI2_SI_ESTIMATED','VRI2_SPECIES_ESTIMATED','VRI2_AGE_ESTIMATED','VRI2_HEIGHT_ESTIMATED']
                # for field in dropList:
                #   if arcpy.ListFields(wrkfcName,field):
                #      arcpy.DeleteField_management(wrkfcName, field)

                # Add standard Fields
                # if DfcName <> 'VRI':
                VRI2prefix = 'VRI2'
                if not arcpy.ListFields(wrkfcName, VRI2prefix + "_SOURCE"):
                    print ('Adding Fields...')
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_SOURCE", "TEXT", "", "", '25')  # Spatial polygon source
                    # arcpy.CalculateField_management(wrkfcName,VRI2prefix+"_SOURCE", '"'+DfcName+'"')
                    # Python 64
                    arcpy.CalculateField_management(wrkfcName, VRI2prefix + "_SOURCE", '"' + DfcName + '"', "PYTHON_9.3")
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_ATT_SOURCE_DISTURB", "TEXT", "", "",
                                            '25')  # In some cases the attributes are filled in from OPEN/FC, but the spatial is from VRI
                    # Python 64
                    arcpy.CalculateField_management(wrkfcName, VRI2prefix + "_ATT_SOURCE_DISTURB", '"' + DfcName + '"',
                                                    "PYTHON_9.3")  # Default to same as spatial source - may be over-written later
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_ATT_SOURCE_SPECIES", "TEXT", "", "",
                                            '25')  # In some cases the attributes are filled in from OPEN/FC, but the spatial is from VRI
                    arcpy.CalculateField_management(wrkfcName, VRI2prefix + "_ATT_SOURCE_SPECIES", '"' + DfcName + '"',
                                                    "PYTHON_9.3")  # Default to same as spatial source - may be over-written later
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_OPENING_ID", "LONG")
                    arcpy.CalculateField_management(wrkfcName, VRI2prefix + "_OPENING_ID", "!OPENING_ID!", "PYTHON_9.3", "")
                    # To be calculated Later in Script
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_DISTURB_CODE", "TEXT", "", "", '20')
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_DISTURB_DATE", "DATE")
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_DISTURB_YR", "SHORT")
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_HARVESTED", "TEXT", "", "", '5')
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_SITE_INDEX", "FLOAT")
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_SPECIES", "TEXT", "", "", '10')
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_SPECIES_PERCENT", "SHORT")
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_AGE", "SHORT")
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_HEIGHT", "FLOAT")
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_SI_ESTIMATED", "TEXT", "", "",
                                            '5')  # This will be a flag if the Site Index was taken from Estimated or Previous Site Index attribute
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_SPECIES_ESTIMATED", "TEXT", "", "",
                                            '5')  # This will be a flag if the species info was taken from Estimated or Previous species attribute
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_AGE_ESTIMATED", "TEXT", "", "",
                                            '5')  # This will be a flag if the Age  was estimated
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_HEIGHT_ESTIMATED", "TEXT", "", "",
                                            '5')  # This will be a flag if the Height was estimated
                    arcpy.AddField_management(wrkfcName, VRI2prefix + "_CROWN_CLOSURE",
                                            "SHORT")  # This will be a flag if the Height was estimated

            arcpy.env.workspace = sExtractLoc
            # can check layer selection and output count

            print ("done data extraction")
            # add landscape unit to fcList
            # fcList.append(aoiBnd)
            # mark time
            deltaTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
            print ('data extraction done: ' + deltaTime)

            # Dict variable will be used for Opening ID comparison
            covFTENBLKS = sExtractLoc + "/" + varName + '_' + 'FTENBLKS_wrk'
            covFTENBLKSdict = sExtractLoc + "/" + varName + '_' + 'FTENBLKS_orig'
            covRESULTOPEN = sExtractLoc + "/" + varName + '_' + 'RSLTOPEN_wrk'
            covRESULTOPENdict = sExtractLoc + "/" + varName + '_' + 'RSLTOPEN_orig'
            covRESULTFC = sExtractLoc + "/" + varName + '_' + 'RSLTFC_wrk'
            covRESULTFCdict = sExtractLoc + "/" + varName + '_' + 'RSLTFC_orig'
            covVRI = sExtractLoc + "/" + varName + '_' + 'VRI_wrk'
            covVRIdict = sExtractLoc + "/" + varName + '_' + 'VRI_orig'

            # ---------------------------------------------------------
            # FILTER OUT UNWANTED FEATURES for each input layer and  join fields
            # FTEN
            # only select unsuitable blocks and Delete them
            # remove large areas from ften. Garbage ften areas and woodlot bounds set around 4000000 did not go smaller in fear of losing data
            # Filter out OPENING_ID is null or zero?  These may often be non-forest tenures with associated cutting permits.
            print ('\nLooking for unsuitable cutblocks  from FTEN only using logging complete')
            # SQLstr = '"HARVEST_AUTH_STATUS_CODE" NOT IN (\'HC\',\'HI\',\'HP\',\'HS\',\'LC\',\'PA\',\'PE\',\'PI\',\'S\',\'HB\')'
            # SQLstr = '"BLOCK_STATUS_CODE" NOT IN (\'LC\',\'S\',\'HB\')'  #do i need to add HC?
            SQLstr = "BLOCK_STATUS_CODE NOT IN ('LC','S','HB') or Shape_Area >= 4000000"
            arcpy.MakeFeatureLayer_management(covFTENBLKS, 'CutBlkLyr', SQLstr)
            count = int(arcpy.GetCount_management('CutBlkLyr').getOutput(0))
            # if count > 0:
            if int(arcpy.GetCount_management('CutBlkLyr').getOutput(0)) > 0:
                print ('Deleting unwanted FTENBLKS polygons: ', count)
                arcpy.DeleteFeatures_management('CutBlkLyr')
            arcpy.Delete_management("CutBlkLyr")

            # RESULTS OPENINGS
            # Delete spex areas in RESULTS openings
            print ('\nLooking for RESULTS SPEX and polys with no disturbance codes')
            arcpy.MakeFeatureLayer_management(covRESULTOPEN, 'rsltOpenLyr')
            SQLstr1 = '"OPENING_CATEGORY_CODE" IN (\'SPEX\')'
            # SQLstr2 = """(DENUDATION_1_DISTURBANCE_CODE is null or DENUDATION_1_DISTURBANCE_CODE = '') and (DENUDATION_2_DISTURBANCE_CODE is null or DENUDATION_2_DISTURBANCE_CODE = '')"""
            arcpy.SelectLayerByAttribute_management("rsltOpenLyr", "NEW_SELECTION", SQLstr1)
            # arcpy.SelectLayerByAttribute_management("rsltOpenLyr", "ADD_TO_SELECTION",SQLstr2)
            count = int(arcpy.GetCount_management('rsltOpenLyr').getOutput(0))
            if count > 0:
                print ('Deleting unwanted RESULTOPEN polygons: ', count)
                arcpy.DeleteFeatures_management('rsltOpenLyr')
            arcpy.Delete_management('rsltOpenLyr')

            # RESULTS FC
            # FILTER OUT RESERVES LATER.  Need to keep in for age if available. (not dispersed, variable, mixed or uniform) AND Selected Natural portions (lake, meadow, rock, swamp)
            # print '\nLooking for Reserves and Natural features from RESULTFC'
            # SQLstr = "(STOCKING_STATUS_CODE in ('MAT') and (SILV_RESERVE_CODE not in ('D','V','M','U') and SILV_RESERVE_CODE is not null)) or (STOCKING_STATUS_CODE in ( 'L', 'M', 'R', 'S'))"
            # arcpy.MakeFeatureLayer_management(covRESULTFC, 'resFCLyr', SQLstr)
            # count = int(arcpy.GetCount_management('resFCLyr').getOutput(0))
            # if count > 0:
            #   print 'Deleting unwanted resFCLyr polygons: ', count
            #   arcpy.DeleteFeatures_management('resFCLyr')
            # arcpy.Delete_management("resFCLyr")

            # RESULTS FC - join to WHSE_FOREST_VEGETATION.RSLT_OPENING_VW which has been flattened for
            # most recent activity for disturbance code/ harvest type code and disturbance dates.
            # NOTE: _VW does not have object IDS so was not able to join.  Use SVW instead.
            # Use Original full records
            # Sort SVW From highest date to lowest so that join occurs on the most current record, if there are duplicates

            if not arcpy.ListFields(covRESULTFC, 'DISTURBANCE_START_DATE'):
                print ('\nJoining fields from RSLT_OPENING_SVW to RESULTFC')
                # arcpy.MakeTableView_management (rslt_open_vw, 'rslt_open_vw_tbl')
                # arcpy.MakeTableView_management (rslt_openings, 'rslt_open_svw_tbl')
                arcpy.Sort_management(covRESULTOPENdict, 'temp_RSLTOPEN_SORT', [["OPENING_WHEN_UPDATED", "DESCENDING"]])
                arcpy.MakeTableView_management('temp_RSLTOPEN_SORT', 'rslt_open_svw_tbl')
                arcpy.AddIndex_management('rslt_open_svw_tbl', "OPENING_ID", "OID_IDX1")

                arcpy.MakeTableView_management(covRESULTFC, 'covRESULTFC_tbl')
                arcpy.AddIndex_management('covRESULTFC_tbl', "OPENING_ID", "OID_IDX2")

                arcpy.JoinField_management('covRESULTFC_tbl', 'OPENING_ID', 'rslt_open_svw_tbl', 'OPENING_ID',
                                        ['OPENING_CATEGORY_CODE', 'OPENING_STATUS_CODE',
                                            'PREV_SITE_INDEX', 'PREV_TREE_SPECIES1_CODE',
                                            'DENUDATION_1_DISTURBANCE_CODE', 'DENUDATION_1_SILV_SYSTEM_CODE',
                                            'DENUDATION_1_COMPLETION_DATE',
                                            'DENUDATION_2_DISTURBANCE_CODE', 'DENUDATION_2_SILV_SYSTEM_CODE',
                                            'DENUDATION_2_COMPLETION_DATE', 'DENUDATION_COUNT',
                                            'PLANTING_1_TECHNIQUE_CODE', 'PLANTING_1_TREATMENT_AREA',
                                            'PLANTING_1_COMPLETION_DATE',
                                            'PLANTING_2_TECHNIQUE_CODE', 'PLANTING_2_TREATMENT_AREA',
                                            'PLANTING_2_COMPLETION_DATE',
                                            'DISTURBANCE_START_DATE', 'DISTURBANCE_END_DATE', 'OPENING_WHEN_CREATED',
                                            'OPENING_WHEN_UPDATED'])

            # Make a full copy with all polys and joined attributes before further processing.
            # if not arcpy.Exists(covRESULTFC+''):
            # arcpy.CopyFeatures_management(covRESULTFC,covRESULTFC+'')

            # get the field lists for coverage's used.
            print ('data manipulation done: ' + deltaTime)
            # list FTEN fields
            print ('finding FTEN fields')
            fields = arcpy.ListFields(covFTENBLKS)
            FTEN_fieldList = []
            for field in fields:
                FTEN_fieldList.append(field.name)
            del field, fields
            # list RSLT opening fields
            print ('Finding RESULT Opening fields')
            fields = arcpy.ListFields(covRESULTOPEN)
            RSLTOPEN_fieldList = []
            for field in fields:
                RSLTOPEN_fieldList.append(field.name)
            del field, fields
            # RSLT FC
            print ('Finding RESULT FC fields')
            fields = arcpy.ListFields(covRESULTFC)
            RSLTFC_fieldList = []
            for field in fields:
                RSLTFC_fieldList.append(field.name)
            del field, fields

            ##CALCULATE FIELDS before removing duplicates - this way, the calculated info is available for all polys if need be
            #######---------------------------------------------------
            print ('\nStarting Field Calculations...')
            # Calculate Standard fields and delete unwanted fields
            # For AGE:  Assume that planting occurs within a few years of disturb, trees are usually ~2yrs old. (as per discussion with Dan Turner)
            #             If we do NOT know a planting date, assume regen gap of approx 3-5 years.  ie. disturb date + 3 yrs
            #                If we DO have a planting date, assume trees are planted at ~2yrs old.  ie. planting date - 2 yrs
            # Use only features with date > yr 2002???  SL

            # Keep Fields for all Features
            keepList = ['OPENING_ID', 'VRI2_SOURCE', 'VRI2_OPENING_ID', 'VRI2_ATT_SOURCE_DISTURB', 'VRI2_ATT_SOURCE_SPECIES',
                        'VRI2_DISTURB_CODE', 'VRI2_DISTURB_DATE', 'VRI2_DISTURB_YR', \
                        'VRI2_HARVESTED', 'VRI2_SITE_INDEX', 'VRI2_SPECIES', 'VRI2_SPECIES_PERCENT', 'VRI2_AGE', 'VRI2_HEIGHT', \
                        'VRI2_SI_ESTIMATED', 'VRI2_SPECIES_ESTIMATED', 'VRI2_AGE_ESTIMATED', 'VRI2_HEIGHT_ESTIMATED',
                        'OBJECTID', 'GEOMETRY_Length', 'Shape_AREA', 'GEOMETRY']

            # -----------
            fcName = 'FTENBLKS'
            print (fcName)
            arcpy.MakeFeatureLayer_management(covFTENBLKS, "covFTENBLKSlyr")
            # Calc Disturb Code to 'L' - logged - we've already filtered for LC, HB, S.  Assume Logged.
            # arcpy.CalculateField_management('covFTENBLKSlyr','VRI2_DISTURB_CODE', "\"Presumed Logged\"", )
            arcpy.CalculateField_management('covFTENBLKSlyr', "VRI2_DISTURB_CODE", "'Presumed Logged'", "PYTHON_9.3", "")

            # Calculate Date as best of DISTURBANCE_END_DATE, DISTURBANCE_START_DATE, PLANNED_HARVEST_DATE, BLOCK_STATUS_DATE -  where not null
            # calc in hierarchical order, such that dates overwrite each other
            for dateFld in ('BLOCK_STATUS_DATE', 'PLANNED_HARVEST_DATE', 'DISTURBANCE_START_DATE', 'DISTURBANCE_END_DATE'):
                arcpy.SelectLayerByAttribute_management("covFTENBLKSlyr", "NEW_SELECTION",
                                                        "" + dateFld + " is not null and " + dateFld + " <> date'12:00:00 AM'")
                # arcpy.CalculateField_management('covFTENBLKSlyr','VRI2_DISTURB_DATE', """DatePart("dd/MM/yyyy",["""+dateFld+"""])""")
                # arcpy.CalculateField_management('covFTENBLKSlyr','VRI2_DISTURB_DATE', "["+dateFld+"]")
                arcpy.CalculateField_management('covFTENBLKSlyr', 'VRI2_DISTURB_DATE', "!" + dateFld + "!", "PYTHON_9.3", "")
                # If the program crashs at the line below, comment out and re-run
                # arcpy.CalculateField_management('covFTENBLKSlyr','VRI2_DISTURB_YR', "DatePart(\"yyyy\",[VRI2_DISTURB_DATE])")
                arcpy.CalculateField_management('covFTENBLKSlyr', 'VRI2_DISTURB_DATE', "!" + dateFld + "!", "PYTHON_9.3", "")
                # If the program crashs at the line below, comment out and re-run
                # arcpy.CalculateField_management('covFTENBLKSlyr','VRI2_DISTURB_YR', "DatePart(\"yyyy\",[VRI2_DISTURB_DATE])")
                # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
                # The following inputs are layers or table views: "TEST_AREA_FTENBLKS_wrk"
                arcpy.ConvertTimeField_management('covFTENBLKSlyr', "VRI2_DISTURB_DATE", "'Not Used'", "VRI2_DISTURB_YR2",
                                                "SHORT", "yyyy;1033;;")
                # The following inputs are layers or table views: "TEST_AREA_FTENBLKS_wrk"
                arcpy.CalculateField_management('covFTENBLKSlyr', "VRI2_DISTURB_YR", "!VRI2_DISTURB_YR2!", "PYTHON_9.3", "")
                arcpy.DeleteField_management('covFTENBLKSlyr', "VRI2_DISTURB_YR2")

            # Again, assume all have been harvested
            arcpy.SelectLayerByAttribute_management("covFTENBLKSlyr", "CLEAR_SELECTION")
            arcpy.CalculateField_management('covFTENBLKSlyr', 'VRI2_HARVESTED', "\"YES\"", "PYTHON_9.3", "")
            # Age as difference from current year and disturb year plus 3 yrs.  ie. We don't know when actually planted.  Assume natural regen starts within 3 years. Min Age of 1.
            arcpy.SelectLayerByAttribute_management("covFTENBLKSlyr", "NEW_SELECTION",
                                                    "VRI2_DISTURB_YR is not null and VRI2_DISTURB_YR <> 0")
            arcpy.CalculateField_management('covFTENBLKSlyr', 'VRI2_AGE', "" + stimePeriod + " - (!VRI2_DISTURB_YR! + 3)",
                                            "PYTHON_9.3", "")
            arcpy.CalculateField_management('covFTENBLKSlyr', 'VRI2_AGE_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("covFTENBLKSlyr", "SUBSET_SELECTION", "VRI2_AGE < 1")
            arcpy.CalculateField_management('covFTENBLKSlyr', 'VRI2_AGE', "1", "PYTHON_9.3", "")

            arcpy.Delete_management("covFTENBLKSlyr")
            # del FTEN fields and keep which ones we want
            for field in FTEN_fieldList:
                if field not in keepList and field not in ['CUT_BLOCK_FOREST_FILE_ID', 'CUT_BLOCK_ID', 'BLOCK_STATUS_CODE',
                                                        'BLOCK_STATUS_DATE', 'PLANNED_HARVEST_DATE',
                                                        'DISTURBANCE_START_DATE', 'DISTURBANCE_END_DATE',
                                                        'HARVEST_AUTH_STATUS_CODE', 'Shape_Length', 'Shape_Area', 'GEOMETRY',
                                                        'GEOMETRY_Length', 'GEOMETRY_AREA', 'SHAPE', 'SHAPE_Length',
                                                        'SHAPE_Area', 'Shape','OBJECTID_1' ]:
                    # print 'Deleting field '+ field
                    # added Shape
                    arcpy.DeleteField_management(covFTENBLKS, field)

            # -----------
            # Already have filtered out anything without a code in DENUDATION_1_DISTURBANCE_CODE or DENUDATION_2_DISTURBANCE_CODE
            fcName = 'RSLTOPEN'
            print( fcName)
            arcpy.MakeFeatureLayer_management(covRESULTOPEN, "covRESULTOPENlyr")
            # Calc Disturb Code - hierarchical.  Overwrite code 1 with code 2 if 2 is not null.  Note that Disturb End Date is latest of DENUDATION_1_COMPLETION_DATE and DENUDATION_2_COMPLETION_DATE
            arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                    "DENUDATION_1_DISTURBANCE_CODE is not null and DENUDATION_1_DISTURBANCE_CODE <> ''")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_DISTURB_CODE', "!DENUDATION_1_DISTURBANCE_CODE!",
                                            "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                    "DENUDATION_2_DISTURBANCE_CODE is not null and DENUDATION_2_DISTURBANCE_CODE <> ''")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_DISTURB_CODE', "!DENUDATION_2_DISTURBANCE_CODE!",
                                            "PYTHON_9.3", "")
            # Calc Harvested  for Logged, Salvaged, or Pest if this occured in either of Denudation disturb code 1 or 2
            # arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION","VRI2_DISTURB_CODE in ('L','S')")
            arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                    "DENUDATION_1_DISTURBANCE_CODE in ('L','S','P') or DENUDATION_2_DISTURBANCE_CODE in ('L','S','P')")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_HARVESTED', "\"YES\"", "PYTHON_9.3", "")
            # If no disturb code, and not FG, assume it will be cut (look at dates > 2010??)
            arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                    "DENUDATION_1_DISTURBANCE_CODE is NULL and DENUDATION_2_DISTURBANCE_CODE is NULL")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_DISTURB_CODE', "\"Presumed Logged\"", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_HARVESTED', "\"YES\"", "PYTHON_9.3", "")

            # FIX THIS SECVTION>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Calculate Date as best of dates where not null.  Use disturbance date where available, or planting date if disturb date not given
            # calc in hierarchical order, such that dates overwrite each other
            # Note that Disturb end date is latest of DENUDATION_1_COMPLETION_DATE and DENUDATION_2_COMPLETION_DATE
            for dateFld in ('OPENING_WHEN_CREATED', 'PLANTING_1_COMPLETION_DATE', 'PLANTING_2_COMPLETION_DATE',
                            'DISTURBANCE_START_DATE', 'DISTURBANCE_END_DATE'):
                arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                        "" + dateFld + " is not null and " + dateFld + " <> date'12:00:00 AM'")
                # arcpy.CalculateField_management('covRESULTOPENlyr',"DATE_RSLTOPEN", "DatePart(\"dd/MM/yyyy\",["+dateFld+"]")
                arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_DISTURB_DATE', "!" + dateFld + "!", "PYTHON_9.3", "")
                # arcpy.CalculateField_management('covRESULTOPENlyr','VRI2_DISTURB_YR', "DatePart(\"yyyy\",[VRI2_DISTURB_DATE])",  "PYTHON_9.3", "" )

                arcpy.ConvertTimeField_management('covRESULTOPENlyr', "VRI2_DISTURB_DATE", "'Not Used'", "VRI2_DISTURB_YR2",
                                                "SHORT", "yyyy;1033;;")
                # The following inputs are layers or table views: "TEST_AREA_FTENBLKS_wrk"
                arcpy.CalculateField_management('covRESULTOPENlyr', "VRI2_DISTURB_YR", "!VRI2_DISTURB_YR2!", "PYTHON_9.3", "")
                arcpy.DeleteField_management('covRESULTOPENlyr', "VRI2_DISTURB_YR2")
                # Repaired to here for 64 bit

            # Age as difference from current year and disturb year plus 3 yrs if planting date NOT know.   Min Age of 1.
            # If using year of planting, then assume trees are ~2yrs old when planted
            arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                    "VRI2_AGE is null and (VRI2_DISTURB_YR is not null and VRI2_DISTURB_YR <> 0)")
            # Default to disturb year plus 3 for natural regen
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_AGE', "" + stimePeriod + " - (!VRI2_DISTURB_YR! + 3)",
                                            "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_AGE_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            # recalc if planting dates were used.  Just use PLANTING_1_COMPLETION_DATE. Note that this is sometimes after PLANTING_2_COMPLETION_DATE(??)
            arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                    "PLANTING_1_COMPLETION_DATE is not null and PLANTING_1_COMPLETION_DATE <> date'12:00:00 AM'")
            arcpy.ConvertTimeField_management('covRESULTOPENlyr', "PLANTING_1_COMPLETION_DATE", "'Not Used'",
                                            "PLANTING_1_COMPLETION_DATE_YR", "SHORT", "yyyy;1033;;")

            # arcpy.CalculateField_management('covRESULTOPENlyr','VRI2_AGE',""+stimePeriod+" - (DatePart(\"yyyy\",[PLANTING_1_COMPLETION_DATE]) - 2)")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_AGE',
                                            "" + stimePeriod + " - (!PLANTING_1_COMPLETION_DATE_YR! - 2)", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_AGE_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")

            # Calc to 1 if < 1 year of age
            arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION",
                                                    "VRI2_AGE < 1 and VRI2_AGE is not null")
            arcpy.CalculateField_management('covRESULTOPENlyr', 'VRI2_AGE', "1", "PYTHON_9.3", "")
            # Species - assume species will be the same as previous ?  --> USE FROM VRI further down in script
            # arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION", "PREV_TREE_SPECIES1_CODE is not NULL and PREV_TREE_SPECIES1_CODE <> ''" )
            # arcpy.CalculateField_management('covRESULTOPENlyr','VRI2_SPECIES',"[PREV_TREE_SPECIES1_CODE]")
            # arcpy.CalculateField_management('covRESULTOPENlyr','VRI2_SPECIES_ESTIMATED',"\"YES\"")
            # arcpy.SelectLayerByAttribute_management("covRESULTOPENlyr", "NEW_SELECTION", "PREV_SITE_INDEX > 0" )
            # arcpy.CalculateField_management('covRESULTOPENlyr','VRI2_SITE_INDEX',"[PREV_SITE_INDEX]")
            # arcpy.CalculateField_management('covRESULTOPENlyr','VRI2_SI_ESTIMATED',"\"YES\"")

            arcpy.Delete_management("covRESULTOPENlyr")
            # del RSLT Opening fields and keep which ones we want
            for field in RSLTOPEN_fieldList:
                if field not in keepList and field not in ['MAP_LABEL', 'OPENING_CATEGORY_CODE', 'OPENING_STATUS_CODE',
                                                        'PREV_SITE_INDEX', 'PREV_TREE_SPECIES1_CODE',
                                                        'DENUDATION_1_DISTURBANCE_CODE', 'DENUDATION_1_SILV_SYSTEM_CODE',
                                                        'DENUDATION_1_COMPLETION_DATE',
                                                        'DENUDATION_2_DISTURBANCE_CODE', 'DENUDATION_2_SILV_SYSTEM_CODE',
                                                        'DENUDATION_2_COMPLETION_DATE',
                                                        'PLANTING_1_TECHNIQUE_CODE', 'PLANTING_1_TREATMENT_AREA',
                                                        'PLANTING_1_COMPLETION_DATE',
                                                        'PLANTING_2_TECHNIQUE_CODE', 'PLANTING_2_TREATMENT_AREA',
                                                        'PLANTING_2_COMPLETION_DATE',
                                                        'DISTURBANCE_START_DATE', 'DISTURBANCE_END_DATE',
                                                        'OPENING_WHEN_CREATED', 'OPENING_WHEN_UPDATED',
                                                        'GEOMETRY', 'Shape', 'Shape_Length', 'Shape_Area', 'GEOMETRY_Length',
                                                        'GEOMETRY_AREA', 'Shape', 'GEOMETRY_Area', ]:
                    arcpy.DeleteField_management(covRESULTOPEN, field)

            # -----------
            fcName = 'RSLTFC'
            print (fcName)
            # Reserves and Natural Features
            reserveQry = "(STOCKING_STATUS_CODE in ('MAT') and (SILV_RESERVE_CODE not in ('D','V','M','U') and SILV_RESERVE_CODE is not null)) or (STOCKING_STATUS_CODE in ( 'L', 'M', 'R', 'S'))"

            arcpy.MakeFeatureLayer_management(covRESULTFC, "covRESULTFClyr")
            # Calc Disturb Code - hierarchical.  Overwrite NSR with code 1, then with code 2 if 2 is not null.  Note that Disturb end date is latest of DENUDATION_1_COMPLETION_DATE and DENUDATION_2_COMPLETION_DATE
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION", "STOCKING_STATUS_CODE = 'NSR'")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_DISTURB_CODE', "!STOCKING_STATUS_CODE!", "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "DENUDATION_1_DISTURBANCE_CODE is not null and DENUDATION_1_DISTURBANCE_CODE <> ''")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_DISTURB_CODE', "!DENUDATION_1_DISTURBANCE_CODE!",
                                            "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "DENUDATION_2_DISTURBANCE_CODE is not null and DENUDATION_2_DISTURBANCE_CODE <> ''")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_DISTURB_CODE', "!DENUDATION_2_DISTURBANCE_CODE!",
                                            "PYTHON_9.3", "")
            # Calc Harvested  for NSR, Logged,Salvaged, Pest if this occured in either of Denudation disturb code 1 or 2
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "DENUDATION_1_DISTURBANCE_CODE in ('L','S','P') or DENUDATION_2_DISTURBANCE_CODE in ('L','S','P')")
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "ADD_TO_SELECTION", "STOCKING_STATUS_CODE = 'NSR'")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_HARVESTED', "\"YES\"", "PYTHON_9.3", "")

            # Exclude Reserves - calc back to NULL
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION", reserveQry)
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_DISTURB_CODE', "\"Reserve or Natural\"", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_HARVESTED', "None", "PYTHON_9.3", "")

            # Any remaining openings without a disturbance code will be presumed to be logged
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION", "VRI2_DISTURB_CODE is null")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_DISTURB_CODE', "\"Presumed Logged\"", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_HARVESTED', "\"YES\"", "PYTHON_9.3", "")

            # Calculate Date as best of DISTURBANCE_END_DATE, DISTURBANCE_START_DATE, PLANNED_HARVEST_DATE, BLOCK_STATUS_DATE - ie where not null
            # calc in hierarchical order, such that dates overwrite each other
            # Do not include reserves/natural features
            ##NEED TO LINK TO RSLT_OPENING_VW to get disturbance type and date - this was done above
            for dateFld in (
            'FOREST_COVER_WHEN_CREATED', 'OPENING_WHEN_CREATED', 'PLANTING_1_COMPLETION_DATE', 'PLANTING_2_COMPLETION_DATE',
            'DISTURBANCE_START_DATE', 'DISTURBANCE_END_DATE'):
                arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                        "" + dateFld + " is not null and " + dateFld + " <> date'12:00:00 AM'")
                arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "REMOVE_FROM_SELECTION", reserveQry)
                # arcpy.CalculateField_management('covRESULTFClyr','VRI2_DISTURB_DATE', "["+dateFld+"]","PYTHON_9.3", "" )
                arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_DISTURB_DATE', "!" + dateFld + "!", "PYTHON_9.3", "")
                # arcpy.CalculateField_management('covRESULTFClyr','VRI2_DISTURB_YR', "DatePart(\"yyyy\",[VRI2_DISTURB_DATE])")
                arcpy.ConvertTimeField_management('covRESULTFClyr', "VRI2_DISTURB_DATE", "'Not Used'", "VRI2_DISTURB_YR2",
                                                "SHORT", "yyyy;1033;;")
                arcpy.CalculateField_management('covRESULTFClyr', "VRI2_DISTURB_YR", "!VRI2_DISTURB_YR2!", "PYTHON_9.3", "")
                arcpy.DeleteField_management('covRESULTFClyr', "VRI2_DISTURB_YR2")

                # Calc best of stand age and height based on available info for even and uneven aged stands.  Note that the age etc were taken at the REFERENCE_YEAR
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "FOREST_COVER_INV_TYPE = 'EVEN' and I_SPECIES_CODE_1 is not null")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES", "!I_SPECIES_CODE_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES_PERCENT", "!I_SPECIES_PERCENT_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE",
                                            "!I_SPECIES_AGE_1! + (" + stimePeriod + " - !REFERENCE_YEAR!)", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_HEIGHT", "!I_SPECIES_HEIGHT_1!", "PYTHON_9.3",
                                            "")  ###ADD XTRA HEIGHT depending on time since reference year?

            # For Uneven, Calc age based on the layer with the greatest stems per HA  (only one of these conditions can be met)
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "FOREST_COVER_INV_TYPE = 'UNEVEN' and (I1_TOTAL_STEMS_PER_HA > I2_TOTAL_STEMS_PER_HA and I1_TOTAL_STEMS_PER_HA > I3_TOTAL_STEMS_PER_HA and I1_TOTAL_STEMS_PER_HA > I4_TOTAL_STEMS_PER_HA)")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES", "!I_SPECIES_CODE_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES_PERCENT", "!I_SPECIES_PERCENT_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE",
                                            "!I_SPECIES_AGE_1! + (" + stimePeriod + " - !REFERENCE_YEAR!)", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_HEIGHT", "!I_SPECIES_HEIGHT_1!", "PYTHON_9.3",
                                            "")  ###ADD XTRA HEIGHT depending on time since reference year?

            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "FOREST_COVER_INV_TYPE = 'UNEVEN' and (I2_TOTAL_STEMS_PER_HA > I1_TOTAL_STEMS_PER_HA and I2_TOTAL_STEMS_PER_HA > I3_TOTAL_STEMS_PER_HA and I2_TOTAL_STEMS_PER_HA > I4_TOTAL_STEMS_PER_HA)")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES", "!I_SPECIES_CODE_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES_PERCENT", "!I_SPECIES_PERCENT_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE",
                                            "!I_SPECIES_AGE_1! + (" + stimePeriod + " - !REFERENCE_YEAR!)", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_HEIGHT", "!I_SPECIES_HEIGHT_1!", "PYTHON_9.3",
                                            "")  ###ADD XTRA HEIGHT depending on time since reference year?

            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "FOREST_COVER_INV_TYPE = 'UNEVEN' and (I3_TOTAL_STEMS_PER_HA > I2_TOTAL_STEMS_PER_HA and I3_TOTAL_STEMS_PER_HA > I1_TOTAL_STEMS_PER_HA and I3_TOTAL_STEMS_PER_HA > I4_TOTAL_STEMS_PER_HA)")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES", "!I_SPECIES_CODE_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES_PERCENT", "!I_SPECIES_PERCENT_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE",
                                            "!I_SPECIES_AGE_1! + (" + stimePeriod + " - !REFERENCE_YEAR!)", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_HEIGHT", "!I_SPECIES_HEIGHT_1!", "PYTHON_9.3",
                                            "")  ###ADD XTRA HEIGHT depending on time since reference year?

            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "FOREST_COVER_INV_TYPE = 'UNEVEN' and (I4_TOTAL_STEMS_PER_HA > I2_TOTAL_STEMS_PER_HA and I4_TOTAL_STEMS_PER_HA > I3_TOTAL_STEMS_PER_HA and I4_TOTAL_STEMS_PER_HA > I1_TOTAL_STEMS_PER_HA)")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES", "!I_SPECIES_CODE_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES_PERCENT", "!I_SPECIES_PERCENT_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE",
                                            "!I_SPECIES_AGE_1! + (" + stimePeriod + " - !REFERENCE_YEAR!)", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_HEIGHT", "!I_SPECIES_HEIGHT_1!", "PYTHON_9.3",
                                            "")  ###ADD XTRA HEIGHT depending on time since reference year?

            # Fill in Blank Ages if year of Disturbance is known
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "VRI2_AGE is null and (VRI2_DISTURB_YR is not null and VRI2_DISTURB_YR <> 0)")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE", "" + stimePeriod + " - (!VRI2_DISTURB_YR! + 3)",
                                            "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_AGE_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "SUBSET_SELECTION", "VRI2_AGE < 1")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_AGE', "1", "PYTHON_9.3", "")

            # Fill in Blank Species - assume species will be the same as previous if not already in RSLTS FC, get from RSLTS Open
            #            --> USE FROM VRI further down in script
            # arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION", "(VRI2_SPECIES is NULL or VRI2_SPECIES = '') and (PREV_TREE_SPECIES1_CODE is not NULL and PREV_TREE_SPECIES1_CODE <> '')" )
            # arcpy.CalculateField_management('covRESULTFClyr','VRI2_SPECIES',"[PREV_TREE_SPECIES1_CODE]")

            # Site Index
            arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION",
                                                    "SITE_INDEX > 0 and SITE_INDEX is not NULL")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SITE_INDEX", "!SITE_INDEX!", "PYTHON_9.3", "")
            # Prev Site Index?
            #            --> USE FROM VRI further down in script
            # arcpy.SelectLayerByAttribute_management("covRESULTFClyr", "NEW_SELECTION", "(VRI2_SITE_INDEX is null or VRI2_SITE_INDEX = '') and PREV_SITE_INDEX > 0" )
            # arcpy.CalculateField_management('covRESULTFClyr','VRI2_SITE_INDEX',"[PREV_SITE_INDEX]")

            # for FOREST_COVER_INV_TYPE = NONE or UNKNOWN??
            # Calc Roads, Unnatural (landings etc) to age 0 height 0.
            # miscQuery = "STOCKING_STATUS_CODE = 'NSR' or (STOCKING_STATUS_CODE = 'NP' AND STOCKING_TYPE_CODE in ( 'RD', 'UNN'))"
            miscQuery = "(STOCKING_STATUS_CODE = 'NP' AND STOCKING_TYPE_CODE in ( 'RD', 'UNN'))"
            arcpy.SelectLayerByAttribute_management('covRESULTFClyr', "NEW_SELECTION", miscQuery)
            # Default to 0/Null
            # arcpy.CalculateField_management('covRESULTFClyrMisc',"VRI2_SPECIES","NULL")  #Should already be null??
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE", "0", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES", "None", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES_PERCENT", "None", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_HEIGHT", "0", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_AGE_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_HEIGHT_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")

            # Non-plantable - eg. from severe forest fire or non-productivt - Default to 1 year old
            miscQuery = "STOCKING_STATUS_CODE = 'NSR' AND STOCKING_TYPE_CODE = 'NPL'"
            arcpy.SelectLayerByAttribute_management('covRESULTFClyr', "NEW_SELECTION", miscQuery)
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_AGE", "1", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES", "None", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_SPECIES_PERCENT", "None", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', "VRI2_HEIGHT", "0.2", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_AGE_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.CalculateField_management('covRESULTFClyr', 'VRI2_HEIGHT_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            # CHECK FOR blank ages!!  Check NSR. Check if calculated correctly

            arcpy.Delete_management("covRESULTFClyr")

            # del RSLT FC fields and keep which ones we want
            for field in RSLTFC_fieldList:
                if field not in keepList and field not in ['STANDARDS_UNIT_ID', 'SILV_POLYGON_NUMBER',
                                                        'STOCKING_STATUS_CODE', 'STOCKING_TYPE_CODE', 'SILV_RESERVE_CODE',
                                                        'REFERENCE_YEAR', 'SITE_INDEX', 'FOREST_COVER_INV_TYPE',
                                                        'I_SPECIES_CODE_1', 'I_SPECIES_PERCENT_1', 'I_SPECIES_AGE_1',
                                                        'I_SPECIES_HEIGHT_1',
                                                        'I1_SPECIES_CODE_1', 'I1_SPECIES_PERCENT_1', 'I1_SPECIES_AGE_1',
                                                        'I1_SPECIES_HEIGHT_1', 'I1_TOTAL_STEMS_PER_HA',
                                                        'I2_SPECIES_CODE_1', 'I2_SPECIES_PERCENT_1', 'I2_SPECIES_AGE_1',
                                                        'I2_SPECIES_HEIGHT_1', 'I2_TOTAL_STEMS_PER_HA',
                                                        'I3_SPECIES_CODE_1', 'I3_SPECIES_PERCENT_1', 'I3_SPECIES_AGE_1',
                                                        'I3_SPECIES_HEIGHT_1', 'I3_TOTAL_STEMS_PER_HA',
                                                        'I4_SPECIES_CODE_1', 'I4_SPECIES_PERCENT_1', 'I4_SPECIES_AGE_1',
                                                        'I4_SPECIES_HEIGHT_1', 'I4_TOTAL_STEMS_PER_HA',
                                                        'OPENING_CATEGORY_CODE', 'OPENING_STATUS_CODE', 'PREV_SITE_INDEX',
                                                        'PREV_TREE_SPECIES1_CODE',
                                                        'DENUDATION_1_DISTURBANCE_CODE', 'DENUDATION_1_SILV_SYSTEM_CODE',
                                                        'DENUDATION_1_COMPLETION_DATE',
                                                        'DENUDATION_2_DISTURBANCE_CODE', 'DENUDATION_2_SILV_SYSTEM_CODE',
                                                        'DENUDATION_2_COMPLETION_DATE',
                                                        'PLANTING_1_TECHNIQUE_CODE', 'PLANTING_1_TREATMENT_AREA',
                                                        'PLANTING_1_COMPLETION_DATE',
                                                        'PLANTING_2_TECHNIQUE_CODE', 'PLANTING_2_TREATMENT_AREA',
                                                        'PLANTING_2_COMPLETION_DATE',
                                                        'DISTURBANCE_START_DATE', 'DISTURBANCE_END_DATE',
                                                        'FOREST_COVER_WHEN_CREATED', 'FOREST_COVER_WHEN_UPDATED',
                                                        'OPENING_WHEN_CREATED', 'OPENING_WHEN_UPDATED', 'Shape_Length',
                                                        'Shape_Area', 'Shape', 'GEOMETRY_Length',
                                                        'GEOMETRY_Area', 'DEOMETRY', 'I_CROWN_CLOSURE_PERCENT',
                                                        'I1_CROWN_CLOSURE_PERCENT', 'I2_CROWN_CLOSURE_PERCENT']:
                    arcpy.DeleteField_management(covRESULTFC, field)

            # -----------
            fcName = 'VRI'
            print (fcName)
            # DO NOT USE OPENING_IND! this was an old attribute and is not reliable
            # Openings as:
            #    OPENING_ID, OPENING_NUMBER, HARVEST DATE, DISTURB CODE = L
            # Note that Disturbance Codes in VRI are different than Disturbance code in RSLTS
            arcpy.MakeFeatureLayer_management(covVRI, 'vegLyr')
            # Calc Age and Height for VRI
            arcpy.CalculateField_management('vegLyr', "VRI2_SPECIES", "!SPECIES_CD_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', "VRI2_SPECIES_PERCENT", "!SPECIES_PCT_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', "VRI2_AGE", "!PROJ_AGE_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', "VRI2_HEIGHT", "!PROJ_HEIGHT_1!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', "VRI2_SITE_INDEX", "!SITE_INDEX!", "PYTHON_9.3", "")

            # Use Est Site Index to fill in blanks
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION",
                                                    "VRI2_SITE_INDEX is null and EST_SITE_INDEX is not null ")
            arcpy.CalculateField_management('vegLyr', "VRI2_SITE_INDEX", "!EST_SITE_INDEX!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', 'VRI2_SI_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")

            # ----
            # OPENINGS - assume Logged, unless overwriten below
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION", "OPENING_ID IS NOT NULL and OPENING_ID <> 0")
            arcpy.SelectLayerByAttribute_management("vegLyr", "ADD_TO_SELECTION",
                                                    "OPENING_NUMBER is not  null and OPENING_NUMBER <> ''")
            arcpy.CalculateField_management('vegLyr', 'VRI2_HARVESTED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', 'VRI2_DISTURB_CODE', "\"Presumed Logged\"", "PYTHON_9.3", "")

            # Assume NSR was Harvested - NOT USED - see below
            # arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION", "NON_FOREST_DESCRIPTOR = 'NSR'")
            # arcpy.CalculateField_management('vegLyr','VRI2_HARVESTED', "\"YES\"")
            # arcpy.CalculateField_management('vegLyr','VRI2_DISTURB_CODE', "\"NSR\"")

            # Calc Harvest Date if known, and Harvested where there is any kind of opening
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION",
                                                    "HARVEST_DATE IS NOT NULL and HARVEST_DATE <> date'12:00:00 AM'")
            arcpy.CalculateField_management('vegLyr', "VRI2_DISTURB_DATE", "!HARVEST_DATE!", "PYTHON_9.3", "")
            # arcpy.CalculateField_management('vegLyr','VRI2_DISTURB_YR', "DatePart(\"yyyy\",[VRI2_DISTURB_DATE])")
            arcpy.ConvertTimeField_management('vegLyr', "VRI2_DISTURB_DATE", "'Not Used'", "VRI2_DISTURB_YR2", "SHORT",
                                            "yyyy;1033;;")
            arcpy.CalculateField_management('vegLyr', "VRI2_DISTURB_YR", "!VRI2_DISTURB_YR2!", "PYTHON_9.3", "")
            arcpy.DeleteField_management('vegLyr', "VRI2_DISTURB_YR2")

            # Add other openings, to be calculated as Harvested
            arcpy.SelectLayerByAttribute_management("vegLyr", "ADD_TO_SELECTION", "LINE_7B_DISTURBANCE_HISTORY like 'L%'")
            arcpy.CalculateField_management('vegLyr', 'VRI2_HARVESTED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', 'VRI2_DISTURB_CODE', "\"L\"", "PYTHON_9.3", "")
            # ----
            # Fill in  NSR where Harvested and no other disturb code
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION",
                                                    "VRI2_HARVESTED = 'YES' and VRI2_DISTURB_CODE is null and NON_FOREST_DESCRIPTOR = 'NSR'")
            arcpy.CalculateField_management('vegLyr', 'VRI2_DISTURB_CODE', "\"NSR\"", "PYTHON_9.3", "")

            # Fill in Blank Disturbance from Non-Logging Dist code
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION",
                                                    "VRI2_DISTURB_YR is null and VRI2_HARVESTED = 'YES' and EARLIEST_NONLOGGING_DIST_TYPE is not NULL")
            arcpy.CalculateField_management('vegLyr', "VRI2_DISTURB_CODE", "!EARLIEST_NONLOGGING_DIST_TYPE!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', 'VRI2_DISTURB_DATE', "!EARLIEST_NONLOGGING_DIST_DATE!", "PYTHON_9.3", "")
            # arcpy.CalculateField_management('vegLyr','VRI2_DISTURB_YR', "DatePart(\"yyyy\",[VRI2_DISTURB_DATE])", "PYTHON_9.3", "")
            arcpy.ConvertTimeField_management('vegLyr', "VRI2_DISTURB_DATE", "'Not Used'", "VRI2_DISTURB_YR3", "SHORT",
                                            "yyyy;1033;;")
            arcpy.CalculateField_management('vegLyr', "VRI2_DISTURB_YR", "!VRI2_DISTURB_YR3!", "PYTHON_9.3", "")
            arcpy.DeleteField_management('vegLyr', "VRI2_DISTURB_YR3")
            arcpy.Delete_management("vegLyr")

            # *********
            # *********
            # Fill in blank Disturb year from Openings
            print ('1.  Getting Opening Disturb info for missing VRI values...')
            # arcpy.QualifiedFieldNames = "QUALIFIED"
            arcpy.MakeFeatureLayer_management(covVRI, 'vegLyrJoin',
                                            "OPENING_ID is not null and OPENING_ID <> 0 and VRI2_DISTURB_YR is null")
            # arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION", "OPENING_ID is not null and OPENING_ID <> 0 and VRI2_DISTURB_YR is null")
            arcpy.MakeFeatureLayer_management(covRESULTOPEN, "covRESULTOPENAttlyr")

            # arcpy.AddJoin_management('vegLyrJoin', 'VRI2_OPENING_ID', 'covRESULTOPENAttlyr', 'VRI2_OPENING_ID')
            updFieldList = ['VRI2_ATT_SOURCE_DISTURB', 'VRI2_DISTURB_CODE', 'VRI2_DISTURB_DATE', 'VRI2_DISTURB_YR',
                            'VRI2_HARVESTED']
            arcpy.JoinField_management('vegLyrJoin', 'VRI2_OPENING_ID', 'covRESULTOPENAttlyr', 'VRI2_OPENING_ID', updFieldList)
            arcpy.SelectLayerByAttribute_management("vegLyrJoin", "NEW_SELECTION",
                                                    "VRI2_ATT_SOURCE_DISTURB_1 is not null and VRI2_ATT_SOURCE_DISTURB_1 <> ''")
            for field in updFieldList:
                # field1 = varName +'_VRI_wrk.'+field
                # field2 = varName +'_RSLTOPEN_wrk.'+field
                # arcpy.CalculateField_management('vegLyrJoin',field,"["+field+"_1]", "PYTHON_9.3", "")
                arcpy.CalculateField_management('vegLyrJoin', field, "!" + field + "_1!", "PYTHON_9.3", "")
                # arcpy.CalculateField_management('vegLyrJoin',field1, "["+field2+"]")
            for field in updFieldList:
                arcpy.DeleteField_management('vegLyrJoin', field + '_1')
            # arcpy.RemoveJoin_management('vegLyrJoin')
            arcpy.Delete_management("vegLyrJoin")
            arcpy.Delete_management("covRESULTOPENAttlyr")

            # VRI2_DISTURB_YR IS null AND HARVESTED IS NOT NULL. Opening ID just does not work some times - must do spatially
            print ('2.  Getting Disturb Yr where no opening ID')
            arcpy.MakeFeatureLayer_management(covVRI, 'vegLyrNoDate', "VRI2_HARVESTED is not null and VRI2_DISTURB_YR is null")
            arcpy.MakeFeatureLayer_management(covRESULTOPEN, "covRESULTOPENlyr")
            if not arcpy.Exists('Harvest_no_Date'):
                arcpy.Identity_analysis("vegLyrNoDate", "covRESULTOPENlyr", "Harvest_no_Date")
            if not arcpy.Exists('Harvest_no_Date_SORT'):
                arcpy.Sort_management('Harvest_no_Date', 'Harvest_no_Date_SORT', [["Shape_Area", "DESCENDING"]])
            arcpy.MakeFeatureLayer_management('Harvest_no_Date_SORT', "tempLyrSORT")
            # FIDLink = 'FID_' + varName + '_VRI_wrk'
            joinFieldList = ['VRI2_ATT_SOURCE_DISTURB_1', 'VRI2_DISTURB_CODE_1', 'VRI2_DISTURB_DATE_1', 'VRI2_DISTURB_YR_1',
                            'VRI2_HARVESTED_1']
            updFieldList = ['VRI2_ATT_SOURCE_DISTURB', 'VRI2_DISTURB_CODE', 'VRI2_DISTURB_DATE', 'VRI2_DISTURB_YR',
                            'VRI2_HARVESTED']
            fields = arcpy.ListFields('tempLyrSORT')
            fid_fields = [field.name for field in fields if "_VRI_WRK" in field.name.upper()]
            print("FID-like fields:", fid_fields)
            FIDLink=fid_fields[0]
            arcpy.JoinField_management('vegLyrNoDate', 'OBJECTID', 'tempLyrSORT', FIDLink, joinFieldList)
            arcpy.SelectLayerByAttribute_management("vegLyrNoDate", "NEW_SELECTION",
                                                    "VRI2_ATT_SOURCE_DISTURB_1 is not null and VRI2_ATT_SOURCE_DISTURB_1 <> ''")
            for field in updFieldList:
                arcpy.CalculateField_management('vegLyrNoDate', field, "!" + field + "_1!", "PYTHON_9.3", "")
            for field2 in joinFieldList:
                arcpy.DeleteField_management('vegLyrNoDate', field2)
            arcpy.Delete_management("vegLyrNoDate")
            arcpy.Delete_management("tempLyrSORT")

            # Fill in blank species info from  FC  - by spatial overlay.  Take the FC unit with the largest area.
            # WARNING - this is likely a 1-many relationship, as an FC opening can be sub-divided into units.
            # Do an identity instead?? Then sort by area, and take the resulting unit with the largest area?
            # Alternative would be to cut in the units as well, but havent they already been 'interpreted' into the VRI ?
            print ('3.  Getting Opening species info for VRI missing values...')
            arcpy.MakeFeatureLayer_management(covVRI, 'vegLyrNoAge',
                                            "((OPENING_ID is not null and OPENING_ID <> 0) or  VRI2_HARVESTED = 'YES') and VRI2_AGE is null")
            arcpy.MakeFeatureLayer_management(covRESULTFC, "covRESULTFCAttlyr",
                                            "VRI2_DISTURB_CODE <> 'Reserve or Natural' and (VRI2_AGE is not null and VRI2_AGE > 0)")
            if not arcpy.Exists('Opening_no_fc_info'):
                arcpy.Identity_analysis("vegLyrNoAge", "covRESULTFCAttlyr", "Opening_no_fc_info")
            if not arcpy.Exists('Opening_no_fc_info_SORT'):
                arcpy.Sort_management('Opening_no_fc_info', 'Opening_no_fc_info_SORT', [["Shape_AREA", "DESCENDING"]])

            arcpy.MakeFeatureLayer_management('Opening_no_fc_info_SORT', "tempLyrSORT")
            # FIDLink = 'FID_' + varName + '_VRI_wrk'
            # arcpy.AddJoin_management('vegLyrNoAge', FIDLink, 'tempLyrSORT', FIDLink)
            joinFieldList = ['VRI2_ATT_SOURCE_SPECIES_1', 'VRI2_SPECIES_1', 'VRI2_SPECIES_PERCENT_1', 'VRI2_AGE_1',
                            'VRI2_HEIGHT_1', \
                            'VRI2_SPECIES_ESTIMATED_1', 'VRI2_AGE_ESTIMATED_1', 'VRI2_HEIGHT_ESTIMATED_1']
            updFieldList = ['VRI2_ATT_SOURCE_SPECIES', 'VRI2_SPECIES', 'VRI2_SPECIES_PERCENT', 'VRI2_AGE', 'VRI2_HEIGHT', \
                            'VRI2_SPECIES_ESTIMATED', 'VRI2_AGE_ESTIMATED', 'VRI2_HEIGHT_ESTIMATED']
            fields = arcpy.ListFields('tempLyrSORT')
            fid_fields = [field.name for field in fields if "_VRI_WRK" in field.name.upper()]
            print("FID-like fields:", fid_fields)
            FIDLink=fid_fields[0]
            arcpy.JoinField_management('vegLyrNoAge', 'OBJECTID', 'tempLyrSORT', FIDLink, joinFieldList)
            arcpy.SelectLayerByAttribute_management("vegLyrNoAge", "NEW_SELECTION",
                                                    "VRI2_ATT_SOURCE_SPECIES_1 is not null and VRI2_ATT_SOURCE_SPECIES_1 <> ''")
            for field in updFieldList:
                # ADD criteria for NOT NULL?
                # field1 = varName +'_VRI_wrk.'+field
                # field2 = varName +'_RSLTFC_wrk.'+field
                # field2 = 'Opening_no_fc_info_SORT.'+field
                arcpy.CalculateField_management('vegLyrNoAge', field, "!" + field + "_1!", "PYTHON_9.3", "")
                # arcpy.CalculateField_management('vegLyrNoAge',field1, field2)
            for field2 in joinFieldList:
                arcpy.DeleteField_management('vegLyrNoAge', field2)
            # arcpy.RemoveJoin_management ('vegLyrNoAge')
            arcpy.Delete_management("vegLyrNoAge")
            arcpy.Delete_management("tempLyrSORT")
            # arcpy.Delete_management("Opening_no_fc_info_SORT")
            # --

            ###################################################
            ####Finish VRI by filling in missing ages & species
            arcpy.MakeFeatureLayer_management(covVRI, 'vegLyr')

            # Fill in  blank ages - calc from year of disturb etc...
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION",
                                                    "VRI2_AGE is null and (VRI2_DISTURB_YR  > 0 and VRI2_DISTURB_YR is not null)")
            arcpy.CalculateField_management('vegLyr', 'VRI2_AGE', "" + stimePeriod + " - (!VRI2_DISTURB_YR! + 3)", "PYTHON_9.3",
                                            "")
            arcpy.CalculateField_management('vegLyr', 'VRI2_AGE_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("vegLyr", "SUBSET_SELECTION", "VRI2_AGE < 1")
            arcpy.CalculateField_management('vegLyr', 'VRI2_AGE', "1", "PYTHON_9.3", "")

            # Fill in blank species for openings where age is known. - This could be used for height info
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION",
                                                    "VRI2_HARVESTED = 'YES' and VRI2_AGE is not null ")
            arcpy.SelectLayerByAttribute_management("vegLyr", "SUBSET_SELECTION",
                                                    "VRI2_SPECIES is null and EST_SITE_INDEX_SPECIES_CD is not null ")
            arcpy.CalculateField_management('vegLyr', "VRI2_SPECIES", "!EST_SITE_INDEX_SPECIES_CD!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('vegLyr', 'VRI2_SPECIES_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")

            # Create separate Features for VRI Opening
            arcpy.SelectLayerByAttribute_management("vegLyr", "NEW_SELECTION", "VRI2_HARVESTED = 'YES'")
            arcpy.CopyFeatures_management('vegLyr', varName + "_VEG_R1_POLY_OPENINGS")  # Make VRI opening features
            delList.append(sExtractLoc + "/" + varName + "_VEG_R1_POLY_OPENINGS")  # add name to list

            arcpy.Delete_management("vegLyr")

            deltaTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
            print ('Field Calcs DONE at: ' + deltaTime)
            # sys.exit()

            # -----------
            # vri simplify fields and keep which ones we want. All fields kept for now.
            fields = arcpy.ListFields(covVRI)
            VRI_fieldList = []
            for field in fields:
                VRI_fieldList.append(field.name)
            del field, fields

            # del vri fields and keep which ones we want
            # for field in VRI_fieldList:
            #    if field not in ['FEATURE_ID', 'FOR_MGMT_LAND_BASE_IND','PROJ_AGE_1','PROJ_AGE_CLASS_CD_1','OPENING_ID','OPENING_IND','OBJECTID','GEOMETRY_Length', 'Shape_AREA','GEOMETRY']:
            #        arcpy.DeleteField_management(covVRI, field)

            # ------
            # SAMPLE/TEST CODE
            # calculate VRI Harvest Date

            # ** Disturbance dates only exist in RESULTS open this will make a dictionary list to populate the dates on opeing id
            # rslt_open_dict = create_dict_from_fields(covRESULTOPENdict,"OPENING_ID","DISTURBANCE_START_DATE","")
            # Populate_table_withdictionary("AllVRIfinal", "HARVESTED_DATE", "OPENING_IDFC", rslt_open_dict,"HARVESTED_DATE")

            # rslt_act_dict = create_dict_from_fields(covRSLTACT,"OPENING_ID","ATU_COMPLETION_DATE","")
            # Populate_table_withdictionary("AllVRIfinal", "HARVESTED_DATE", "OPENING_ID", rslt_act_dict,"HARVESTED_DATE")

            # select
            # LOGGING_DATE IS null AND HARVESTED IS NOT NULL. Opening ID just does not work some times
            # arcpy.MakeFeatureLayer_management("AllVRIfinal","VRILyr","\"HARVESTED_DATE\" IS null AND \"HARVESTED\" IS NOT NULL")
            # arcpy.MakeFeatureLayer_management(covRESULTOPENdict,"RSLTopenLyr","\"OPENING_CATEGORY_CODE\" not in ('NDFS','NDCF','NDAML','NDVML','NDWL')")
            # arcpy.Identity_analysis("VRILyr","RSLTopenLyr","Logging_no_Date")
            # arcpy.MakeFeatureLayer_management("Logging_no_Date","log_no_Lyr","\"FID_ALLVRIfinal\" > -1")
            # no_log_dict = create_dict_from_fields("log_no_Lyr","FID_ALLVRIfinal","DISTURBANCE_START_DATE","")
            # Populate_table_withdictionary("AllVRIfinal", "LOGGING_DATE", "OBJECTID", no_log_dict)

            # calculate harvest year from Harvest Date
            # arcpy.CalculateField_management("VRILyr","HARVESTED_YEAR", "DatePart('YYYY','[HARVESTED_DATE]')")

            # Populate_table_withdictionary("AllVRIfinal", "LOGGING_DATE", "OPENING_IDOPEN", rslt_open_dict)
            # ------

            # MAKE  Intermediate COPIES before duplicates are removed
            print ('Copying to Intermediate coverage, before opening comparison...')
            for FCName in ['FTENBLKS', 'RSLTOPEN', 'RSLTFC']:
                wrkName = varName + '_' + FCName + '_wrk'
                intName = varName + '_' + FCName + '_int'
                if not arcpy.Exists(intName):
                    arcpy.CopyFeatures_management(wrkName, intName)

            # ---------------------------------------------------------
            # COMPARE OPENING IDS   - build Dict from original features (before removal of overlaps etc)
            # Collect opening id's from FTEN openings
            print ('\nCollecting OPENING_IDs')
            x = 0
            FTENDict = {}
            rows = arcpy.SearchCursor(covFTENBLKSdict)
            row = rows.next()
            # x = 0
            while row:
                if not row.isNull("OPENING_ID"):
                    FTENDict[x] = row.getValue("OPENING_ID")
                    x += 1
                row = rows.next()
            del row, rows

            # Collect opening id's from RESULTS openings
            rsltOpeningDict = {}
            rows = arcpy.SearchCursor(covRESULTOPENdict)
            row = rows.next()
            # x = 0
            while row:
                if not row.isNull("OPENING_ID"):
                    rsltOpeningDict[x] = row.getValue("OPENING_ID")
                    x += 1
                row = rows.next()
            del row, rows

            # collect existing spatial RESULTS FC opening numbers
            print ('collecting RESULTS FC openings')
            rsltFcDict = {}
            rows = arcpy.SearchCursor(covRESULTFCdict)
            row = rows.next()
            # x = 0
            while row:
                if not row.isNull("OPENING_ID"):
                    rsltFcDict[x] = row.getValue("OPENING_ID")
                    x += 1
                row = rows.next()
            del row, rows

            # collect existing vri openings *sometimes Opening id does not exist in feature so really only opennum is generated
            print ('VRI openings')
            vriOpeningDict = {}
            # vriOpenNumDict = {}
            rows = arcpy.SearchCursor(covVRIdict)
            row = rows.next()
            while row:
                if not row.isNull("OPENING_ID"):
                    vriOpeningDict[x] = row.getValue("OPENING_ID")
                    x += 1
                # open_id = row.getValue("OPENING_ID")
                # if open_id:
                #    vriOpeningDict[x] = open_id
                # map_id = row.getValue("MAP_ID")
                # open_num = row.getValue("OPENING_NUMBER")
                # if open_num:
                # vriOpenNumDict[x] = [map_id.strip().lstrip('0'), open_num.strip()]
                # x += 1
                row = rows.next()
            del row, rows

            # make different combinations of opening id dictionaries
            # Dictionary with all three
            print ('\nCreating Opening_ID dictionaries and deleting duplicates...')
            vriRsltOpenFCOpenDict = {}
            vriRsltOpenFCOpenDict.update(rsltOpeningDict)  # merge opening dictionaries
            vriRsltOpenFCOpenDict.update(rsltFcDict)
            vriRsltOpenFCOpenDict.update(vriOpeningDict)
            # populate dictionary
            vriRsltOpenDict = {}
            vriRsltOpenDict.update(vriOpeningDict)
            vriRsltOpenDict.update(rsltOpeningDict)
            vriRsltFCDict = {}
            vriRsltFCDict.update(vriOpeningDict)
            vriRsltFCDict.update(rsltFcDict)

            # delete ften cutblocks with existing spatial opening_ids in VRI/RSLT OPEN/ RSLT FC
            # print 'FTENDict', FTENDict
            # print 'rsltOpeningDict',rsltOpeningDict
            # print 'rsltFcDict', rsltFcDict
            # print 'vriOpeningDict',vriOpeningDict
            # print 'vriRsltOpenFCOpenDict', vriRsltOpenFCOpenDict
            arcpy.env.overwriteOutput = True
            print ('Deleting FTEN blocks')
            rows = arcpy.UpdateCursor(covFTENBLKS)
            row = rows.next()
            while row:
                if row.getValue("OPENING_ID") in vriRsltOpenFCOpenDict.values():
                    rows.deleteRow(row)
                row = rows.next()
            del row, rows

            # delete RESULTS openings with existing spatial opening_ids in VRI/RSLT FC. This means the block is captured in both VRI and RESULTS FC.
            print ('Deleting RESULTS Opening openings')
            rows = arcpy.UpdateCursor(covRESULTOPEN)
            row = rows.next()

            while row:
                if row.getValue("OPENING_ID") in vriRsltFCDict.values():
                    rows.deleteRow(row)

                row = rows.next()
            del row, rows

            # delete rslt FC openings with existing spatial opening_ids in VRI.  This may include reserves.
            # Note that when FC openings are integrated with VRI, reserves < 1ha are ignored.
            print ('Deleting RESULT FC openings')
            rows = arcpy.UpdateCursor(covRESULTFC)
            row = rows.next()

            while row:
                # open_id = row.getValue("OPENING_ID")
                # map_id = row.getValue("MAPSHEET")
                # open_num = row.getValue("OPENING_NUMBER")
                if row.getValue("OPENING_ID") in vriOpeningDict.values():
                    rows.deleteRow(row)

                row = rows.next()
            del row, rows

            # ---------------------------------------------------------
            # find ND features - Natural Disturbance   #??  KEEP FOR NOW, but make sure to carry over the disturbance codes
            # May tend to be smaller/less extensive, but Results FC will still track ages/dates
            # rslt_nd_dict = create_dict_from_fields(covRESULTOPENdict,"OPENING_ID","OPENING_CATEGORY_CODE","\"OPENING_CATEGORY_CODE\" in ('NDFS','NDCF','NDAML','NDVML','NDWL')")
            # deleting ND features
            # Delete_row_withdictionary(covRESULTOPEN,"OPENING_ID", rslt_nd_dict)
            # Delete_row_withdictionary(covRESULTFC,"OPENING_ID", rslt_nd_dict)
            arcpy.env.overwriteOutput = True
            ##SLIVER ELIMINATION < 1000 m sq
            print ('\nEliminating slivers ...')
            for cov in [covFTENBLKS, covRESULTOPEN, covRESULTFC]:
                tempElimLyr1 = f"{cov}_tempElimLyr1"
                tempElimLyr2 = f"{cov}_tempElimLyr2"
                
                # Rename the original dataset so that we have a backup (e.g., a_9098644_RSLTFC_wrk_del)
                arcpy.Rename_management(cov, cov + "_del")
                
                # Create a feature layer from the backup
                arcpy.MakeFeatureLayer_management(cov + "_del", tempElimLyr1)
                
                # Check how many features have Shape_AREA < 1000
                selCount = int(arcpy.GetCount_management(tempElimLyr1).getOutput(0))
                
                # If there are any features to eliminate, run the elimination tool;
                # otherwise simply copy the backup back to the original name.
                if selCount > 0:
                    arcpy.SelectLayerByAttribute_management(tempElimLyr1, "NEW_SELECTION", "Shape_AREA < 1000")
                    arcpy.Eliminate_management(tempElimLyr1, cov)
                else:
                    arcpy.CopyFeatures_management(cov + "_del", cov)
                
                print(f"Processed {cov}")
                
                # (Optional) Remove any remaining sliver features from the backup
                arcpy.MakeFeatureLayer_management(cov + "_del", tempElimLyr2)
                arcpy.SelectLayerByAttribute_management(tempElimLyr2, "NEW_SELECTION", "Shape_AREA < 1000")
                if int(arcpy.GetCount_management(tempElimLyr2).getOutput(0)) > 0:
                    arcpy.DeleteFeatures_management(tempElimLyr2)
                
                arcpy.Delete_management(tempElimLyr1)
                arcpy.Delete_management(tempElimLyr2)

            deltaTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
            print( deltaTime)
            if not arcpy.Exists(covRESULTFC):
                raise Exception("The update features dataset does not exist: " + covRESULTFC)
            else:
                print('covRESULTFC exists')
            #######--------------------------------------
            # COMBINE OPENINGS
            # Use UPDATE to spatially combine all openings  - FTENBLKS, RSLTSOPEN, RSLTSFC
            # Use VRI OPenings to erase updated features - VRI takes precedence
            # Union back with VRI

            # Hierarchy of erasing openings is as follows
            # 1: VRI Openings
            # 2: RESULTS FC openings
            # 3: RESULTS Open openings
            # 4: FTEN BLocks

            arcpy.env.overwriteOutput = True
                        # Use UPDATE so that common fields are kept.
            print ('Combining all Openings..')
            arcpy.Update_analysis(covFTENBLKS+'_del', covRESULTOPEN+'_del', 'tempU_1', "BORDERS")
            print('update 1 compleated ')
            if arcpy.Exists('tempU_2'):
                print('temp2 exists')
            if arcpy.Exists('tempU_22'):
                arcpy.Delete_management('tempU_22')
                print('existing temp22 deleted')
            if arcpy.Exists(covRESULTFC):
                print('covRESULTFC exists')
            if not arcpy.Exists(covRESULTFC):
                raise Exception("The update features dataset does not exist: " + covRESULTFC)
            arcpy.Update_analysis('tempU_1', covRESULTFC, 'tempU_22', "BORDERS")

            # DropFields
            keepList = ['VRI2_SOURCE', 'VRI2_OPENING_ID', 'VRI2_ATT_SOURCE_DISTURB', 'VRI2_ATT_SOURCE_SPECIES',
                        'VRI2_DISTURB_CODE', 'VRI2_DISTURB_DATE', 'VRI2_DISTURB_YR', \
                        'VRI2_HARVESTED', 'VRI2_SITE_INDEX', 'VRI2_SPECIES', 'VRI2_SPECIES_PERCENT', 'VRI2_AGE', 'VRI2_HEIGHT', \
                        'VRI2_SI_ESTIMATED', 'VRI2_SPECIES_ESTIMATED', 'VRI2_AGE_ESTIMATED', 'VRI2_HEIGHT_ESTIMATED',
                        'OBJECTID', 'GEOMETRY_Length', 'EOMETRY_AREA', 'GEOMETRY', \
                        'Shape', 'Shape_Area', 'Shape_Length', 'SHAPE', 'SHAPE_Length', 'SHAPE_Area','OBJECTID_1']
            for field in [f.name for f in arcpy.ListFields('tempU_22')]:
                if field not in keepList:
                    arcpy.DeleteField_management('tempU_22', field)
            # arcpy.Update_analysis('tempU_2', 'VRI_VEG_R1_POLY_OPENINGS', 'temp_ALL_openings_resultant', "BORDERS") #THis is just use for checking results

            # Erase with VRI where there is some kind of opening. Those with an actual Opening ID already in VRI should have been filtered out already.
            # This assumes that the VRI 'Openings' have better data than any remaining overlapping openings from FTEN or RSLTS.
            arcpy.MakeFeatureLayer_management(varName + '_VEG_R1_POLY_OPENINGS', "VRIopenidLyr")  # "OPENING_ID is not NULL")
            # OPENING_ID is not NULL and VRI2_AGE_ESTIMATED is not null?
            arcpy.Erase_analysis('tempU_22', 'VRIopenidLyr', "temp_Openings_erased")
            arcpy.Delete_management('VRIopenidLyr')

            # Delete Slivers < 1 ha
            arcpy.MakeFeatureLayer_management('temp_Openings_erased', 'tempELyr')
            arcpy.SelectLayerByAttribute_management('tempELyr', "NEW_SELECTION", "Shape_AREA < 10000")
            if int(arcpy.GetCount_management('tempElyr').getOutput(0)) > 0:
                arcpy.DeleteFeatures_management('tempELyr')
            arcpy.Delete_management('tempELyr')

            # Union with VRI  - note field name changes
            # arcpy.Union_analysis (["VRI_VEG_R1_POLY_OPENINGS", "temp_Openings_erased"], "ALL_openings_resultant")
            # arcpy.Union_analysis ([covVRI, "tempU_2"], "VRI2_resultant_U2")

            vri2Result = "VRI2_resultant_" + varName + "_" + stimePeriod
            # if arcpy.Exists(vri2Result):
            # arcpy.Delete_management(vri2Result)
            print ('Unioning to get final resultant...')
            arcpy.Union_analysis([covVRI, "temp_Openings_erased"], vri2Result)

            # 1 - Where VRI Opening, and no other opening - leave attributes as is
            # (VRI2_SOURCE_1 is null or VRI2_SOURCE_1 = '') and VRI2_HARVESTED is not null
            # In general, if RSLTSFC opening is already in VRI, then ignore, even though it may have more current species info by polygon unit

            # 2 - Where Opening, but not VRI - update with new Opening info
            # (VRI2_SOURCE_1 is not null and VRI2_SOURCE_1 <> '') and VRI2_HARVESTED is null
            # Calc code for Reserves/Natural - but use original VRI attributes for age, height, etc. as available
            print ('\nUpdating new Opening attributes...')
            arcpy.MakeFeatureLayer_management(vri2Result, "VRI2Lyr",
                                            "VRI2_SOURCE_1 is not null and VRI2_SOURCE_1 <> '' and VRI2_DISTURB_CODE_1 = 'Reserve or Natural'")
            arcpy.CalculateField_management('VRI2Lyr', 'VRI2_DISTURB_CODE', "!VRI2_DISTURB_CODE_1!", "PYTHON_9.3", "")
            arcpy.Delete_management('VRI2Lyr')

            # Update Fields for openings that are not Reserves/Natural
            arcpy.MakeFeatureLayer_management(vri2Result, "VRI2Lyr",
                                            "(VRI2_SOURCE_1 is not null and VRI2_SOURCE_1 <> '') and (VRI2_DISTURB_CODE_1 <> 'Reserve or Natural' and VRI2_DISTURB_CODE_1 is not null and VRI2_DISTURB_CODE_1 <> '')")
            updFieldList = ['VRI2_SOURCE', 'VRI2_OPENING_ID', 'VRI2_ATT_SOURCE_DISTURB', 'VRI2_ATT_SOURCE_SPECIES',
                            'VRI2_DISTURB_CODE', 'VRI2_DISTURB_DATE', 'VRI2_DISTURB_YR', \
                            'VRI2_HARVESTED', 'VRI2_SITE_INDEX', 'VRI2_SPECIES', 'VRI2_SPECIES_PERCENT', 'VRI2_AGE',
                            'VRI2_HEIGHT', \
                            'VRI2_SI_ESTIMATED', 'VRI2_SPECIES_ESTIMATED', 'VRI2_AGE_ESTIMATED', 'VRI2_HEIGHT_ESTIMATED']
            for field in updFieldList:
                # Do not calculate if Site Index and Species are null - do not want to overwrite if we know this from VRI
                if field in ['VRI2_SITE_INDEX', 'VRI2_SPECIES']:
                    arcpy.SelectLayerByAttribute_management('VRI2Lyr', "NEW_SELECTION", "" + field + "_1 is not NULL")
                    count = int(arcpy.GetCount_management('VRI2Lyr').getOutput(0))
                    print ('Sub count Not Null:  '), field, count
                arcpy.CalculateField_management('VRI2Lyr', field, "!" + field + "_1!", "PYTHON_9.3", "")
                arcpy.SelectLayerByAttribute_management('VRI2Lyr', "CLEAR_SELECTION")

                # Use Est Site Index and Est species to fill in blanks
            # FOR New HARVESTED/OPENINGS only  - see MakeFeature query above
            arcpy.SelectLayerByAttribute_management("VRI2Lyr", "NEW_SELECTION",
                                                    "VRI2_SITE_INDEX is null and EST_SITE_INDEX is not null ")
            arcpy.CalculateField_management('VRI2Lyr', "VRI2_SITE_INDEX", "!EST_SITE_INDEX!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('VRI2Lyr', 'VRI2_SI_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("VRI2Lyr", "NEW_SELECTION",
                                                    "VRI2_SPECIES is null and EST_SITE_INDEX_SPECIES_CD is not null ")
            arcpy.CalculateField_management('VRI2Lyr', "VRI2_SPECIES", "!EST_SITE_INDEX_SPECIES_CD!", "PYTHON_9.3", "")
            arcpy.CalculateField_management('VRI2Lyr', 'VRI2_SPECIES_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.Delete_management('VRI2Lyr')

            # ----------------------
            # Fill in Missing Heights for disturbance polygons
            # Set up Height calc based on site index and species (where known) - Provincial Site Index Curve formulas
            # FD First, then all else as Pine?  Or by species if known, then all else by pine
            # VB Log function is by default, the Natural Logarithm

            PLheightCalc = """1.3+([VRI2_SITE_INDEX]-1.3)*((1 + Exp(7.815 - 1.285 * Log(50) - 1.007 *Log([VRI2_SITE_INDEX] -1.3))) /  (1 + Exp(7.815 - 1.285 * Log([VRI2_EST_AGE_BH]) - 1.007 * Log([VRI2_SITE_INDEX] -1.3))))"""
            FDheightCalc = """1.3+([VRI2_SITE_INDEX]-1.3)*((1 + Exp(5.78 - 1.15 * Log(50) - 0.238 *Log([VRI2_SITE_INDEX] -1.3))) /  (1 + Exp(5.78 - 1.15 * Log([VRI2_EST_AGE_BH]) - 0.238 *Log([VRI2_SITE_INDEX] -1.3))))"""

            # Estimated breast height age
            # A - Age at breast height is estimated as Age - 7 years (pers comm - Bernie Peschke).  But Age cannot be < 0
            vri2Result = "VRI2_resultant_" + varName + "_" + stimePeriod
            if not arcpy.ListFields(vri2Result, 'VRI2_EST_AGE_BH'):
                arcpy.AddField_management(vri2Result, "VRI2_EST_AGE_BH", "SHORT")

            print ('\nCalculating estimated Height for applicable features...')
            arcpy.MakeFeatureLayer_management(vri2Result, "VRI2LyrH",
                                            "(VRI2_HARVESTED = 'YES' or VRI2_SOURCE <> 'VRI') and (VRI2_AGE > 0 and VRI2_HEIGHT is null)")
            arcpy.CalculateField_management('VRI2LyrH', 'VRI2_EST_AGE_BH', "!VRI2_AGE! - 7", "PYTHON_9.3", "")
            # If age drops below 0, calc to 1
            arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION", "VRI2_EST_AGE_BH < 1")
            arcpy.CalculateField_management('VRI2LyrH', 'VRI2_EST_AGE_BH', "1", "PYTHON_9.3", "")

            # If Site Index not known??  Use average SI by species within a certain area (eg. LU, watershed, buffer distance) - Summary Stats? Or nearest neighbour - Near Analysis?
            # Mean for the Area/TSA?
            # Start with a very rough guess of Site Index = 15 .  THis was based on looking at the average SI for Merritt(15), Okanagan (15), Lillooet (12) and Kamloops TSAs (15)
            # If Site_Index not known or already estimated, use a rough guess of 15
            arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION", "VRI2_SITE_INDEX is null")
            arcpy.CalculateField_management('VRI2LyrH', "VRI2_SITE_INDEX", "15", "PYTHON_9.3", "")
            arcpy.CalculateField_management('VRI2LyrH', 'VRI2_SI_ESTIMATED', "\"YES15\"", "PYTHON_9.3", "")

            # If Site Index is known, or newly calcuated above , calc Height for selected layer
            # FOR NOW, USE PL HEIGHT formula from Site Index Curves, and assume 7 years to breast height.
            # THis could be refined by species later on.
            # If species is not known, could assume based on the usual planted species, by BEC (see table from Bernie)

            ## WARNING!:  The Geoprocessor is very inconsistent with how it deals with the Logarithm calc and
            ## often gives an error message!!  The solution is to log off and back on again and try to re-run the script, or calculate manually in ArcMap!
            arcpy.env.overwriteOutput = True
            print( 'calculating VRI2_HEIGHT...')
            arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION", "VRI2_SITE_INDEX > 0")
            # arcpy.CalculateField_management('VRI2LyrH','VRI2_HEIGHT', PLheightCalc,"VB")
            # print 'test'
            # arcpy.CalculateField_management('VRI2LyrH','VRI2_HEIGHT', "Log([VRI2_SITE_INDEX])","VB")
            # print 'actual'
            arcpy.CalculateField_management("VRI2LyrH", "VRI2_HEIGHT","1.3+(!VRI2_SITE_INDEX!-1.3)*((1 + math.exp(7.815 - 1.285 * math.log(50) - 1.007 * math.log(max(!VRI2_SITE_INDEX! - 1.3, 0.0001)))) /  (1 + math.exp(7.815 - 1.285 * math.log(max(!VRI2_EST_AGE_BH!, 0.0001)) - 1.007 * math.log(max(!VRI2_SITE_INDEX! - 1.3, 0.0001)))))",
                                            "PYTHON_9.3"
)
            # """1.3+([VRI2_SITE_INDEX]-1.3)*((1 + Exp(7.815 - 1.285 * Log(50) - 1.007 *Log([VRI2_SITE_INDEX] -1.3))) /  (1 + Exp(7.815 - 1.285 * Log([VRI2_EST_AGE_BH]) - 1.007 * Log([VRI2_SITE_INDEX] -1.3))))"""
            arcpy.CalculateField_management('VRI2LyrH', 'VRI2_HEIGHT_ESTIMATED', "\"YES\"", "PYTHON_9.3", "")
            arcpy.Delete_management('VRI2LyrH')
            print ('Done Height calc - CHECK RESULTS')

            # Refine Where Age < 7
            # Age 1-2  gets 0.2 m,  3-4 gets  0.4,  5-6 0.8, 7 = 1.2  Based on Lodgepole Pine with SI = 15
            print (' Revising Heights for Estimated Age < 7 ...')
            arcpy.MakeFeatureLayer_management(vri2Result, "VRI2LyrH",
                                            "(VRI2_HARVESTED = 'YES' or VRI2_SOURCE <> 'VRI') and VRI2_AGE > 0")
            arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION",
                                                    "VRI2_HEIGHT_ESTIMATED = 'YES' and (VRI2_AGE > 0 and VRI2_AGE < 3)")
            arcpy.CalculateField_management("VRI2LyrH", "VRI2_HEIGHT", "0.2", "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION",
                                                    "VRI2_HEIGHT_ESTIMATED = 'YES' and (VRI2_AGE >=3 and VRI2_AGE < 5)")
            arcpy.CalculateField_management("VRI2LyrH", "VRI2_HEIGHT", "0.4", "PYTHON_9.3", "")
            # Fixed coding age error VRI2_AGE >=5 and VRI2_AGE < 8 sb  6
            # arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION", "VRI2_HEIGHT_ESTIMATED = 'YES' and (VRI2_AGE >=5 and VRI2_AGE < 8)")
            arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION",
                                                    "VRI2_HEIGHT_ESTIMATED = 'YES' and (VRI2_AGE >=5 and VRI2_AGE < 6)")
            arcpy.CalculateField_management("VRI2LyrH", "VRI2_HEIGHT", "0.8", "PYTHON_9.3", "")
            arcpy.SelectLayerByAttribute_management("VRI2LyrH", "NEW_SELECTION",
                                                    "VRI2_HEIGHT_ESTIMATED = 'YES' and (VRI2_AGE = 7)")
            arcpy.CalculateField_management("VRI2LyrH", "VRI2_HEIGHT", "1.2", "PYTHON_9.3", "")
            arcpy.Delete_management('VRI2LyrH')

            # DELETE UNNECCESSARY FIELDS
            # keep fields
            '''
                    delFieldList = ['FID_temp_Openings_erased','VRI2_SOURCE_1','VRI2_OPENING_ID_1','VRI2_ATT_SOURCE_DISTURB_1','VRI2_ATT_SOURCE_SPECIES_1','VRI2_DISTURB_CODE_1','VRI2_DISTURB_DATE_1','VRI2_DISTURB_YR_1',\
                                'VRI2_HARVESTED_1','VRI2_SITE_INDEX_1','VRI2_SPECIES_1','VRI2_SPECIES_PERCENT_1','VRI2_AGE_1','VRI2_HEIGHT_1',\
                                'VRI2_SI_ESTIMATED_1','VRI2_SPECIES_ESTIMATED_1','VRI2_AGE_ESTIMATED_1','VRI2_HEIGHT_ESTIMATED_1','VRI2_EST_AGE_BH','VRI2_CROWN_CLOSURE']
                    for field in delFieldList:
                        arcpy.DeleteField_management(vri2Result, field)
                    '''
            print ("\nAdd Run Date..")
            arcpy.AddField_management(vri2Result, "VRI2_RUN_DATE", "DATE")
            arcpy.CalculateField_management(vri2Result, 'VRI2_RUN_DATE', '"' + today + '"', "PYTHON_9.3", "")

            # Make list of intermediate files to delete
            print ('Cleaning up files...')
            delList = ['tempU_1', 'FTENBLKSduplicates', 'RSLTFCduplicates', 'RSLTOPENduplicates', 'temp_Openings_erased',
                    'temp_RSLTOPEN_SORT', \
                    varName + '_FTENBLKS_wrk_del', varName + '_RSLTFC_wrk_del', varName + '_RSLTOPEN_wrk_del']

            for item in delList:
                if arcpy.Exists(item):
                    arcpy.Delete_management(item)

            # Dissolve on Harvested only
            vri2HarvestResult = "VRI2_Harvested_" + varName + "_" + stimePeriod
            if not arcpy.Exists(vri2HarvestResult):
                print ('Dissolving VRI2 Resultant for Harvesting: ' + varName)
                arcpy.MakeFeatureLayer_management(vri2Result, "VRI2HarvestLyr", "VRI2_HARVESTED = 'YES'")
                arcpy.Dissolve_management('VRI2HarvestLyr', vri2HarvestResult, 'VRI2_SOURCE;VRI2_HARVESTED;VRI2_DISTURB_YR',
                                        "#", "SINGLE_PART", "DISSOLVE_LINES")
                arcpy.Delete_management('VRI2HarvestLyr')

            print ('\n Done Calculations - CHECK RESULTS')

        '''
        #THIS IS ONLY REQUIRED IF AOI was split into pieces for processing      
        #merge all the files together.

        if sCreateMerge == '1':
            arcpy.AddMessage ('All features are being merged together')
            mergestring = ''
            for aoiArea in aoiList:
                gridin = "VRI2_resultant_"+aoiArea    #aoiArea + "_VRIover"
                arcpy.AddMessage (str(gridin))
                count = int(arcpy.GetCount_management(gridin).getOutput(0))
                if count > 0:
                    mergestring = mergestring + ";" + gridin
            inputs = mergestring[1:]
            arcpy.AddMessage (str(inputs))
            arcpy.Merge_management(inputs,"AllVRI_Merge")                              

        #THIS SHOULDN'T BE NECESSARY, as overlaps for each input were removed after initial data extraction
        #arcpy.env.workspace = workspace
        print '\nChecking final dataset for overlaps..'
        obj = overlapmod_py3.featureClass(vri2Result)  #("AllVRI_Merge")
        obj.findoverlap(sAOIfeat,"AllVRI")#makes with a 'fixed' prefix on the end
        arcpy.Rename_management("AllVRIfixed","AllVRIfinal")
        '''

        print ('CHECK RESULTS!')
        print ('\nTSA results can be combined manually using MERGE..')



        # cleanup(sExtractLoc,input_data)

        # ---------------------------------------------------------------------------
        print ('\nSCRIPT COMPLETE')
        totalTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
        print ('\n This script took ' + totalTime + ' to run.')
