"""
    Script Name:  CEA_Watershed_analysis
    ArcGIS Version. 10.1
    Author:  Graham MacGregor, Sasha Lees, Gail Smith
    Date:    06-Nov-2013
    Purpose:   To prepare watershed indicator scores for the watersheds of interest.
    Assumptions:   You must have a master watershed dataset which includes fields for:
        Assessment Unit/Watershed Group
        Watershed Unit/Unique reporting ID
        Watershed Name (may not be unique)
        Watershed Type:  eg. Super Watershed, Large Watershed, Watershed, Basin, Sub-basin, residual
        Total watershed area

    Arguments:

    Outputs:
    Dependencies:

    History:
    23-May-2014 salees
    updated ECA section to include MPB criteria

    11-Jun-2014 salees
    Added Coal Lease score -  % of watershed unit that is in coal lease

    2-Jul-2014 salees
        Updated to point to latest VRI2 input.  Some calcs adjusted to use new attribute names/values.

    21-Dec-2021 nbouvier
        Updated to remove hard coding for Shape_Area, Shape_Length fields - uses module to determine field.
    
    2023 cfolkers
        converted to python 3, added smarts to detect if layers are present, added loop go through each scale of watershed, probably more stuff

"""

import arcpy, os, sys, time, datetime, string
from arcpy.sa import Reclassify, RemapRange
arcpy.env.overwriteOutput = True   # Overwrite output if it already exists
try:
    arcpy.CheckOutExtension("Spatial")
    from arcpy.sa import *
    from arcpy.da import *
except:
    arcpy.AddError("Spatial Extension could not be checked out")
    os.sys.exit(0)

class wtrshd_analysis:
    def __init__(self, wtrshdname, Bfold):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold
    
        #user Variables
        WatershedName=self.wtrshdname
        BaseFolder=self.Bfold

        # AOItype='_Named_Watershed'

        # NamedWatershed= WatershedName.replace(' ','_')
        # data_name =NamedWatershed+AOItype  #'Hominka_River_WAU' 
        # print(inputfolder)
        # masterWS = os.path.join(inputfolder,r'WatershedData_Omineca.gdb', data_name)        #this one 
        # print(masterWS)
        # # uniqueValues = [data_name] #this one
        # # data_name = 'Hominka_River_Named_Watershed'
        # input_gdb=os.path.join(inputfolder,(NamedWatershed+'_Input_Data.gdb'))

        # masterWS=r'\\142.27.147.234\spatialfiles2work\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\1_WHPOR_Analyses\2023\6_Hominka\1_SpatialData\1_InputData\Hominka_River_Input_Data.gdb\Hominka_River_Named_Watershed'
        # stimePeriod = '2023'
        datevar = time.strftime("%Y%m%d")  # Date in the format of year, month, day  eg. 20131121
        inputfolder=os.path.join(BaseFolder,r'1_SpatialData\1_InputData')
        str_lkup=r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\VRI_BNDY.gdb\StreamWght_lookup'
        CEAfolder=os.path.join(BaseFolder,r'1_SpatialData\4_CEA_Watershed_Analysis')
        # sOutputLoc =os.path.join(CEAfolder,'stage')
        sOutputLoc = os.path.join(CEAfolder,r'Ouput')
        reportDir = os.path.join(sOutputLoc,r'reports')
        csv=os.path.join(CEAfolder,r'Watershed_Inputs_List_V1.2.csv')
        prj_file=os.path.join(sOutputLoc,r'PCS_Albers.prj')
        mapsheet_file= r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\Maps50K.gdb\WHSE_BASEMAPPING_NTS_50K_GRID'

        #get all watershed levels
        arcpy.env.workspace=os.path.join(inputfolder,r'WatershedData_Omineca.gdb')
        All_wtrshds=arcpy.ListFeatureClasses()
        print('==========Watersheds to process==========')
        print(All_wtrshds)
        print('==========Watersheds to process==========')
            




        # ------------------------------------------------------------------------------
        # Start Time and date
        startTime = time.time()
        deltaTime = time.time()
        START_TIME = time.ctime(time.time())
        print ('   Starting : ', START_TIME)
        print (deltaTime)
        print ("Running against: {}".format(sys.version))

        # -------------------------------------------------------------------------------
        # Add method utility paths here
        # Add xl utility and CEA watershed Module
        # print ('\nImporting CEA Module...')
        # ceaMod = r'W:\for\RNI\RNI\General_User_Data\CFolkers\Scripts\Python\WHPOR\CEA_Module_NB.py'
        # if ceaMod not in sys.path:
        #     sys.path.append(ceaMod)

        import CEA_Module_NB

        # -------------------------------------------------------------------------------
        # Variables for FGDB Name & inputs
        analysisVal = 'Hazard'
        # stimePeriod = '2020'
        datevar = time.strftime("%Y%m%d")  # Date in the format of year, month, day  eg. 20131121
        datevar = '20220329'


        # Set Data Source Variables & the data connection to the data warehouse (to use, you must have sde connections made)
        sDATAconnect = r"Database Connections\\BCGW.sde"  # BCGW data connection
        BCGW = r'Database Connections\BCGW4Scripting.sde'  # BCGW4Scripting uses embedded passwords.

        # -------------------------------------------------------------------------------
        # The output location for the Area of Interest/Watershed group FGDB
        # AOI is initially based on Watershed Assessment Unit/Group
        # sOutputLoc = os.path.join(CEAfolder,r'Ouput')
        # r"N:\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\1_WHPOR_Analyses\2023\6_Hominka\1_SpatialData\4_CEA_Watershed_Analysis\Output"
        if not os.path.exists(sOutputLoc):
            print ('The output path does not exist - creating directory ' + sOutputLoc)
            os.makedirs(sOutputLoc)
        else:
            print(' Directory already exists')
        print ('\n...File Geodatabase will be written to:  ' + sOutputLoc)

        reportDir = os.path.join(CEAfolder,r'Reports')
        # r"N:\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\1_WHPOR_Analyses\2023\6_Hominka\1_SpatialData\4_CEA_Watershed_Analysis\Reports"
        if not os.path.exists(reportDir):
            print ('The Reports path does not exist - creating directory ' + reportDir)
            os.makedirs(reportDir)
        print ('...Reports will be written to:  '+reportDir + '\n')
            

        # ############################    START OF FUNCTIONS/METHODS     #############################


        def __PrintTime(delta_time_in):
            """
            Print Total Time and Change in Time
            :param: delta_time_in
            :return: deltaTime
            """
            totalTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
            deltaTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - delta_time_in))
            print ('Time since last time: ', deltaTime)
            print ('Total Time so far: ', totalTime)
            return deltaTime


        def __AddRunDate(in_feats, date_fld):
            """
            Add Run Date field to input layer and calculate date
            :param in_feats:
            :param date_fld:
            :return:
            """
            if not arcpy.ListFields(in_feats, date_fld):
                print ('\nAdding Field ' + date_fld)
                arcpy.AddField_management(in_feats, date_fld, "DATE", "", "", "", "", "NULLABLE", "NON_REQUIRED")
            else:
                print ('\nDate Field' + date_fld + 'already exists...Skipping AddField...')
            
            print ('\nCalculating Date to today for ' + date_fld)
            arcpy.CalculateField_management(in_feats, date_fld, "datetime.datetime.now( )", "PYTHON3")


        def create_fgdb():
            """
            Create File Geodatabase for AOI Assessment Unit
            :return:
            """
            print(sOutputLoc)
            print(setOutputFGDB)
            print ('\nChecking for FGDB ...')
            if arcpy.Exists(fgdbLoc):
                print (setOutputFGDB + 'already exists...\n')
                
            else:
                print ('Creating FGDB '+setOutputFGDB)
                arcpy.CreateFileGDB_management(sOutputLoc, setOutputFGDB)
                


        def create_aoi_bnd(query):
            """
            Create AOI boundary from Watershed Assessment Units
            :param query:
            :return:
            """
            arcpy.env.workspace = fgdbLoc
            print ('\nChecking for AOI Watershed boundaries ...')
            
            '''
            #create watersheds based on an area of interest
            objdata = CEA_Module.extractData()
            objdata.extract_by_Location(wsBnd, wsNested, "Watersheds_in_AOI")
            '''
            
            if not arcpy.Exists('Watersheds_in_AOI'):
                print ('\nCopying selected Assessment Unit Watersheds')
                arcpy.MakeFeatureLayer_management(masterWS, 'featLyr', query)
                count = int(arcpy.GetCount_management('featLyr').getOutput(0)) 
                print ('Watershed count:', count)
                if count == 0:
                    print ('!! Zero features for Assesment Units.  Quitting...')
                    # sys.exit()
                    
                # Copy features
                arcpy.CopyFeatures_management('featLyr', 'Watersheds_in_AOI')
                arcpy.Delete_management('featLyr')
            if not arcpy.Exists('Watersheds_bnd'):
                # Create outer boundary
                print ('Dissolving to create outer boundary')
                arcpy.Dissolve_management("Watersheds_in_AOI", "Watersheds_bnd")


        def create_stats_table():
            """
            Create Master table for collecting indicator scores
            :return: 
            """
            # make main watershed table creates table which watershed stats can be linked to.
            print ('\nChecking for Master STATS TABLE ...')
            if arcpy.Exists('Watershed_STATS_TABLE'):
                arcpy.Delete_management('Watershed_STATS_TABLE')
            if not arcpy.Exists('Watershed_STATS_TABLE'):
                print ('\n Creating Master Watershed_STATS_TABLE')
                arcpy.Frequency_analysis(wsNested, 'Watershed_STATS_TABLE', [wsUnitFld, wsLinkFld, wsNameFld, wsTypeFld,
                                                                            wsAreaHa, wsAreaKM2, wsAreaM2])
            else:
                print ('\n Master Watershed_STATS_TABLE already exists'   ) 


        def data_prep():
            """
            Data Extraction and Preparation  (Sasha Lees)
            Read input CSV list in the form of:
            VariableName   DataSource    SourceType OutfileName FinalFileName  dissolve_flag    Subtype_field Feature Query
            'na' is used in csv where no value or action is required.
            the CSV list should NOT include header fields
            Clip source data to the AOI, and dissolve or merge as necessary
            :return: 
            """

            # Create python list from CSV
            print ('\nData Prep: Processing input data list from CSV...')
            # inputcsv = r'T:\WHPOR\Stage\Watershed_Inputs_list_2020_master.csv'
            inputcsv = csv
            # Filehandle - open for reading
            filehand = open(inputcsv, 'r')    
            # Create empty list
            out_list = []
            
            for line in filehand:
                line = line.replace('\n', '')    # replace carriage return
                line_list = line.split(',')   # creates a list from the first line
                out_list.append(line_list)   # appends the list into a list of lists
            filehand.close()
            print (out_list)

            # Check for 'Source' FeatureDataset in GDB
            arcpy.env.workspace = fgdbLoc
            if not arcpy.Exists('source'):
                print('\nCreating FeatureDataset called: source')
                arcpy.env.XYTolerance = "0.01 Meters"
                arcpy.env.ZTolerance = "0.01 Meters"
                prj = r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\PCS_Albers.prj'
                arcpy.CreateFeatureDataset_management(fgdbLoc, 'source', prj)
            else:
                print ('\nsource FeatureDataset already exists.')
            
            # ---------------------------------------
            # Loop for each datasource in python list
            # ---------------------------------------
            arcpy.env.workspace = os.path.join(fgdbLoc, 'source')
            for inputStruct in out_list:      # for each input list do the loop
                var_name = inputStruct[0]
                print ('\nNow running:  ' + var_name)
                src_feats = inputStruct[1]
                src_type = inputStruct[2]
                out_feats = inputStruct[3]
                final_feats = inputStruct[4]
                dissolve_flag = inputStruct[5]
                type_field = inputStruct[6]
                f_query = inputStruct[7]
                
            

                # SET DATA SOURCES based on criteria in CSV and add to dataSourceDict.
                print ('Adding to dataSourceDict')
                if final_feats !='na':
                    if not var_name in dataSourceDict:
                    # if not dataSourceDict.has_key(var_name):
                        dataSourceDict[var_name] = fgdbLoc + '\\source\\' + final_feats
                elif out_feats == 'na':
                    if not var_name in dataSourceDict:
                    # if not dataSourceDict.has_key(var_name):
                        dataSourceDict[var_name] = src_feats

                if src_type == 'BCGW':
                    src_feats = os.path.join(BCGW, src_feats)
                # else:    #if a local file path
                #  src_feats = r'"'+ src_feats+'"'
                # print src_feats
                    
                # ---------------------------------------
                # Clip data list if out_feats not 'na'
                # Use layer query if f_query not 'na'
                # ---------------------------------------
                if out_feats != 'na':
                    # if arcpy.Exists(out_feats):
                    #   arcpy.Delete_management(out_feats)
                    if not arcpy.Exists(out_feats):
                        # make feature layer
                        if f_query == 'na' or int(arcpy.management.GetCount(src_feats)[0]) ==0:
                            print ('...no layer query required...')
                            arcpy.MakeFeatureLayer_management(src_feats, 'tempLyr')
                        else:
                            print ('...Executing layer query...'+f_query)
                            arcpy.MakeFeatureLayer_management(src_feats, 'tempLyr', f_query)
                        arcpy.SelectLayerByLocation_management('tempLyr', "INTERSECT", wsBnd)
                        arcpy.CopyFeatures_management('tempLyr', 'interimData_out')
                        arcpy.RepairGeometry_management('interimData_out')
                        print ('...Repaired Geometry1...')

                        # Clipping to AOI
                        print ('...Clipping Feature Layer...')
                        arcpy.Clip_analysis('interimData_out', wsBnd, out_feats)
                        count = int(arcpy.GetCount_management(out_feats).getOutput(0)) 
                        print (out_feats, ' count:', count)
                        if count == 0:
                            print ('!! Zero features for '+out_feats )
                        
                        # Dissolve if required
                        # This is a general dissolve to remove potential feature overlaps or to simplify features
                        # Default to dissolve on all fields, assuming no fields are required.
                        # Could use type_field if a field is required.
                        if dissolve_flag == 'dissolve' and int(arcpy.management.GetCount(src_feats)[0]) ==0:
                            print ('...no dissolve required...')
                        
                        if dissolve_flag == 'dissolve' and int(arcpy.management.GetCount(src_feats)[0]) >0:  # and count > 0:
                            print ('...Dissolving data...')
                            arcpy.Dissolve_management(out_feats, out_feats+'_diss', [type_field], "", "SINGLE_PART")
                        
                        print ('Done processing ' + out_feats + '\n')
                        arcpy.Delete_management('tempLyr')
                        if arcpy.Exists('interimData_out'):
                            arcpy.Delete_management('interimData_out')
                    else:
                        print ('Data already exists for', out_feats)
                else:
                    print ('No Clipping required....using alternate data source')
                    
            # ---------------------------------------
            # Merge Datasets for waterbodies and for Grazing and Wildfires(Burns)
            # ----------------------------------------

            arcpy.env.workspace = os.path.join(fgdbLoc, 'source')

            if not arcpy.Exists('AllOpenWater'):
                print ('\nUnioning and dissolving Lakes, Wetlands, and Manmade Waterbodies to create AllOpenWater...')
                arcpy.Union_analysis(["FWA_Lakes", "FWA_Wetlands"], "temp_water", "ONLY_FID")   #, "FWA_Manmade_Wtrbds" removed
                arcpy.Dissolve_management('temp_water', 'AllOpenWater', "", "", "SINGLE_PART")
                arcpy.Delete_management('temp_water')

            if not arcpy.Exists('AllGrazing'):
                arcpy.conversion.FeatureClassToFeatureClass('FTEN_Grazing', f"{fgdbLoc}/source", 'AllGrazing')

                # print ('\nUnioning and dissolving FTEN and Tantalis Grazing Tenures to create AllGrazing...')
                # arcpy.Union_analysis(["FTEN_Grazing"], "temp_grazing", "ONLY_FID")         #, "TA_Grazing_diss"
                # arcpy.Dissolve_management('temp_grazing', 'AllGrazing', "", "", "SINGLE_PART")
                # arcpy.Delete_management('temp_grazing')
                
            # # Added section for wildfires less than 25 years old
            # if not arcpy.Exists('AllBurns25'):
            #     print '\nUnioning and dissolving Historical and Current Wildfires...'
            #     arcpy.Union_analysis(["Burn_Hist" ], "temp_burn")       #"Burn_Curr_diss"
            #     arcpy.MakeFeatureLayer_management("temp_burn", "temp_burnLyr")
            #     arcpy.SelectLayerByAttribute_management('temp_burnLyr', "NEW_SELECTION", "FIRE_YEAR != 0")
            #     arcpy.CalculateField_management('temp_burnLyr', "FIRE_YEAR", "!FIRE_YEAR!", "PYTHON3", "")
            #     arcpy.Dissolve_management('temp_burn', 'AllBurns25', "FIRE_YEAR", "", "SINGLE_PART")
            #     arcpy.Delete_management('temp_burn')       
            
            if not arcpy.Exists('Private_IR'):
                print ('\n Unioning Private and IR ...')
                if arcpy.Exists("IR_CLAB_diss") and arcpy.Exists("ICF_Private") :
                    arcpy.Union_analysis(["ICF_Private", "IR_CLAB_diss"], "Private_IR")
                else: 
                    print('IR CLaB DISS does not exist')
                    arcpy.Union_analysis(["ICF_Private", "IR_CLAB"], "Private_IR")
            
            dataSourceDict['PrivIR'] = fgdbLoc + '\\source\\Private_IR'

            print ('\n Copied Roads & ROW ...')
                
            print ('...DONE data preparation.')
            __PrintTime(deltaTime)
            
            return dataSourceDict
            

        def create_slope():
            """
            Module for extracting grid slopes and creating H50 and H70 Slope feature classes  (Graham, Sasha)
            :return: 
            """
            print ('\nStarting create_slope ...' )
            arcpy.env.workspace = fgdbLoc
            # if not arcpy.Exists("SLOPE_GRID"):
            #     raise FileNotFoundError("Input raster 'SLOPE_GRID' does not exist.")
            if not arcpy.Exists(fgdbLoc + "\\slope60_poly"):
                arcpy.env.workspace = fgdbLoc
                watershed_aoi_bnd = "Watersheds_bnd"
                # initiate grid class
                obj = CEA_Module_NB.gridClass(BaseFolder)
                # find geometry envelope
                envelope = obj.get_geom_envelope(watershed_aoi_bnd)
                print (envelope)
                # generate slope classes #specify slope source data location
                gridslopesource = (datasource_dict['Slope'])
                print (gridslopesource)
                # extract slope envelope based on AOI envelope string
                # obj.extractGrid(gridslopesource, "SLOPE_GRID", envelope)  # extracts slope for area of interest
                arcpy.management.Clip(in_raster=gridslopesource, out_raster="SLOPE_GRID", in_template_dataset=watershed_aoi_bnd, 
                                      nodata_value="0", clipping_geometry="ClippingGeometry")
                
                # reclass grid h50 slope grid
                # reclassrange = RemapRange([[0,50,0],[50,9999,1]]) #"0.000000 50 0;50 9999 1"
                # # obj.categorizeGrid("SLOPE_GRID", reclassrange, "GridSlope_50")  # makes steep slopes
                # #arcpy.Reclassify_3d(inGrid, "VALUE", reclassrange, outputName, "DATA")
                # Reclassify("SLOPE_GRID", reclassrange, "GridSlope_50")
                reclass_range = RemapRange([[0, 50, 0], [50, 9999, 1]])
                grid_slope_50 = Reclassify("SLOPE_GRID", "Value", reclass_range)
                grid_slope_50.save("GridSlope_50")
                #  reclass grid
                #reclassrange = "0.000000 60 0;60 9999 1"
                # reclassrange = RemapRange([[0,60,0],[60,9999,1]])
                # # obj.categorizeGrid("SLOPE_GRID", reclassrange, "GridSlope_60")  # makes steep slopes
                # Reclassify("SLOPE_GRID", reclassrange, "GridSlope_60")
                reclass_range = RemapRange([[0, 60, 0], [60, 9999, 1]])
                grid_slope_50 = Reclassify("SLOPE_GRID", "Value", reclass_range)
                grid_slope_50.save("GridSlope_60")
                # convert gid to poly and clips to a boundary
                obj.Grid_to_Poly("GridSlope_50", "Value", "slope50_poly", watershed_aoi_bnd)
                obj.Grid_to_Poly("GridSlope_60", "Value", "slope60_poly", watershed_aoi_bnd)
            dataSourceDict['slope50'] = fgdbLoc + "\\slope50_poly"
            dataSourceDict['slope60'] = fgdbLoc + "\\slope60_poly"
            
            print ('...DONE create_slope.')
            __PrintTime(deltaTime)


        def add_elev(in_table, in_min_dict, in_max_dict):
            """
            Add elevations to watershed Min and Max (Graham)
            :param in_table: 
            :param in_min_dict: 
            :param in_max_dict: 
            :return: 
            """
            print ('\nStarting add_elev...' )
            # add min max elevations to
            objelev = CEA_Module_NB.featureclass_utils()
            list_returned = objelev.return_field_list(in_table)
            
            if 'MinElev' not in list_returned:
                arcpy.AddField_management(in_table, 'MinElev', 'FLOAT')
            if 'MaxElev' not in list_returned:
                arcpy.AddField_management(in_table, 'MaxElev', 'FLOAT')
                
            objtab = CEA_Module_NB.table_utils()
            objtab.Populate_table_withdictionary(in_table, 'MinElev', wsLinkFld, in_min_dict)
            objtab.Populate_table_withdictionary(in_table, 'MaxElev', wsLinkFld, in_max_dict)
            
            # Add elevation range/relief
            if not arcpy.ListFields(in_table, 'Elev_Relief'):
                arcpy.AddField_management(in_table, 'Elev_Relief', 'Double', '', '2')
                arcpy.CalculateField_management(in_table, 'Elev_Relief', "!MaxElev! - !MinElev!", "PYTHON3")
            
            print ('...DONE add_elev.')
            __PrintTime(deltaTime)


        def create_h_poly(elev_src):
            """
            Module for creating Hypsographic Polygons of watersheds 
            The H value is the %elevation at which that percent of the watershed is above.
            For example,  H70 is the elevation at which 70% of the watershed lies above.
            :param elev_src: 
            :return: 
            """
            h_poly_start_time = time.time()
            
            print ('\nStarting Hpoly generation...') 
            arcpy.env.workspace = fgdbLoc
                
            # make an Hpoly library file geodatabase
            obj_fgdb = CEA_Module_NB.FGDB_utils(BaseFolder)
            outFeatureDataset = obj_fgdb.make_FGDB(sOutputLoc, setOutputlibraryFGDB, 'H_Polys')

            if not arcpy.Exists('DEM_GRID'):
                grid_dem_source = elev_src
                obj = CEA_Module_NB.gridClass(BaseFolder)
                envelopestring = obj.get_geom_envelope(wsBnd)
                obj.extractGrid(grid_dem_source, "DEM_GRID", envelopestring)
                print ('Done extracting DEM')

            # Specify Hypsographic break line(s)
            h_line = 'H70_40'
            out_h_poly_fd = outFeatureDataset
            
            # if not arcpy.Exists(appendout_h_poly_fd):
            print ('\n Running Watershed Generation and Min Max Elevation')
            objdem = CEA_Module_NB.watershedData()
            objdem.H_watershed_gen(wsNested, wsLinkFld, h_line, out_h_poly_fd, 'DEM_GRID')
            maxnum = objdem.maxDict
            minnum = objdem.minDict
            add_elev('Watershed_STATS_TABLE', minnum, maxnum)  # adds min/max elevation and Relief to summary table

            # Add elevation range/relief
            if not arcpy.ListFields('Watershed_STATS_TABLE', 'Elev_Relief'):
                arcpy.AddField_management('Watershed_STATS_TABLE', 'Elev_Relief', 'Double', '', '2')
            arcpy.CalculateField_management('Watershed_STATS_TABLE', 'Elev_Relief', "!MaxElev! - !MinElev!", "PYTHON3")

            dataSourceDict['Hpoly'] = out_h_poly_fd + "\\Append_Hpoly" + h_line
            
            # return maxnum, minnum
            h_poly_total_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - h_poly_start_time))
            print ('\n This Hpoly script took ' + h_poly_total_time + ' to run.')
            print ('...DONE create_h_poly.')
            __PrintTime(deltaTime)


        def alpine_nf(in_vri):
            """
            Calc Non-forested(Alpine and Alpine Forest)  (Gail)
            VRI2 based analysis - inputs VRI2 and shape field
            :param in_vri: 
            :return: 
            """
            if not arcpy.Exists('RU_Alpine_NF'):
                print ('\nStarting Alpine Non-Forest analysis...' )
                arcpy.env.workspace = srcLoc
                
                # find the area field for resultant (e.g. Shape_area or Geometry_area)
                obj_fc = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_fc.GetGeometryField(in_vri)
                area_field = geom_tuple[0]
                    
                print ('Calculating Non-Forested area. Alpine or Alpine forest')
                if not arcpy.ListFields(in_vri, 'ALPINE_NF'):
                    arcpy.AddField_management(in_vri, 'ALPINE_NF', 'TEXT', '', '', '5')
                if not arcpy.ListFields(in_vri, 'ALPINE_NF_HA'):
                    arcpy.AddField_management(in_vri, 'ALPINE_NF_HA', 'DOUBLE')
                
                arcpy.MakeFeatureLayer_management(in_vri, "NFlyr")
                # arcpy.SelectLayerByAttribute_management('NFlyr',"NEW_SELECTION",
                # "\"BCLCS_LEVEL_1\" = 'N' and \"BCLCS_LEVEL_2\" IN ('L','N') and \"BCLCS_LEVEL_3\" IN ('U','A')")
                arcpy.SelectLayerByAttribute_management('NFlyr', "NEW_SELECTION",
                                                        "\"BCLCS_LEVEL_3\" = 'A' or \"NON_PRODUCTIVE_DESCRIPTOR_CD\" IN ('A','AF')")
                arcpy.CalculateField_management("NFlyr", "ALPINE_NF", "\"YES\"", "PYTHON3")

                # Intersect selection with watersheds and calculate hectares
                if not arcpy.Exists(fgdbLoc + '\\RU_Alpine_NF'):
                    print (' Intersecting Alpine NF with Watersheds..')
                    arcpy.Intersect_analysis([wsNested, 'NFlyr'], fgdbLoc + '\\RU_Alpine_NF', "NO_FID", "0.1")
                    arcpy.CalculateField_management(fgdbLoc + '\\RU_Alpine_NF', "ALPINE_NF_HA",
                                                    "!" + area_field + "!/10000", "PYTHON3")
                    print ('Done intersect...')
                
                arcpy.Delete_management('NFlyr')
                
            arcpy.env.workspace = fgdbLoc
            if not arcpy.Exists('frq_score_Alpine_NF'):
                arcpy.Frequency_analysis('RU_Alpine_NF', 'frq_score_Alpine_NF', [wsLinkFld, wsAreaHa], ['ALPINE_NF_HA'])
                if not arcpy.ListFields('frq_score_Alpine_NF', 'ALPINE_NF_PERCENT'):
                    arcpy.AddField_management('frq_score_Alpine_NF', 'ALPINE_NF_PERCENT', 'DOUBLE')
                    arcpy.CalculateField_management("frq_score_Alpine_NF", "ALPINE_NF_PERCENT",
                                                    "(!ALPINE_NF_HA! / !RU_Area_ha! )*100", "PYTHON3")

            # join the stats table
            objfcutil = CEA_Module_NB.featureclass_utils()
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_score_Alpine_NF", wsLinkFld, ['ALPINE_NF_PERCENT'])
                    
            print ('...DONE Alpine NF')
            __PrintTime(deltaTime)


        def bec_zone_analysis(in_watershed, in_bec):
            """
            BEC Zone - proportion of watershed by BEC variant category and sum Snow Accumulation Score - BEC   (Gail)
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Remove ''' from check missing values
            CAUTION
            Coding was added to identify missing BEC LU Values with -1  SB
            CHECK the output results for -1 values in the BEC_Score column
            BEC_Weighting IS NULL coding was modified to -1 in the BEC dataset to identify the
            BEC Units missing the BEC weighting
            :param in_watershed: 
            :param in_bec: 
            :return: 
            """
            print ('\nStarting BEC analysis...')   # Gail Smith

            # Intersecting AOI with Watershed Reporting Units and BEC and add BEC weight field...'
            arcpy.MakeFeatureLayer_management(in_watershed, 'RUs_Lyr')
            arcpy.MakeFeatureLayer_management(in_bec, 'BEC_Lyr')
            if not arcpy.ListFields('BEC_Lyr', 'BEC_Weighting'):
                print ('    BEC_Weighting field does not exist in source data.')
                sys.exit()
            
            if not arcpy.Exists('BEC_RU'):
                arcpy.Intersect_analysis(['BEC_Lyr', 'RUs_Lyr'], 'BEC_RU', "NO_FID", "0.1")
                # get geom field for area calculations
            obj_fc = CEA_Module_NB.featureclass_utils()
            geom_tuple = obj_fc.GetGeometryField('BEC_RU')
            area_field = geom_tuple[0]

            if not arcpy.Exists('frq_score_BEC'):
                print ('  BEC Table Summaries...'    )
                # Get area of BEC by weight per RU
                # Table 1 - Running interm frequency to determine BEC weight by RU & weight...'
                arcpy.MakeTableView_management('BEC_RU', 'BEC_RU_layer')  # Frequency won't take a FC
                arcpy.Frequency_analysis('BEC_RU_layer', 'sumBEC_table1', [wsLinkFld, wsAreaM2, 'BEC_Weighting'], area_field)
                if not arcpy.ListFields('sumBEC_table1', 'BEC_Score'):
                    arcpy.AddField_management('sumBEC_table1', 'BEC_Score', 'Double', '', '2')

                # Check for missing values
                arcpy.MakeFeatureLayer_management(in_bec, "becLyr2")    
                arcpy.SelectLayerByAttribute_management('becLyr2', "NEW_SELECTION", "BEC_Weighting IS NULL")
                # calculate current select to 0
                arcpy.CalculateField_management("becLyr2", "BEC_Weighting", "0", "PYTHON3")

                count = int(arcpy.GetCount_management('becLyr2').getOutput(0))
                if count > 0:
                    print ('    This many BEC UNITS have no information:', arcpy.GetCount_management('becLyr2'))
                    print( '    QUITTING!  CHeck your data!')
                    print(in_bec)
                    sys.exit()

                # Default
                arcpy.CalculateField_management("sumBEC_table1", "BEC_Score", "0", "PYTHON3")
                # expression =  "[BEC_Weighting]*(["+areaItem+"]/["+wsAreaM2+"])"
                arcpy.CalculateField_management('sumBEC_table1', 'BEC_Score',
                                                "!BEC_Weighting! * ( !" + area_field + "! / !" + wsAreaM2 + "!)", "PYTHON3")

                # Table 2   - add up total scores
                arcpy.MakeTableView_management('sumBEC_table1', 'table1_layer')  # Frequency won't take a FC
                arcpy.Frequency_analysis('table1_layer', 'frq_score_BEC', [wsLinkFld], "'BEC_Score'")
                
                print ('  Cleanup...')
                if arcpy.Exists('sumBEC_table1'):
                    arcpy.Delete_management('sumBEC_table1')
                    
            # Delete unnecessary fields and join to main table
            objfcutil = CEA_Module_NB.featureclass_utils()

            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_score_BEC", wsLinkFld, 'BEC_Score')
            
            print ('BEC Final Summation Table = frq_score_BEC. It was joined to Watershed_STATS_TABLE')
            print ('...DONE BEC Zones.')
            __PrintTime(deltaTime)


        def eca(in_vri, in_row, in_private, in_bec):
            """
            ECA   (Sasha)
            Calc Equivalent Clearcut Area (ECA)
            VRI2 based analysis.
            BEC is used to classify wet/moist vs dry zones for use in Mountain Pine Beetle ECA effect calculation
            ECA is calculated in an hierarchical order such that later calculations can over-write earlier calcs.
            :param in_vri: 
            :param in_row: 
            :param in_private: 
            :param in_bec: 
            :return: 
            """
            arcpy.env.workspace = fgdbLoc
            print ('\nStarting ECA analysis...')
            if not arcpy.Exists('ECA_resultant'):
                height_field = 'VRI2_HEIGHT'  # THis is the VRI with FTEN and Results integrated. Default value is NULL
                objECA = CEA_Module_NB.featureclass_utils()
                
                arcpy.env.workspace = srcLoc

                # Add years since IBM disturbance.  Assumes Projected_Date is always populated.
                print ('Calculating years since IBM disturbance...')
                if not arcpy.ListFields(in_vri, 'yrs_since_IBM_dstrb'):
                    arcpy.AddField_management(in_vri, 'yrs_since_IBM_dstrb', 'SHORT')
                arcpy.MakeFeatureLayer_management(in_vri, 'vriLyr')
                arcpy.SelectLayerByAttribute_management('vriLyr', "NEW_SELECTION",
                                                        "EARLIEST_NONLOGGING_DIST_TYPE = 'IBM' and EARLIEST_NONLOGGING_DIST_DATE is not null ")
                arcpy.CalculateField_management('vriLyr', "yrs_since_IBM_dstrb", "!PROJECTED_DATE_YR! - !ENL_DISTURB_YEAR!",
                                                "PYTHON3")
                arcpy.Delete_management('vriLyr')
                print ('Done calculating years since IBM disturbance...')
        
                # Prep BEC - add wet/moist/dry based on moose classification
                if arcpy.Exists('BEC_moisture'):
                    arcpy.Delete_management('BEC_moisture')
                arcpy.Dissolve_management(in_bec, 'BEC_moisture', 'BEC_MOIST_CLS', "", "SINGLE_PART")
                
                # Union VRI and BEC
                vri_bec = 'VRI2_BEC_moist_temp'
                print ('Union VRI2 and BEC_moisture...')
                arcpy.Union_analysis([in_vri, 'BEC_moisture'], vri_bec)

                if not arcpy.Exists('ECA_temp2'):
                    print ('Merging private and Right of Way')
                    arcpy.Union_analysis([in_row, in_private], 'PrivROW')
                    print ('Creating identity of VRI and PrivROW')
                    # New Added buffered roads
                    arcpy.Identity_analysis(vri_bec, 'Roads_Row', "ECA_temp2")

                # Add Wildfires - New
                print ('Union ECA_temp with Wildfires')
                arcpy.Union_analysis("ECA_temp2 #; AllBurns25 #", "ECA_temp")

                print ('Calculating ECA...')
                if not arcpy.ListFields("ECA_temp", 'ECA_Factor'):
                    arcpy.AddField_management("ECA_temp", 'ECA_Factor', 'DOUBLE')
                if not arcpy.ListFields("ECA_temp", 'ECA_Type'):
                    arcpy.AddField_management("ECA_temp", 'ECA_Type', 'Text', '', '', '25')
                if not arcpy.ListFields("ECA_temp", 'ECA_HA'):
                    arcpy.AddField_management("ECA_temp", 'ECA_HA', 'Double', '', '2')
                
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                # Default to initially determine what is not being selected for (if anything)
                # Note: Default records that remain are largely herb, shrubby, alpine, rock, water & misc natural non-vegetated
                print ('Calculating default ECA values...')
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "0", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "Default", "PYTHON3")
                
                # The majority of ROWS are captured in VRI
                # ROW = 100% ECA - note that some of this is overwritten below - eg. if there is height info
                print ('Calculating ECA for ROWs')
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "ROADS = 'Y'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "Roads_Row", "PYTHON3")
                arcpy.Delete_management('ecaLyr')

                # -----------------------------------CRITERIA FOR MPB FACTOR
                # Calculating MPB factor based on years since MPB disturbance,  %stand dead, and BEC
                # MPB effect on ECA kicks in within 5 yrs, and is maximum at ~20yrs.  Stand recovery from 20-60+ years
                # This value will be additive with ECA height value

                # Add fields for %Dead Class and yrs since attack class
                print ('Starting Calculations for MPB Factor...')
                for fld in ('MPB_dead_cls', 'MPB_yrs_cls', 'MPB_Factor'):
                    if not arcpy.ListFields("ECA_temp", fld):
                        print ('Adding field ', fld)
                        arcpy.AddField_management("ECA_temp", fld, 'SHORT')
                # Default MPB Factor to 0
                arcpy.CalculateField_management('ECA_temp', "MPB_Factor", "0", "PYTHON3")
                
                # Use VRI 2 and Basal Area Adjusted - PINE_PERCENT_FINAL field
                # Calc MPB_dead_cls  based on % dead
                pc_dead_code = """def getDeadCls(pcDead):
                    if pcDead > 0 and pcDead <= 30:
                        return 1
                    if pcDead > 30 and pcDead <= 50:
                        return 2
                    if pcDead > 50 and pcDead <= 70:
                        return 3
                    if pcDead > 70:
                        return 4
                    else:
                        return 0"""
                
                # Calc MPB_yrs_cls  based on years since attack
                mpb_yrs_code = """def getYrsCls(ysa):
                    if ysa > 0 and ysa <= 5:
                        return 5
                    if ysa > 5 and ysa <= 10:
                        return 10
                    if ysa > 10 and ysa <= 15:
                        return 15
                    if ysa > 15 and ysa <= 20:
                        return 20
                    if ysa > 20 and ysa <= 25:
                        return 25
                    if ysa > 25 and ysa <= 30:
                        return 30
                    if ysa > 30 and ysa <= 35:
                        return 35
                    if ysa > 35 and ysa <= 40:
                        return 40
                    if ysa > 40 and ysa <= 45:
                        return 45
                    if ysa > 45 and ysa <= 50:
                        return 50
                    if ysa > 50 and ysa <= 55:
                        return 55
                    if ysa > 55 and ysa <= 60:
                        return 60
                    if ysa > 60:
                        return 100
                    else:
                        return 0"""

                # Select for >30% pine stands with > 0 percent dead and IBM disturbance
                # select_criteria = "tot_pine_pc > 30 and STAND_PERCENTAGE_DEAD > 0 and EARLIEST_NONLOGGING_DIST_TYPE = 'IBM'"
                # Decide not to use %Pine to restrictively, as sometime the IBM %dead is > %pine
                # Changed or to and *******************************************

                select_criteria = "(PINE_PERCENT_FINAL > 30 and STAND_PERCENTAGE_DEAD > 0) and EARLIEST_NONLOGGING_DIST_TYPE = 'IBM'"
                arcpy.MakeFeatureLayer_management('ECA_temp', 'mpbLyr', select_criteria)
                print ('Calculating MPB_dead_cls and MPB_yrs_cls')
                arcpy.CalculateField_management('mpbLyr', 'MPB_dead_cls', "getDeadCls(!STAND_PERCENTAGE_DEAD!)",
                                                "PYTHON3", pc_dead_code)
                arcpy.CalculateField_management('mpbLyr', 'MPB_yrs_cls', "getYrsCls(!yrs_since_IBM_dstrb!)",
                                                "PYTHON3", mpb_yrs_code)
                
                # Dictionary for MPB Factor - based on: BEC Moisture Class, Percent Dead Class, Years Since Attack Class
                mpb_factor_code = """def getMPBfactor(BECm,Dcls,Ycls):
                    #print BECm,Dcls,Ycls
                    if BECm == 'Dry':
                        if Dcls ==0:
                            return 0
                        if Dcls ==1:
                            return 0
                        else:
                            if Dcls ==2:
                                Dry_Dict = {5:5,10:10,15:20,20:30,25:30,30:25,35:20,40:15,45:10,50:5,55:5,60:0,100:0}
                            if Dcls ==3:
                                Dry_Dict = {5:10,10:30,15:40,20:50,25:50,30:40,35:30,40:20,45:15,50:10,55:5,60:5,100:0}
                            if Dcls ==4:
                                Dry_Dict = {5:15,10:50,15:60,20:70,25:70,30:60,35:50,40:40,45:30,50:20,55:15,60:10,100:0}
                
                            retVal = None
                            if Ycls in Dry_Dict:
                            # if Dry_Dict.has_key(Ycls):
                                retVal = Dry_Dict[Ycls]
                                #print retVal
                            return retVal
                                
                    if BECm == 'Wet':
                        if Dcls ==0:
                            return 0
                        if Dcls ==1:
                            return 0
                        else:
                            if Dcls ==2:
                                Wet_Dict = {5:5,10:10,15:15,20:20,25:20,30:15,35:10,40:5,45:0,50:0,55:0,60:0,100:0}
                            if Dcls ==3:
                                Wet_Dict = {5:5,10:15,15:20,20:30,25:30,30:20,35:15,40:10,45:10,50:5,55:0,60:0,100:0}
                            if Dcls ==4:
                                Wet_Dict = {5:10,10:30,15:40,20:45,25:45,30:40,35:30,40:25,45:20,50:10,55:5,60:0,100:0}
                
                            retVal = None
                            if Ycls in Wet_Dict:
                            # if Wet_Dict.has_key(Ycls):
                                retVal = Wet_Dict[Ycls]
                                #print retVal
                            return retVal"""
                            
                # Loop to calculate MPB Factor
                arcpy.CalculateField_management('mpbLyr', 'MPB_Factor',
                                                "getMPBfactor(!BEC_MOIST_CLS!,!MPB_dead_cls!,!MPB_yrs_cls!)",
                                                "PYTHON3", mpb_factor_code)
                arcpy.Delete_management("mpbLyr")

                # [sic] Decidous leading stands height modification to Secondary Height
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")        
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "LEADING_SPECIES = 'DECIDUOUS'")
                arcpy.CalculateField_management('ecaLyr', "VRI2_HEIGHT", "!PROJ_HEIGHT_2!", "PYTHON3", "")    
                arcpy.Delete_management("ecaLyr")

                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                
                # -----------------------------------CRITERIA FOR Height FACTOR
                # Forest with Height info
                # Assumes that PROJ_HEIGHT_1 is > 0 where there is species info. ie. Height is never zero, only null.
                # Zero and null heights are further dealt with below.
                # Assume Fully stocked??
                # Calculate in Descending order, so that they over-write each other.
                # Winkler Height Model - maximum height 25 meters
                # Note:  0 height is a legit value for RSLTS FC NP roads/unnatural(landings)
                eca_list = [[' >= 19', '0.0', 'Height 19 m plus'],
                            [' < 19 and '+height_field+' >=18', '5.4', 'Height 18-<19 m'],
                            [' < 18 and '+height_field+' >= 17', '6.9', 'Height 17-<18 m'],
                            [' < 17 and '+height_field+' >= 16', '8.7', 'Height 16-<17 m'],
                            [' < 16 and '+height_field+' >= 15', '11.0', 'Height 15-<16 m'],
                            [' < 15 and '+height_field+' >= 14', '13.8', 'Height 14-<15 m'],
                            [' < 14 and '+height_field+' >= 13', '17.3', 'Height 13-<14 m'],
                            [' < 13 and '+height_field+' >= 12', '21.7', 'Height 12-<13 m'],
                            [' < 12 and '+height_field+' >= 11', '26.9', 'Height 11-<12 m'],
                            [' < 11 and '+height_field+' >= 10', '33.3', 'Height 10-<11 m'],
                            [' < 10 and '+height_field+' >=9', '40.9', 'Height 9-<10 m'],
                            [' < 9 and '+height_field+' >= 8', '49.7', 'Height 8-<9 m'],
                            [' < 8 and '+height_field+' >= 7', '59.5', 'Height 7-<8 m'],
                            [' < 7 and '+height_field+' >= 6', '70.1', 'Height 6-<7 m'],
                            [' < 6 and '+height_field+' >= 5', '80.7', 'Height 5-<6 m'],
                            [' < 5 and '+height_field+' >= 4', '90.1', 'Height 4-<5 m'],
                            [' < 4 and '+height_field+' >= 3', '96.9', 'Height 3-<4 m'],
                            [' < 3 and '+height_field+' >= 2', '99.8', 'Height 2-<3 m'],
                            [' < 2 and '+height_field+' >= 0', '100.0', 'Height 0-<2 m']]
                
                print ('Calculating ECA based on VRI height')
                for item in eca_list:
                    select_criteria = item[0]
                    ecaClass = item[1]
                    ecaType = item[2]
                    
                    selectQuery = height_field + select_criteria
                    print (selectQuery)
                    
                    arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", selectQuery)
                    arcpy.CalculateField_management('ecaLyr', "ECA_Factor", '"' + ecaClass + '"', "PYTHON3")
                    arcpy.CalculateField_management('ecaLyr', "ECA_Type", '"' + ecaType + '"', "PYTHON3")

                    # Adding height values prior to any changes from the MPB factor
                    arcpy.AddField_management("ECA_temp", 'ECA_HT_Factor', 'DOUBLE')
                    arcpy.AddField_management("ECA_temp", 'ECA_HT_Type', 'Text', '', '', '25')
                    arcpy.CalculateField_management('ecaLyr', "ECA_HT_Factor", "!ECA_Factor!", "PYTHON3")
                    arcpy.CalculateField_management('ecaLyr', "ECA_HT_Type", "!ECA_Type!", "PYTHON3")
                
                # -----------------------------------------------------
                # Add MPB and Height Factor - not to exceed 100
                selectQuery = "MPB_Factor > 0"
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", selectQuery)
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "!ECA_Factor! + !MPB_Factor!", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "MPB", "PYTHON3", "")

                # Height modified to 19 from 12
                selectQuery = height_field+' >= 0 and '+height_field+'< 19'
                arcpy.SelectLayerByAttribute_management('ecaLyr', "SUBSET_SELECTION", selectQuery)
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "MPB and Height", "PYTHON3")
                # if over 100, calc back down to 100%
                selectQuery = "ECA_Factor > 100"
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", selectQuery)
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "100", "PYTHON3")
                
                print ('\nAdding category for additional openings...')
                # This Section assumes if 100% ECA if Harvested in the last 20 years, and no other height info is available
                # BEWARE OF TIME SINCE HARVEST!! ONLY USE HARVESTING IN LAST 20 years.
                # Select harvesting from Results/FTEN  where VRI2_HEIGHT  is Null.
                # Beware that 0 is a legit value (dealt with above)
                # WARNING: CHECK FOR VRI2_HARVESTED = 'YES' and VRI2_DISTURB_YR IS NULL!!
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        height_field + "is NULL and VRI2_HARVESTED = 'YES' and VRI2_DISTURB_YR > 2002")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "Misc 20Yr Opening", "PYTHON3")
                
                print ('Calculating ECA for Burns etc..')
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "EARLIEST_NONLOGGING_DIST_TYPE in ( 'B', 'NB') and EARLIEST_NONLOGGING_DIST_DATE > date'01-JAN-1990'")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "ADD_TO_SELECTION",
                                                        "VRI2_DISTURB_CODE = 'B' and VRI2_DISTURB_DATE > date'01-JAN-1990'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "Burn", "PYTHON3")
                
                print ('Calculating ECA for BCLCS NonNatural ...')
                # GP=Gravel Pit; MI=Open Pit Mine; RZ=Road Surface; TZ=Tailings; UR=Urban 
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "BCLCS_LEVEL_5 in ('GP','MI','RZ','TZ','UR')")  # CB
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "BLCLCS Non-Natural", "PYTHON3")
                
                # Did not use M- meadow, as these may be natural
                # Clearing, Gravel Pit, Urban  - (No height info)
                print( 'Calculating ECA for NP NonNatural ...')
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "NON_PRODUCTIVE_DESCRIPTOR_CD in ('C', 'GR','U')")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "NP Non-Natural", "PYTHON3")

                print ('Calculating ECA for private land - moved location towards end of ECA')
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "OWNER_TYPE = 'PRIVATE'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "75", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "Private", "PYTHON3")
                arcpy.Delete_management('ecaLyr')
                
                # find the area field for resultant
                geom_tuple = objECA.GetGeometryField("ECA_temp")
                area_field = geom_tuple[0]
                
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.CalculateField_management('ecaLyr', "ECA_HA",
                                                "(!" + area_field + "! /10000) * (!ECA_Factor! /100)", "PYTHON3")

                # #################################################
                # #################################################
                # Back up original calculations prior to height fix
                arcpy.AddField_management("ECA_temp", 'ECA_Factor_Orig', 'DOUBLE')
                arcpy.AddField_management("ECA_temp", 'ECA_Type_Orig', 'Text', '', '', '25')
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor_Orig", "!ECA_Factor!", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type_Orig", "!ECA_Type!", "PYTHON3")
            
                # ECA height model fix contains duplication
                arcpy.AddField_management("ECA_temp", 'ECA_Factor2', 'DOUBLE')
                arcpy.AddField_management("ECA_temp", 'ECA_Type2', 'Text', '', '', '25')
                arcpy.Delete_management('ecaLyr')
                # Setting Default
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Default", "PYTHON3")
                # Note: The records that remain as default are largely herb, shrubby, alpine, rock,
                # water and misc natural non-vegetated
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "0", "PYTHON3")
                # MPB - Add MPB and Height Factor - not to exceed 100
                select_query_2 = "MPB_Factor > 0"
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", select_query_2)
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "!ECA_Factor_Orig!", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "!ECA_Type_Orig!", "PYTHON3")
                # select_query_2 = height_field+' >= 0 and '+height_field+'< 12'
                # arcpy.SelectLayerByAttribute_management('ecaLyr',"SUBSET_SELECTION",select_query_2)
                # arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "!ECA_Factor_Orig!", "PYTHON3", "")
                # arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "\"MPB and Height\"", "PYTHON3", "")
                # select_query_2 = "ECA_Factor2 > 100"
                # arcpy.SelectLayerByAttribute_management('ecaLyr',"NEW_SELECTION",select_query_2)
                # arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "100", "PYTHON3", "" )
                # BCLCS NonNatural ...'
                # GP=Gravel Pit; MI=Open Pit Mine; RZ=Road Surface; TZ=Tailings; UR=Urban 
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "BCLCS_LEVEL_5 in ( 'GP','MI','RZ','TZ','UR')")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "BLCLCS Non-Natural", "PYTHON3")
                # NP NonNatural
                # Clearing, Gravel Pit, Urban  - (No height info)
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "NON_PRODUCTIVE_DESCRIPTOR_CD in ( 'C', 'GR','U')")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "NP Non-Natural", "PYTHON3")
                # Presumed Logged Cutblocks
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "VRI2_DISTURB_CODE = 'Presumed Logged'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Presumed Logged", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "!ECA_Factor!", "PYTHON3")
                # Misc 20Yr Opening
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        height_field + "is NULL and VRI2_HARVESTED = 'YES' and VRI2_DISTURB_YR > 2002")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Misc 20Yr Opening", "PYTHON3")

                # ##Fires and Wildfires
                # Wildfires if logged it is coded below
                # FIRE_YEAR - Modified data extraction process to Fires < 25 years
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "FIRE_YEAR > 1995 AND VRI2_SPECIES IS NOT NULL")
                # arcpy.SelectLayerByAttribute_management('ecaLyr',"NEW_SELECTION", "FIRE_YEAR != 0 AND VRI2_SPECIES IS NULL")
                # Added default ECA of 80(Provincial Burn Severity) - Temporary until Burn Severity is calculated
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "80", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Wildfire", "PYTHON3")
                
                # Burns if logged it is coded below
                # Commented out lines and modified code
                # arcpy.SelectLayerByAttribute_management('ecaLyr',"NEW_SELECTION",
                # "\"EARLIEST_NONLOGGING_DIST_TYPE\" in ( 'B', 'NB') and \"EARLIEST_NONLOGGING_DIST_DATE\" > date'01-JAN-1900'")      
                # arcpy.SelectLayerByAttribute_management('ecaLyr',"NEW_SELECTION",
                # "\"VRI2_DISTURB_CODE \" = 'B' and \"VRI2_DISTURB_DATE\" > date'01-JAN-1900'")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "VRI2_DISTURB_CODE = 'B' AND VRI2_DISTURB_YR >= 1995")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "80", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Burn", "PYTHON3")
                
                # Logged or Salvaged
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "VRI2_DISTURB_CODE = 'L' OR VRI2_DISTURB_CODE = 'S'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Logged_Salv", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "!ECA_Factor!", "PYTHON3")

                # Private land
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "OWNER_TYPE = 'PRIVATE'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "75", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Private", "PYTHON3")
                arcpy.Delete_management('ecaLyr')
            
                # Add IBM disturbance occurred after logging.
                print ('Checking to see if IBM disturbance occurred after logging...')
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.AddField_management('ecaLyr', 'IBM_YEAR', 'SHORT')
                arcpy.AddField_management('ecaLyr', 'temp_days2', 'SHORT')
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "EARLIEST_NONLOGGING_DIST_TYPE = 'IBM' and EARLIEST_NONLOGGING_DIST_DATE is not null ")
                arcpy.CalculateField_management('ecaLyr', "IBM_YEAR", "!VRI2_DISTURB_YR! - !ENL_DISTURB_YEAR!", "PYTHON3")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "IBM_YEAR < 0")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "!ECA_Factor_Orig!", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "MPB after log", "PYTHON3")
                arcpy.Delete_management('vriLyr')    

                #  Convert ECA for Decidous to 0 for SP1 100%
                print ('Conifer1....2nd interation...')
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                # arcpy.SelectLayerByAttribute_management('ecaLyr',"NEW_SELECTION","\"CONIFER1\" = 'DECIDOUS'")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION",
                                                        "CONIFER1 = 'DECIDOUS' AND SPECIES_PCT_1 = 100")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "0", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Reset_Decid", "PYTHON3")
                arcpy.Delete_management('ecaLyr')
                
                # ROW Roads - comment out if it does not exist
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "ROADS = 'Y'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Roads_Row", "PYTHON3")
                arcpy.Delete_management('ecaLyr')

                # ROW - comment out if it does not exist
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "ROW = 'Y'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "100", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Roads_Row", "PYTHON3")
                arcpy.Delete_management('ecaLyr')

                # Burn Severity Update 2018 - Temporary
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.SelectLayerByAttribute_management('ecaLyr', "NEW_SELECTION", "BS_Severity_2018 = 'Y'")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor2", "!Burn_Score_2018_ECA!", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type2", "Wildfires_2018", "PYTHON3")

                # Final Calculations
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")
                arcpy.CalculateField_management('ecaLyr', "ECA_Factor", "!ECA_Factor2!", "PYTHON3")
                arcpy.CalculateField_management('ecaLyr', "ECA_Type", "!ECA_Type2!", "PYTHON3")
                arcpy.Delete_management('ecaLyr')
                arcpy.MakeFeatureLayer_management("ECA_temp", "ecaLyr")        
                arcpy.CalculateField_management('ecaLyr', "ECA_HA", "(!" + area_field + "! /10000) * (!ECA_Factor! /100)",
                                                "PYTHON3")
                # End of fix       

                # Dissolve
                eca_out = srcLoc + '\\ECA_dissolve'
                if not arcpy.Exists(eca_out):
                    print ('Dissolving on ECA fields..')
                    arcpy.Dissolve_management('ECA_temp', eca_out, 'ECA_Type;ECA_Factor', "#", "SINGLE_PART", "DISSOLVE_LINES")
                    if not arcpy.ListFields(eca_out, 'ECA_HA'):
                        arcpy.AddField_management(eca_out, 'ECA_HA', 'Double', '', '2')
                    # arcpy.CalculateField_management(eca_out, "ECA_HA", "[" + areaItem + "]/10000" + " * ([ECA_Factor]/100)")
                    arcpy.CalculateField_management(eca_out, "ECA_HA", "(!" + area_field + "! /10000) * (!ECA_Factor! /100)",
                                                    "PYTHON3")
                    print ('Done dissolving...')

                # -----------------------------------------------------
                # Overlay with Nested Watersheds
                arcpy.env.workspace = fgdbLoc
                print ('Overlaying ECA with Watersheds')
                # desc = arcpy.Describe('eca_ws')
                # areaItem = desc.AreaFieldName
                eca_out = srcLoc + '\\ECA_dissolve'
                eca_ws = 'ECA_resultant'
                if arcpy.Exists(eca_ws):
                    arcpy.Delete_management(eca_ws)
                if not arcpy.Exists(eca_ws):
                    print ('Creating intersect of ECA Dissolved and Watershed Reporting Units')
                    # arcpy.Identity_analysis(wsNested,eca_out,eca_ws)
                    arcpy.Intersect_analysis([wsNested, eca_out], eca_ws, "NO_FID", "0.1")
                    geom_tuple = objECA.GetGeometryField(eca_out)
                    area_field = geom_tuple[0]
                    arcpy.AddField_management(eca_ws, 'ECA_HA2', 'Double', '', '2')
                    arcpy.CalculateField_management(eca_ws, "ECA_HA2", "!" + area_field + "! / 10000", "PYTHON3")
                    arcpy.AddField_management(eca_ws, 'ECA_FAC', 'Double', '', '2')
                    arcpy.AddField_management(eca_ws, 'TEMP', 'Double', '', '2')
                    arcpy.CalculateField_management(eca_ws, "TEMP",  "!ECA_Factor!", "PYTHON3")
                    arcpy.CalculateField_management(eca_ws, "ECA_FAC",  "!TEMP! /100", "PYTHON3")
                    arcpy.CalculateField_management(eca_ws, "ECA_HA",  "!ECA_HA2! * !ECA_FAC!", "PYTHON3")
                    print ('Done')

            eca_ws = 'ECA_resultant'      
            if not arcpy.Exists('frq_score_ECA'):
                # summarize
                arcpy.Frequency_analysis(eca_ws, "frq_score_ECA", [wsLinkFld, wsAreaHa], ["ECA_ha"])
                arcpy.AddField_management("frq_score_ECA", 'ECA_Score', 'Double')
                # arcpy.CalculateField_management("frq_score_ECA", "ECA_Score", "([ECA_HA]/["+wsAreaHa+"])*100")
                # Python 64
                arcpy.CalculateField_management("frq_score_ECA", "ECA_Score", "(!ECA_HA! / !RU_Area_ha!) * 100", "PYTHON3")
                
            objfcutil = CEA_Module_NB.featureclass_utils()
            # fieldskeep = [wsLinkFld,'ECA_HA']
            # objfcutil.delete_fields("frq_score_ECA", fieldskeep)
            
            # join the stats table
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_score_ECA", wsLinkFld, ['ECA_Score'])
                
            print ('...Done calculating ECA.')
            __PrintTime(deltaTime)


        def DDR(inWatershed, inStreams):
            """
            DDR  - Drainage Density Ruggedness (Graham).  Stream Density as a function of Relief
            :param inWatershed: 
            :param inStreams: 
            :return: 
            """
            arcpy.env.workspace = fgdbLoc
            print ('\nStarting DDR analysis...')
            if not arcpy.Exists('DDR_resultant'):
                print ('Overlaying streams and watersheds')
                arcpy.Identity_analysis(inStreams, inWatershed, "DDR_resultant")
                
                # find the area field for resultant
                obj_fc60 = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_fc60.GetGeometryField("DDR_resultant")
                length_field = geom_tuple[1]

                arcpy.AddField_management("DDR_resultant", 'DDR_Length_km', 'Double', '', '2')
                arcpy.CalculateField_management("DDR_resultant", 'DDR_Length_km', "!" + length_field + "!/1000", "PYTHON3")
                
            if not arcpy.Exists('frq_score_DDR'):
                arcpy.Frequency_analysis("DDR_resultant", 'frq_score_DDR', [wsLinkFld, wsAreaKM2], ['DDR_Length_km'])
                arcpy.AddField_management("frq_score_DDR", 'DDR_Score', 'DOUBLE')
                
            # objfcutil = CEA_Module_NB.featureclass_utils()
            # fieldskeep = [wsLinkFld,'DDR_Length_km','DDR_Score']
            # objfcutil.delete_fields("frq_score_DDR", fieldskeep)
            
            objfcutil = CEA_Module_NB.featureclass_utils()
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_score_DDR", wsLinkFld, ['DDR_Length_km', 'DDR_Score'])
            # Python 64 - already existed
            arcpy.CalculateField_management("Watershed_STATS_TABLE", 'DDR_Score',
                                            "(!DDR_Length_km!/!" + wsAreaKM2 + "!) * (!MaxElev!- !MinElev!)", "PYTHON3")
            print ('...DONE DDR.')
            __PrintTime(deltaTime)


        def open_water(in_h_fc, in_lake_wetland):
            """
            Absence of Lakes and Wetlands (Graham)
            :param in_h_fc: 
            :param in_lake_wetland: 
            :return: 
            """
            arcpy.env.workspace = fgdbLoc
            print ('\nStarting OpenWater analysis...')
            # the Hpoly layer key field is Unit_id
            link_field = 'Unit_ID'
            if not arcpy.Exists('OW_resultant'):
                # Overlay H poly with open water
                arcpy.Identity_analysis(in_lake_wetland, in_h_fc, "OW_resultant")
                print ('Finished OW identity...')

                # find the area field for resultant
                obj_ow = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_ow.GetGeometryField("OW_resultant")
                area_field = geom_tuple[0]
                
                # add area fields and
                print ('Starting OW cursor updates...')
                cursor_data = ("ZONE", area_field, "Lake_wetland_adjust_ha")
                arcpy.AddField_management("OW_resultant", 'Lake_wetland_adjust_ha', 'DOUBLE')
                with arcpy.da.UpdateCursor("OW_resultant", cursor_data) as cursor:
                    for row in cursor:
                        if row[0] == 'Upper40':
                            row[2] = (row[1]/10000) * 0.25  # shape area
                        elif row[0] == 'Mid 30-70':
                            row[2] = (row[1]/10000) * 0.75  # shape area
                        elif row[0] == 'Lower30':
                            row[2] = (row[1]/10000) * 1.0  # shape area
                        cursor.updateRow(row)

            if not arcpy.Exists('frq_abs_lake_wetland'):
                print ('Starting OW frequency...')
                arcpy.Frequency_analysis("OW_resultant", 'frq_abs_lake_wetland', [link_field], ['Lake_wetland_adjust_ha'])
                # figure out percentage of area of watershed in
                arcpy.AddField_management("frq_abs_lake_wetland", 'Lake_wetland_Abscence', 'DOUBLE')
                # arcpy.CopyRows_management("OW_STATS_TABLE", "frq_abs_lake_wetland")
                
            objfcutil = CEA_Module_NB.featureclass_utils()
            # fieldskeep = [link_field,'Lake_wetland_Abscence','Lake_wetland_adjust_ha']
            # objfcutil.delete_fields("frq_abs_lake_wetland", fieldskeep)
            
            # join the stats table
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_abs_lake_wetland", link_field,
                                ['Lake_wetland_Abscence', 'Lake_wetland_adjust_ha'])
            
            arcpy.CalculateField_management("Watershed_STATS_TABLE", 'Lake_wetland_Abscence',
                                            "(!Lake_wetland_adjust_ha!/!" + wsAreaHa + "!) * 100", "PYTHON3")
            
            print ('...DONE openWater.')
            __PrintTime(deltaTime)


        def slope60(inWatershed, inSlope):
            """
            Terrain Stability
            Calculates percentage of slope over 60 for watersheds (Graham)
            :param inWatershed:
            :param inSlope:
            :return:
            """
            print ('\nStarting Slope60 analysis...')
            if not arcpy.Exists('Slope60_resultant'):
                # Overlay slope
                arcpy.Identity_analysis(inWatershed, inSlope, "Slope60_resultant")
                # find the area field for resultant
                obj_fc60 = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_fc60.GetGeometryField("Slope60_resultant")
                area_field = geom_tuple[0]
                # add area fields and
                arcpy.AddField_management("Slope60_resultant", 'In_60_ha', 'DOUBLE')
                # arcpy.AddField_management("Slope60_resultant",'All_ha','DOUBLE')
                # arcpy.CalculateField_management("Slope60_resultant",'All_ha',"!shape.area@hectares!","PYTHON3")
                # select only polygons with 60 percent slope
                arcpy.MakeFeatureLayer_management("Slope60_resultant", "Slope60LYR", wsLinkFld + " > 0 and GRIDCODE = 1")
                arcpy.CalculateField_management("Slope60LYR", 'In_60_ha', "!" + area_field + "!/10000", "PYTHON3")
                
                arcpy.Delete_management("Slope60LYR")
                
            if not arcpy.Exists('frq_score_TerrStab'):
                arcpy.Frequency_analysis("Slope60_resultant", 'frq_score_TerrStab', [wsLinkFld, wsAreaHa], ['In_60_ha'])
                # figure out percentage of area of watershed in
                arcpy.AddField_management("frq_score_TerrStab", 'Terrain_stability_percent', 'DOUBLE')
                # Python 64 already exists
                arcpy.CalculateField_management("frq_score_TerrStab", 'Terrain_stability_percent',
                                                "(!In_60_ha!/!" + wsAreaHa + "!) * 100", "PYTHON3")
                # arcpy.CopyRows_management("SLOPE60_STATS_TABLE", "frq_score_TerrStab")
                
            # delete unnecessary fields
            objfcutil = CEA_Module_NB.featureclass_utils()
            # fieldskeep = [wsLinkFld,'Terrain_stability_percent']
            # objfcutil.delete_fields("frq_score_TerrStab", fieldskeep)
            # join the slope 60 stats table
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_score_TerrStab",
                                wsLinkFld, 'Terrain_stability_percent')
                
            print ('...DONE slope50 Terrain.')
            __PrintTime(deltaTime)


        def gsc_geology(in_watershed, in_gsc):
            """
            Soil Erodibility (Gail Smith)
            :param in_watershed: 
            :param in_gsc: WHSE_MINERAL_TENURE.GEOL_QUATERNARY_POLY
            :return: 
            """
            print ('\nStarting gsc_geology analysis...')
            if not arcpy.Exists('RU_GSCgeology'):
                # in_watershed must contain a wsAreaM2 field
                arcpy.Intersect_analysis([in_gsc, in_watershed], 'RU_GSCgeology', "NO_FID", "0.1", "INPUT")

            obj_geol = CEA_Module_NB.featureclass_utils()
            geom_tuple = obj_geol.GetGeometryField("RU_GSCgeology")
            area_field = geom_tuple[0]
            
            sum_tab_area = 'sumGSCgeology'
            sum_tab_fin = 'frq_score_GSCgeology'
            if not arcpy.Exists('frq_score_GSCgeology'):
                print ('  Frequency on Input Layer by RU')
                # Table 1
                arcpy.Frequency_analysis('RU_GSCgeology', sum_tab_fin, [wsLinkFld, wsAreaM2], [area_field])
                if not arcpy.ListFields(sum_tab_fin, 'GSC_Score'):
                    arcpy.AddField_management(sum_tab_fin, 'GSC_Score', 'Double', '', '2')
                # percentage score
                arcpy.CalculateField_management(sum_tab_fin, 'GSC_Score', "(!" + area_field + "!/!"+wsAreaM2+"!)*100",
                                                "PYTHON3")
                # Table 2 - Final
                # arcpy.Frequency_analysis(sum_tab_area, sum_tab_fin, [wsLinkFld], ['GSC_Score'])
                
            # objfcutil = CEA_Module.featureclass_utils()
            # fieldskeep = [wsLinkFld,'GSC_Score']
            # objfcutil.delete_fields(sum_tab_fin, fieldskeep)
            
            objfcutil = CEA_Module_NB.featureclass_utils()
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, sum_tab_fin, wsLinkFld, ['GSC_Score'])
            
            print ('  Cleanup...')
            delete_list = [sum_tab_area]
            for input_Layer in delete_list:
                if arcpy.Exists(input_Layer):
                    arcpy.Delete_management(input_Layer)

            print ('...DONE gsc_geology.')
            __PrintTime(deltaTime)


        def gos_steep_coupled_slopes(inWatershed, inDEM, inSlope50, inPerimeter, inFWAWSHD):
            """
            Create gentle over steep layer for analysis (Graham)
            :param inWatershed: 
            :param inDEM: 
            :param inSlope50: 
            :param inPerimeter: 
            :param inFWAWSHD: 
            :return: 
            """
            
            arcpy.env.workspace = fgdbLoc
            arcpy.env.cellSize = inDEM
            arcpy.env.snapRaster = inDEM
            # create steep slopes library location
            ss_lib_fgdb_loc = os.path.join(libfgdbLoc + '\\steep_slopes')
            # if steep slopes library location does not exist create it
            if not arcpy.Exists(ss_lib_fgdb_loc):
                # set object to test
                obj_fgdb = CEA_Module_NB.FGDB_utils(BaseFolder)
                ss_lib_fgdb_loc = obj_fgdb.make_FGDB(sOutputLoc, setOutputlibraryFGDB, 'steep_slopes')
            
            # if the poly
            if arcpy.Exists(ss_lib_fgdb_loc + "\\Gentle_over_steep_coupled_300m_final_poly"):
                print (ss_lib_fgdb_loc + "\\Gentle_over_steep_coupled_300m_final_poly already exists not recreating analysis")
                dataSourceDict['SteepCoupled_poly'] = ss_lib_fgdb_loc + "\\Steep_Coupled_Slopes_poly"
                dataSourceDict['GOS'] = ss_lib_fgdb_loc + "\\Gentle_over_steep_coupled_300m_final_poly"
                
            if not arcpy.Exists(ss_lib_fgdb_loc + "\\Gentle_over_steep_coupled_300m_final_poly"):
                print( '\nStarting raster analysis to define gentle over steep...')
                print( ' ')
                print ('Filtering Grid Slope 50')
                neighborhood = NbrRectangle(3, 3, "CELL")  # set for use in functions below
                
                # The first portion here is not really used but was kept for potential future changes
                print ('Finding Upper area over all steep slopes (Gentle over steep)')
                print(inSlope50)
            
                
                grid_slope50_sum_filter = FocalStatistics(inSlope50, neighborhood, "SUM", "")

                grid_slope50_new = Reclassify(grid_slope50_sum_filter, "Value", RemapRange([[0, 4, 0], [5, 9, 1]]))
                grid_slope50_new_null = Reclassify(grid_slope50_new, "Value", RemapValue([[1, 1]]), "NODATA")
                DEM_SLOPE_50 = ExtractByMask(inDEM, grid_slope50_new_null)
                grid_slope50_new_focal_mean = FocalStatistics(grid_slope50_new, neighborhood, "MEAN", "")
                grid_slope50_edge = Reclassify(grid_slope50_new_focal_mean, "Value", RemapRange([[0.1, 0.5, 1]]), "NODATA")
                dem_slope_50_edge = ExtractByMask(inDEM, grid_slope50_edge)
                grid_slope50_median = FocalStatistics(DEM_SLOPE_50, neighborhood, "MEDIAN", "")
                out_upper_elev = Minus(dem_slope_50_edge, grid_slope50_median)
                Upper_area_slope_50 = Reclassify(out_upper_elev, "Value", RemapRange([[0, 100, 1]]), "NODATA")
                # The upper area of all the slope 50. Not really used but kept in the analysis
                Upper_area_slope_50.save(libfgdbLoc + "\\Upper_area_slope_50")
                print ('Done finding slopes near streams (Gentle over steep)')
                
                # find slope 50 within 50-70meters of streams
                print ('Start finding steep slopes near streams (Gentle over steep coupled)')

                arcpy.PolylineToRaster_conversion("fwa_perimeter", "OBJECTID", libfgdbLoc + "\\FWA_STREAMS_RAST", '', '', "25")
                
                fwa_streams_rast_no_null = Con(IsNull(libfgdbLoc + "\\FWA_STREAMS_RAST"), 0, libfgdbLoc + "\\FWA_STREAMS_RAST")
                print ('Reclassifying streams to 1 and other areas to null')
                fwa_streams_rast_1 = Reclassify(fwa_streams_rast_no_null, "Value", RemapRange([[1, 9999999, 5]]), "DATA")
                streams_slope50_rast = Plus(grid_slope50_new, fwa_streams_rast_1)
                streams_slope50_rastrcls = Reclassify(streams_slope50_rast, "Value", RemapRange([[5, 999999, 2]]), "DATA")
                grid_slope50_remap = Reclassify(streams_slope50_rastrcls, "Value", RemapValue([[1, 1], [2, 2]]), "NODATA")
                grid_slope50_remap_expand = Expand(grid_slope50_remap, 2, [2])
                reclass_expand = Reclassify(grid_slope50_remap_expand, "Value", RemapRange([[2, 2, 1]]), "NODATA")
                slope50_within_50m = Times(reclass_expand, grid_slope50_new_null)
                # steep 50 plus slopes within 50-75 meters of a stream
                slope50_within_50m.save(libfgdbLoc + "\\slope50_within_50m")
                print ('Done finding slopes near streams (Gentle over steep coupled)')
                
                print ('Finding steep coupled slopes to streams and associated gentle over steep (Gentle over steep coupled)')
                grid_slope50_innernull = Reclassify(grid_slope50_new, "Value", RemapRange([[0, 0, 1]]), "NODATA")
                dem_slope_50_dir = FlowDirection(DEM_SLOPE_50)
                slope_50_watershed = Watershed(dem_slope_50_dir, slope50_within_50m, "Value")
                # The flow of water upward in slope 50 that are coupled with a stream.
                # (Slope 50 watersheds that are withing 50-75 meters of a stream.
                slope_50_watershed.save(libfgdbLoc + "\\Steep_Coupled_Slopes")
                
                # convert to polygon layer
                arcpy.RasterToPolygon_conversion(libfgdbLoc + "\\Steep_Coupled_Slopes",
                                                ss_lib_fgdb_loc + "\\Steep_Coupled_Slopes_poly", "NO_SIMPLIFY", "VALUE")
                # outputs steep coupled slopes poly.
                dataSourceDict['SteepCoupled_poly'] = ss_lib_fgdb_loc + "\\Steep_Coupled_Slopes_poly"
                
                dem_slope_50_2 = ExtractByMask(inDEM, slope_50_watershed)
                slope_50_watershed_no_null = Con(IsNull(slope_50_watershed), 0, slope_50_watershed)
                grid_slope50_new_focal_mean = FocalStatistics(slope_50_watershed_no_null, neighborhood, "MEAN", "")
                grid_slope50_edge_2 = Reclassify(grid_slope50_new_focal_mean, "Value", RemapRange([[0.1, 0.5, 1]]), "NODATA")
                dem_slope_50_edge_2 = ExtractByMask("DEM_GRID", grid_slope50_edge_2)
                grid_slope50_median_2 = FocalStatistics(dem_slope_50_2, neighborhood, "MEDIAN", "")
                upper_elevation_2 = Minus(dem_slope_50_edge_2, grid_slope50_median_2)
                upper_area_slope_50_2 = Reclassify(upper_elevation_2, "Value", RemapRange([[0, 100, 1]]), "NODATA")
                upper_area_slope_50_2.save(libfgdbLoc + "\\Upper_area_Steep_Coupled_Slopes")
                # Set a layer of the upper edge to have value of 1 and all other areas null
                dem_grid_50_out = Times(inDEM, grid_slope50_innernull)
                dem_grid_50_out_dir = FlowDirection(dem_grid_50_out, "NORMAL")

                print ('Making Watersheds for gentle over steep')
                gentle_over_steep_coupled_final = Watershed(dem_grid_50_out_dir, upper_area_slope_50_2)
                # Outputs gentle over steep coupled reaster
                gentle_over_steep_coupled_final.save(libfgdbLoc + "\\gentle_over_steep_coupled_final")
                # converts the steep coupled raster
                arcpy.RasterToPolygon_conversion(libfgdbLoc + "\\gentle_over_steep_coupled_final",
                                                ss_lib_fgdb_loc + "\\gentle_over_steep_coupled_final_poly", "NO_SIMPLIFY",
                                                "VALUE")
                
                # convert
                arcpy.PolygonToLine_management(inFWAWSHD, ss_lib_fgdb_loc + "\\fwa_watersheds_line")
                arcpy.PolylineToRaster_conversion(ss_lib_fgdb_loc + "\\fwa_watersheds_line", "OBJECTID",
                                                libfgdbLoc + "\\fwa_watersheds_line_rast", '', '', "25")
                fwa_watersheds = Reclassify(libfgdbLoc + "\\fwa_watersheds_line_rast", "Value", RemapRange([[1, 9999999, 2]]),
                                            "DATA")
                fwa_watersheds2 = Con(IsNull(fwa_watersheds), 0, fwa_watersheds)
                # fwa_watersheds2.save("fwa_watersheds_line_rast_reclass")
                
                # create distance grid
                upper_area_slope_50_3 = Con(IsNull(upper_area_slope_50_2), 0, upper_area_slope_50_2)
                streams_slope50_rast = Plus(fwa_watersheds2, upper_area_slope_50_3)
                # streams_slope50_rast.save("streams_slope50_rast")
                
                fwa_watersheds_for_dist = Reclassify(streams_slope50_rast, "Value", RemapValue([[0, "NODATA"], [3, 2]]), "DATA")
                # fwa_watersheds_for_dist.save("fwa_watersheds_for_dist")
                
                # Make the mask layer to control distance
                gentle_oversteep = Con(IsNull(libfgdbLoc + "\\gentle_over_steep_coupled_final"), 0,
                                    libfgdbLoc + "\\gentle_over_steep_coupled_final")
                gos_watershed_rast = Plus(gentle_oversteep, fwa_watersheds2)
                # gos_watershed_rast.save("gos_watershed_rast")
                
                fwa_watersheds_mask = Reclassify(gos_watershed_rast, "Value",
                                                RemapValue([[0, "NODATA"], [2, "NODATA"], [3, "NODATA"]]), "DATA")
                fwa_watersheds_mask.save(libfgdbLoc + "\\fwa_watersheds_mask")
                
                fwa_watersheds_cost = Reclassify(gos_watershed_rast, "Value",
                                                RemapValue([[0, "NODATA"], [2, 99999], [3, 99999]]), "DATA")
                # fwa_watersheds_cost.save("fwa_watersheds_cost")
                
                arcpy.env.mask = libfgdbLoc + "\\fwa_watersheds_mask"
                # cost distance
                # outEucAlloc = EucAllocation(fwa_watersheds_for_dist, 300, "fwa_watersheds_mask")
                # outEucAlloc.save("GOS_EUC_Allocation")
                cost_alloc_out = CostAllocation(fwa_watersheds_for_dist, fwa_watersheds_cost, 300)
                cost_alloc_out.save(libfgdbLoc + "\\Gentle_over_steep_coupled_300m_final")
                
                arcpy.RasterToPolygon_conversion(libfgdbLoc + "\\Gentle_over_steep_coupled_300m_final",
                                                ss_lib_fgdb_loc + "\\Gentle_over_steep_coupled_300m_final_poly",
                                                "NO_SIMPLIFY", "VALUE")
                dataSourceDict['GOS'] = ss_lib_fgdb_loc + "\\Gentle_over_steep_coupled_300m_final_poly"
                    
            print ('Finshed finding steep coupled slopes to streams and associated gentle over steep (Gentle over steep coupled)')
            print( ' ')
            print ('Starting steep coupled slope summary')
            sc_resultant = "Steep_coupled_resultant"
            if arcpy.Exists('Steep_coupled_resultant'):
                print ("Steep_coupled_resultant already exists not recreating analysis")
            if not arcpy.Exists('Steep_coupled_resultant'):
                arcpy.Identity_analysis(inWatershed, ss_lib_fgdb_loc + "\\Steep_Coupled_Slopes_poly", sc_resultant)
                
                obj_sc50 = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_sc50.GetGeometryField(sc_resultant)
                area_field = geom_tuple[0]
                # add area fields and
                arcpy.AddField_management(sc_resultant, 'In_50_ha', 'DOUBLE')
                # arcpy.AddField_management(sc_resultant,'All_ha','DOUBLE')
                # arcpy.CalculateField_management(sc_resultant,'All_ha',"!shape.area@hectares!","PYTHON3")
                # select only polygons with 60 percent slope
                arcpy.MakeFeatureLayer_management(sc_resultant, "SC50LYR", wsLinkFld + " > 0 and GRIDCODE = 1")
                arcpy.CalculateField_management("SC50LYR", 'In_50_ha', "!" + area_field + "!/10000", "PYTHON3")
                arcpy.Delete_management('SC50LYR')
                
            if not arcpy.Exists('frq_score_Steepcoup'):
                # arcpy.MakeFeatureLayer_management(sc_resultant,"SC50LYR")
                arcpy.Frequency_analysis(sc_resultant, 'frq_score_Steepcoup', [wsLinkFld, wsAreaHa], ['In_50_ha'])
                # figure out percentage of area of watershed in
                arcpy.AddField_management("frq_score_Steepcoup", 'Percent_steep_coupled', 'DOUBLE')
                # arcpy.CalculateField_management("SC50_STATS_TABLE",'Percent_steep_coupled',
                # "(!In_50_ha!/!All_ha!) * 100","PYTHON3")
                arcpy.CalculateField_management("frq_score_Steepcoup", 'Percent_steep_coupled',
                                                "(!In_50_ha!/!" + wsAreaHa + "!) * 100", "PYTHON3")
                # arcpy.CopyRows_management("SC50_STATS_TABLE", "frq_score_Steepcoup")
                
            objfcutil = CEA_Module_NB.featureclass_utils()
            # fieldskeep = [wsLinkFld,'Percent_steep_coupled']
            # objfcutil.delete_fields("frq_score_Steepcoup", fieldskeep)
            
            # join the slope 60 stats table
            join_fields = ['Percent_steep_coupled']
            print ('Joining Steep coupled data to Watershed Stats table')
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_score_Steepcoup", wsLinkFld, join_fields)
                
            print ('...DONE Steep Coupled Slopes Summary.')
            print (' ')
            print ('...DONE Creating Gentle over steep Features.')
            __PrintTime(deltaTime)    


        def roads_Analysis(inWatershed, inRoads, inRiparian, insteepSlopes, inMaps50k):
            """
            Roads Analysis - Extent, Close to Water, On Steep Coupled Slopes (Gail Smith)
            NEED data for the following variables:
            (1) SteepCpldSlope = Steep coupled slopes from steepCoupledSlopes function
            (2) StrmBuffM = 50m stream buffer - or should I create in THIS function
            WHSE_BASEMAPPING.NTS_50K_GRID
            need to make seperate analysis file geodatabase for stream buffers...
            :param inWatershed: 
            :param inRoads: 
            :param inRiparian: 
            :param insteepSlopes: 
            :param inMaps50k: 
            :return: 
            """
            arcpy.env.workspace = fgdbLoc
            print ('\nStarting Roads Analysis...')
            sum_tab_roads = 'frq_score_RdExtent'
            if not arcpy.Exists(sum_tab_roads):
                print ('Intersecting Roads with Watershed RUs...')
                # Intersect roads with Watershed RUs - this will be used to determine extent of rds within each RU,
                # extent of rds within 50m stream buffer and extent of rds within steep coupled slope areas for each RU
                arcpy.Intersect_analysis([inRoads, inWatershed], 'Rds_WRU', 'ALL', '', 'INPUT')

            obj_fc = CEA_Module_NB.featureclass_utils()
            geom_tuple = obj_fc.GetGeometryField('Rds_WRU')
            length_field = geom_tuple[1]
                
            if not arcpy.Exists(sum_tab_roads): 
                print ('Extent of Roading'   )  
                print ('  Running Road Extent frequency TabRds...')
                # Determine Extent of Roads and Calculate Density of Rds / Reporting Unit
                arcpy.Frequency_analysis('Rds_WRU', sum_tab_roads, [wsLinkFld, wsNameFld, wsAreaKM2], length_field)
                # Calculate rds per reporting unit
                if not arcpy.ListFields(sum_tab_roads, 'Rds_Extent'):
                    print ('    adding Extent field...')
                    arcpy.AddField_management(sum_tab_roads, 'Rds_Extent', 'Double', '', '2')
                print ('    calculating extent of rds/RU...')
                arcpy.CalculateField_management(sum_tab_roads, 'Rds_Extent',
                                                "(!" + length_field + "!/1000) / !" + wsAreaKM2 + "!", "PYTHON3")

            # -----------------------------------------------------------------------------
            # Determine extent of roads that are on steep coupled slopes / Reporting unit
            # -----------------------------------------------------------------------------
            print ('Roads on Steep Coupled Slopes...')
            # Intersect steep coupled slopes with roads_WRU
            sum_roads_sc_slps = 'frq_score_RdsStpSlps'
            if not arcpy.Exists(sum_roads_sc_slps): 
                print ('  Intersecting StpSlps with Rds_RU...')
                arcpy.Intersect_analysis([insteepSlopes, 'Rds_WRU'], 'Rds_StpSlps_RU', "ALL", "", "INPUT")
                obj_fc = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_fc.GetGeometryField('Rds_StpSlps_RU')
                length_field = geom_tuple[1]
            if not arcpy.Exists(sum_roads_sc_slps):
                # sum length of rds within steep coupled slopes per RU
                print ('  Running frequency sum_roads_sc_slps...')
                arcpy.Frequency_analysis('Rds_StpSlps_RU', sum_roads_sc_slps, [wsLinkFld, wsNameFld, wsAreaKM2], length_field)
                
                # calculate Rds within Steep coupled slopes per / RU
                if not arcpy.ListFields(sum_roads_sc_slps, 'RdsSlps_Ext_KM2'):
                    print ('adding Extent field...')
                    arcpy.AddField_management(sum_roads_sc_slps, 'RdsSlps_Ext_KM2', 'Double', '', '2')
                print ('    calculating extent of rds/RU...')
                arcpy.CalculateField_management(sum_roads_sc_slps, 'RdsSlps_Ext_KM2',
                                                "(!" + length_field + "!/1000)/ !" + wsAreaKM2 + "!", "PYTHON3")

            # -----------------------------------------------------------------------------
            # Determine extent of roads that are within 50m stream buffer / Reporting unit
            # -----------------------------------------------------------------------------
            print ('Preparing data for roads near buffered water.')
            # make stream buffers in library
            obj_fgdb = CEA_Module_NB.FGDB_utils(BaseFolder)
            buf_data_location = obj_fgdb.make_FGDB(sOutputLoc, setOutputlibraryFGDB, 'strm_buf_50')
            
            # return list of mapsheets in the area of interest
            obj_list = CEA_Module_NB.extractData()
            map_list = obj_list.return_list_items_in_field(dataSourceDict['MAPS50K'], 'MAP_TILE')
            
            appenddataname = 'Rds_StrmBuff_RU_all'
            appenddatanameLocation = os.path.join(buf_data_location, appenddataname)
            if not arcpy.Exists(appenddatanameLocation):
                mapsheets50k = r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\Maps50K.gdb\WHSE_BASEMAPPING_NTS_50K_GRID'
                for mapsheet in map_list:
                    print ('creating tiles to analyze map ' + mapsheet)
                    arcpy.MakeFeatureLayer_management(mapsheets50k, 'mapsheetLyr', '"MAP_TILE" = ' + "'" + mapsheet + "'")
                    objSel = CEA_Module_NB.extractData()
                    if not arcpy.Exists(os.path.join(buf_data_location, 'Rds_StrmBuff_RU_all')):
                        if not arcpy.Exists(os.path.join(buf_data_location, 'Rds_StrmBuff_RU_'+mapsheet)):
                            objSel.extract_by_Distance(inRiparian, 'mapsheetLyr',
                                                    os.path.join(buf_data_location, 'streamlayer' + mapsheet), 50)
                            arcpy.RepairGeometry_management(os.path.join(buf_data_location, 'streamlayer' + mapsheet))
                            arcpy.Buffer_analysis(os.path.join(buf_data_location, 'streamlayer' + mapsheet),
                                                os.path.join(buf_data_location, 'Stream_buf_50' + mapsheet), '50',
                                                'FULL', 'ROUND', 'ALL')
                            arcpy.RepairGeometry_management(os.path.join(buf_data_location, 'Stream_buf_50' + mapsheet))
                            arcpy.Clip_analysis(os.path.join(buf_data_location, 'Stream_buf_50' + mapsheet), 'mapsheetLyr',
                                                os.path.join(buf_data_location, 'CLP_Stream_buf_50_' + mapsheet))
                            arcpy.Intersect_analysis(['Rds_WRU',
                                                    os.path.join(buf_data_location, 'CLP_Stream_buf_50_' + mapsheet)],
                                                    os.path.join(buf_data_location, 'Rds_StrmBuff_RU_' + mapsheet),
                                                    "ALL", "", "INPUT")
                            arcpy.DeleteField_management(os.path.join(buf_data_location, 'Rds_StrmBuff_RU_'+mapsheet),
                                                        'FID_' + 'CLP_Stream_buf_50_' + mapsheet)
                    #         clean up files - undeleted
                    #         arcpy.Delete_management(os.path.join(buf_data_location,'streamlayer' + mapsheet))
                    #         arcpy.Delete_management(os.path.join(buf_data_location,'Stream_buf_50'+mapsheet))
                    #         arcpy.Delete_management(os.path.join(buf_data_location,'CLP_Stream_buf_50_'+mapsheet))
                    # arcpy.Delete_management('mapsheetLyr')

                # make appended coverage
                # append buffers together.
                objappend = CEA_Module_NB.analysis_utils()
                # appenddataname = 'StrmBuff_50m_all'
                # appenddatanameLocation = os.path.join(buf_data_location,appenddataname)
                # if not arcpy.Exists(appenddatanameLocation):
                #    print 'Appending to create ' + appenddataname
                #    objappend.append_data(buf_data_location, appenddataname, 'CLP_Stream_buf_50_', map_list, "POLYGON")
                
                print ('Appending to create ' + appenddataname)
                objappend.append_data(buf_data_location, appenddataname, 'Rds_StrmBuff_RU_', map_list, "POLYLINE")

            print ('Roads Close to Water...')

            sum_strm_buff_rds = 'frq_score_RdsStrBuff'
            # Sum length of rds within 50m stream buffers per RU
            if not arcpy.Exists(sum_strm_buff_rds):
                print( '  Running frequency TabRds...')
                obj_fc = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_fc.GetGeometryField(appenddatanameLocation)
                length_field = geom_tuple[1]
                arcpy.Frequency_analysis(appenddatanameLocation, sum_strm_buff_rds,
                                        [wsLinkFld, wsNameFld, wsAreaKM2], length_field)
                # calculate Rds within 50m stream buffer per / RU
                if not arcpy.ListFields(sum_strm_buff_rds, 'RdsStrmB_Ext_KM2'):
                    print ('    adding Extent field...')
                    arcpy.AddField_management(sum_strm_buff_rds, 'RdsStrmB_Ext_KM2', 'Double', '', '2')
                print ('    calculating extent of rds/RU...')
                arcpy.CalculateField_management(sum_strm_buff_rds, 'RdsStrmB_Ext_KM2',
                                                "(!" + length_field + "!/1000)/ !" + wsAreaKM2 + "!", "PYTHON3")

            # print '  Cleanup...'
            # delete_list = ['Rds_StrmBuff_RU', 'Rds_StpSlps_RU', 'Rds_WRU']
            # for input_Layer in delete_list:
            #    if arcpy.Exists(input_Layer):
            #        arcpy.Delete_management(input_Layer)
            
            # Join final scores to master stats table
            arcpy.env.workspace = fgdbLoc
            table_list = ['frq_score_RdExtent', 'frq_score_RdsStrBuff', 'frq_score_RdsStpSlps']
            for frqtable in table_list:
                print ('Joining fields from ' + frqtable)
                # objfcutil = CEA_Module.featureclass_utils()
                # fieldskeep = [wsLinkFld,'Rds_Extent','RdsSlps_Ext_KM2','RdsStrmB_Ext_KM2']
                # join road extent
                if frqtable == 'frq_score_RdExtent':
                    keepfield = ['Rds_Extent']
                    fieldstr = 'Rds_Extent'
                if frqtable == 'frq_score_RdsStrBuff':
                    keepfield = ['RdsStrmB_Ext_KM2']
                    fieldstr = 'RdsStrmB_Ext_KM2'
                if frqtable == 'frq_score_RdsStpSlps':
                    keepfield = ['RdsSlps_Ext_KM2']
                    fieldstr = 'RdsSlps_Ext_KM2'
                # print arcpy.env.workspace
                if not arcpy.ListFields('Watershed_STATS_TABLE', fieldstr):
                    print ('Joining field ' + fieldstr)
                    # objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, frqtable, wsLinkFld, keepfield)
                    arcpy.JoinField_management('Watershed_STATS_TABLE', wsLinkFld, frqtable, wsLinkFld, keepfield)
                else:
                    print ('Skipping adding field because it already exists ' + fieldstr)
            
            print ('...DONE Roads Analysis.')
            __PrintTime(deltaTime)    


        def harvest_gos(inWatershed, inGOS, Harvested):
            """
            Harvest Disturbance on Gentle over Steep
            Note that this includes any Harvesting in the last 75 yrs. (or in this case, as far back as VRI goes.
            :param inWatershed:
            :param inGOS: WHSE_MINERAL_TENURE.GEOL_QUATERNARY_POLY
            :param Harvested:
            :return:
            """
            print ('\nStarting harvest_gos analysis...')
            if not arcpy.Exists('RU_Harvest_GOS'):
                arcpy.Intersect_analysis([Harvested, inGOS], 'Harvest_GOS', "NO_FID", "0.1", "INPUT")
                arcpy.Intersect_analysis(['Harvest_GOS', inWatershed], 'RU_Harvest_GOS', "NO_FID", "0.1", "INPUT")
                arcpy.Delete_management('Harvest_GOS')
            
            # sum_tab_area = 'sumGOS'
            sum_tab_final = 'frq_score_Harvest_GOS'
            if not arcpy.Exists('frq_score_Harvest_GOS'):
                # inWatershed must contain a wsAreaM2 field
                obj_gos = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_gos.GetGeometryField("RU_Harvest_GOS")
                area_field = geom_tuple[0]
                print ('  Frequency on Input Layer by RU')
                # Table 1
                arcpy.Frequency_analysis('RU_Harvest_GOS', sum_tab_final, [wsLinkFld, wsAreaM2], area_field)
                if not arcpy.ListFields(sum_tab_final, 'GOS_Score_Percent'):
                    arcpy.AddField_management(sum_tab_final, 'GOS_Score_Percent', 'Double', '', '2')
                # expression = "(["+areaItem+"]/["+wsAreaM2+"])*100"   # percentage score
                # arcpy.CalculateField_management(sum_tab_final, 'GOS_Score_Percent', expression)
                # Python 64
                arcpy.CalculateField_management(sum_tab_final, 'GOS_Score_Percent',
                                                "(!" + area_field + "!/!" + wsAreaM2 + "!) * 100", "PYTHON3")
                # Table 2 - Final
                # arcpy.Frequency_analysis(sum_tab_area, sum_tab_final, [wsLinkFld], ['GOS_Score'])
                
            objfcutil = CEA_Module_NB.featureclass_utils()
            print ('joining harvest GOS to watershed stats table')
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, sum_tab_final, wsLinkFld, ['GOS_Score_Percent'])
                
            print ('...DONE Harvest on GOS.')
            __PrintTime(deltaTime)    


        def stream_order_length(inWatershed, inRiparian, inPrivateIR, inLogged, inRange):
            """
            Stream Order Length
            Loop for Logged Riparian, Grazing, and Private Land (Gail Smith)

            Revised 11-July-2014  to use Indian Reserves in combination with Private (Private_IR)

            WARNING!! Make sure to check your results!! It has been found that some of the mapsheets are not processed properly,
            and are therefore missing features. (eg. for Kamloops)

            :param inWatershed:
            :param inRiparian:
            :param inPrivateIR:
            :param inLogged:
            :param inRange:
            :return:
            """
            arcpy.env.workspace = fgdbLoc
            print ('\nStarting Stream Order Length Analysis...'  )
            wght_lu_tab = r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\VRI_BNDY.gdb\StreamWght_lookup'
            
            if not arcpy.ListFields(inRiparian, 'Stream_Wght'):
                print ('   join Stream_Wght field to FWA Streams...')
                arcpy.JoinField_management(inRiparian, 'STREAM_ORDER', wght_lu_tab, 'STREAM_ORD', 'Stream_Wght')
            if not arcpy.Exists('RU_Stream'):
                print ('  Intersect WSs and inStreams then calc stream order length by Reporting Unit')
                arcpy.Intersect_analysis([inWatershed, inRiparian], 'RU_Stream', "NO_FID", "0.1", "INPUT")

            obj_fc = CEA_Module_NB.featureclass_utils()
            geom_tuple = obj_fc.GetGeometryField("RU_Stream")
            length_field = geom_tuple[1]
            
            if not arcpy.Exists('RULgth_Table'):
                print ('   Create RUWghtLgth_Table - Total stream length by Weight by watershed reporting unit')
                # Table 1 - create table with total stream length by Reporting Unit - used further down
                arcpy.arcpy.Frequency_analysis('RU_Stream', 'RULgth_Table', [wsLinkFld], length_field)
            if not arcpy.ListFields('RULgth_Table', 'RULgth'):
                arcpy.AddField_management('RULgth_Table', 'RULgth', 'Double', '', '2')
                arcpy.CalculateField_management('RULgth_Table', 'RULgth', "!" + length_field + "!", "PYTHON3")
            
            # Table 2 - create table with total stream length by Weight by Reporting Unit - used further down
            if not arcpy.Exists('RUWghtLgth_Table'):
                arcpy.Frequency_analysis('RU_Stream', 'RUWghtLgth_Table', [wsLinkFld, 'Stream_Wght'], length_field)
            if not arcpy.ListFields('RUWghtLgth_Table', 'RUWghtLgth'):
                arcpy.AddField_management('RUWghtLgth_Table', 'RUWghtLgth', 'Double', '', '2')
                arcpy.CalculateField_management('RUWghtLgth_Table', 'RUWghtLgth', "!" + length_field + "!", "PYTHON3")
            if not arcpy.ListFields('RUWghtLgth_Table', 'RULgth'):
                print ('  ...join tables above and calculate RUwght_PCNT')
                arcpy.JoinField_management('RUWghtLgth_Table', wsLinkFld, 'RULgth_Table', wsLinkFld, 'RULgth')
            if not arcpy.ListFields('RUWghtLgth_Table', 'RUWght_PCNT'):
                arcpy.AddField_management('RUWghtLgth_Table', 'RUWght_PCNT', 'Double', '', '2')
                arcpy.CalculateField_management('RUWghtLgth_Table', 'RUWght_PCNT', "!RUWghtLgth! / !RULgth!", "PYTHON3")
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # need to loop clip the buffers into library
            obj_fgdb = CEA_Module_NB.FGDB_utils(BaseFolder)
            buf_data_location = obj_fgdb.make_FGDB(sOutputLoc, setOutputlibraryFGDB, 'priv_logged_buf')
            
            # return list of mapsheets in the area of interest
            obj_list = CEA_Module_NB.extractData()
            map_list = obj_list.return_list_items_in_field(dataSourceDict['MAPS50K'], 'MAP_TILE')
            
            mapsheets50k = r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\Maps50K.gdb\WHSE_BASEMAPPING_NTS_50K_GRID'
            
            data_list = []
            # if arcpy.Exists('PrivateIR'):
            # if 'PrivIR' in dataSourceDict:
            # privir_count=int(arcpy.GetCount_management(fgdbLoc + '\\source\\Private_IR')[0])
            if int(arcpy.GetCount_management(os.path.join(fgdbLoc,'Source','Private_IR'))[0])>0:
                data_list.append('PrivateIR')
            # if arcpy.Exists('Logged'):
            # if 'Harvested' in dataSourceDict:
            # logged_fc=arcpy.ListFeatureClasses('Harvested')[0]
            # logged_fc=logged_fc.name
            # print(logged_fc)
            if int(arcpy.GetCount_management(os.path.join(fgdbLoc,'Source','Harvested'))[0])>0:
                print('Number of harvested features')
                print(int(arcpy.GetCount_management(os.path.join(fgdbLoc,'Source','Harvested'))[0]))
                data_list.append('Logged')
            print('==========Contents of data list==========')
            print(data_list)
            print('==========Contents of data list==========')
            # data_list=[]
            # if inPrivateIR != None:
            #     data_list.append('PrivateIR')
            # if inLogged != None:
            #     data_list.append('Logged')

            for inLayer in data_list:
                map_list_not_null = []
                if inLayer == 'PrivateIR':
                    buf_dist = '20'
                    sourceinLayer = inPrivateIR
                if inLayer == 'Logged':
                    buf_dist = '30'
                    sourceinLayer = inLogged
                appenddataname = 'RU_Stream_' + inLayer
                # appenddatanameLocation = os.path.join(buf_data_location,appenddataname)
                appenddatanameLocation = os.path.join(fgdbLoc, appenddataname)

                if not arcpy.Exists(appenddatanameLocation):
                    for mapsheet in map_list:
                        if not arcpy.Exists(os.path.join(buf_data_location, 'RU_Stream_'+inLayer + '_' + mapsheet)):
                            print ('Making tiled buffer for ' + inLayer + '  ' + mapsheet)
                            arcpy.MakeFeatureLayer_management(mapsheets50k, 'mapsheetLyr',
                                                            '"MAP_TILE" = ' + "'" + mapsheet + "'")
                            outCS = arcpy.SpatialReference('NAD 1983 BC Environment Albers')
                            arcpy.management.Project('mapsheetLyr', 'mapsheetLyr', outCS)
                            print('repair geonetry for mapshtlyr')
                            arcpy.management.RepairGeometry(sourceinLayer)
                            arcpy.Clip_analysis(sourceinLayer, 'mapsheetLyr',
                                                os.path.join(buf_data_location, inLayer + '_' + mapsheet))
                            count = int(arcpy.GetCount_management(os.path.join(buf_data_location, inLayer + '_' + mapsheet)).getOutput(0))
                            print( 'Initial Clip count:', count)
                            if count == 0:
                                print ('NO FEATURES FOUND for '+inLayer+' IN MAPSHEET '+mapsheet+'!   CHECK RESULTS!!')
                            else:
                                print ('Buffering...')
                                map_list_not_null.append(mapsheet)
                                arcpy.Buffer_analysis(os.path.join(buf_data_location, inLayer + '_' + mapsheet),
                                                    os.path.join(buf_data_location, inLayer + '_buf_' + buf_dist + '_' + mapsheet),
                                                    buf_dist, 'FULL', 'ROUND', 'ALL')
                                arcpy.RepairGeometry_management(os.path.join(buf_data_location, inLayer + '_buf_' + buf_dist + '_' + mapsheet))
                                # Re-Clip to remove buffer outside of tile, before appending
                                arcpy.Clip_analysis(os.path.join(buf_data_location, inLayer + '_buf_' + buf_dist + '_' + mapsheet),
                                                    'mapsheetLyr', os.path.join(buf_data_location, inLayer + '_buf_' + buf_dist + '_clp_' + mapsheet))
                                arcpy.Intersect_analysis(['RU_Stream', os.path.join(buf_data_location, inLayer + '_buf_' + buf_dist + '_' + mapsheet)], os.path.join(buf_data_location, 'RU_Stream_'+inLayer + '_' + mapsheet), "ALL", "", "INPUT")

                                # Check for null result
                                count = int(arcpy.GetCount_management(os.path.join(buf_data_location, inLayer + '_buf_' + buf_dist + '_' + mapsheet)).getOutput(0))
                                print ('Initial Intersect count:', count)
                                if count == 0:
                                    print ('WARNING! NO INTERSECT RESULTS FOUND for '+inLayer+' IN MAPSHEET '+mapsheet+'! CHECK RESULTS!!')
                                    # sys.exit() NB Update #1
                                    map_list_not_null.remove(mapsheet)

                            # Keeping Buffered Data for QA - next 4 lines
                            # if arcpy.Exists('mapsheetLyr'):
                                # arcpy.Delete_management('mapsheetLyr')
                            # if arcpy.Exists(os.path.join(buf_data_location,inLayer + '_' + mapsheet)):
                                # arcpy.Delete_management(os.path.join(buf_data_location,inLayer + '_' + mapsheet))
                                
                            # if arcpy.Exists(os.path.join(buf_data_location,inLayer + '_buf_' + buf_dist+ '_' + mapsheet)):
                            #    arcpy.Delete_management(os.path.join(buf_data_location,
                            #    inLayer + '_buf_' + buf_dist+ '_' + mapsheet))
                        else:
                            map_list_not_null.append(mapsheet)
                            
                    for mapsheet in map_list_not_null:
                        obj_list = CEA_Module_NB.featureclass_utils()
                        field_list = obj_list.return_field_list(os.path.join(buf_data_location,
                                                                            'RU_Stream_'+inLayer + '_' + mapsheet))
                        del_field = "FID_" + inLayer + '_buf_' + buf_dist + '_' + mapsheet
                        if del_field in field_list:
                            print ('Deleting field ' + del_field)
                            arcpy.DeleteField_management(os.path.join(buf_data_location, 'RU_Stream_'+inLayer + '_' + mapsheet),
                                                        del_field)
                            
                    objappend = CEA_Module_NB.analysis_utils()
                    print ('Appending to create ' + appenddataname         )   
                    # objappend.append_data(buf_data_location, appenddataname, inLayer + '_buf_' + buf_dist+ '_clp_',
                    #                       map_list, "POLYGON")
                    objappend.append_data(fgdbLoc, appenddataname, os.path.join(buf_data_location, 'RU_Stream_'+inLayer + '_'),
                                        map_list_not_null, "POLYLINE")
                    # arcpy.RepairGeometry_management(os.path.join(buf_data_location,appenddataname))
                    # after appended together delete file from the library
                    '''
                    ####keep all files
                    for mapsheet in map_list:
                        if arcpy.Exists(os.path.join(buf_data_location,inLayer + '_buf_' + buf_dist+ '_clp_' + mapsheet)):
                            arcpy.Delete_management(os.path.join(buf_data_location,
                            inLayer + '_buf_' + buf_dist+ '_clp_' + mapsheet))
                else:
                    print (appenddataname+ ' already Exists.')
                '''
                # clean up files
                # delete_list = arcpy.ListFeatureClasses(buf_data_location+'\*_clp_*')
                # print 'Ready to delete:  '
                # for delit in delete_list:
                #    arcpy.Delete_management(delit)
                '''
                if inLayer == 'PrivateIR':
                    if not arcpy.Exists('RU_Stream'+inLayer):
                        print ('    20m PrivateIR buffer/Identify with Reporting Units...')
                        #arcpy.Buffer_analysis (inPrivateIR, inLayer+'Buff', "20 Meters", "FULL","ROUND","ALL")
                    arcpy.Intersect_analysis(['RU_Stream', appenddatanameLocation], 'RU_Stream'+inLayer,
                    "NO_FID", "0.1", "INPUT")
                elif inLayer == 'Logged':
                    if not arcpy.Exists('RU_Stream'+inLayer):
                        print ('    30m Logged buffer/Identify with Reporting Units...')
                        arcpy.Intersect_analysis(['RU_Stream', appenddatanameLocation], 'RU_Stream'+inLayer,
                        "NO_FID", "0.1", "INPUT")
                '''
            
            # data_list = ['Logged', 'Range', 'PrivateIR']  # , 'Logged']   #Note that Logged and PrivateIR are buffered above
            # if inRange != None:
            #     data_list.append('Range')
            if arcpy.Exists(os.path.join(fgdbLoc,'Source','FTEN_Grazing')):
                if int(arcpy.GetCount_management(os.path.join(fgdbLoc,'Source','FTEN_Grazing'))[0])>0:
                    print('Number of Range features')
                    print(int(arcpy.GetCount_management(os.path.join(fgdbLoc,'Source','FTEN_Grazing'))[0]))
                    data_list.append('Range')

            arcpy.env.workspace = fgdbLoc
            for inLayer2 in data_list:
                print ('\n   Summary for: ', inLayer2)
                # Buffer input layer accordingly and 'Intersect' RU_Stream from above
                # arcpy.Buffer_analysis(inLogged, inLayer2+'Buff', "30 Meters","FULL","ROUND","ALL")
                if inLayer2 == 'Range':
                    if not arcpy.Exists('RU_Stream_'+inLayer2):
                        print ('    no Buffer needed & Identify with Reporting Units...')
                        # AddField for FAKE buffer flag - Buffer input layer accordingly and 'Intersect' RU_Stream from above
                        # arcpy.CopyFeatures_management(inRange, inLayer2)
                        arcpy.Intersect_analysis(['RU_Stream', inRange], 'RU_Stream_' + inLayer2, "NO_FID", "0.1", "INPUT")
                        
                
                if arcpy.Exists('RU_Stream_' + inLayer2):
                    sumTabBuff = 'sumStrBuff_' + inLayer2
                    sum_tab_final = 'frq_score_Stream_' + inLayer2

                    obj_fc = CEA_Module_NB.featureclass_utils()
                    geom_tuple = obj_fc.GetGeometryField('RU_Stream_' + inLayer2)
                    length_field = geom_tuple[1]
                    
                    if not arcpy.Exists(sum_tab_final):
                        
                        print ('  Determine % of weighted stream order by length in ', inLayer2)
                        # Table 1 - Frequency on Buffered Input Layer stream length / order / RU
                        # Table 1 - (stream weight x stream order length in cattle/private/logged) / stream order length in RU
                        arcpy.Frequency_analysis('RU_Stream_' + inLayer2, sumTabBuff,
                                                [wsLinkFld, 'Stream_Wght'], length_field)
                        arcpy.JoinField_management(sumTabBuff, wsLinkFld, 'RUWghtLgth_Table', wsLinkFld,
                                                ['RUWghtLgth', 'RUWght_PCNT'])  # RUWght_PCNT', "[RUWghtLgth]/[RULgth
                        if not arcpy.ListFields(sumTabBuff, inLayer2 + '_PCNT'):
                            arcpy.AddField_management(sumTabBuff, inLayer2 + '_PCNT', 'Double', '', '2')
                        # calculations are
                        # Shape_length (Stream length by stream weight sum within feature assessed Logged,PrivateIR,placer))
                        # by watershed
                        # RUWghtLgth. The sum of stream weight by watershed
                        # RUWght_PCNT. (weight length of streams(RUWghtLgth) / all stream length (RULgth)) by watershed
                        # STREAM_WGHT The coefficient weight attached to the stream class
                        # expression = "(( [STREAM_WGHT] *( [GEOMETRY_Length] / [RUWghtLgth] ))* [RUWght_PCNT] )*100"
                        # arcpy.CalculateField_management(sumTabBuff, inLayer2+'_PCNT', expression)
                        # Python 64
                        arcpy.CalculateField_management(sumTabBuff, inLayer2 + '_PCNT',
                                                        "(( !STREAM_WGHT! *( !" + length_field + "! / !RUWghtLgth! )) * !RUWght_PCNT! ) * 100",
                                                        "PYTHON3", "")
                        # Table 2
                        sumfield = inLayer2 + '_PCNT'
                        arcpy.Frequency_analysis(sumTabBuff, sum_tab_final, [wsLinkFld], sumfield)
                    
                        # keep only summary fields
                        objfcutil = CEA_Module_NB.featureclass_utils()
                        fieldskeep = [wsLinkFld, sumfield]
                        objfcutil.delete_fields(sum_tab_final, fieldskeep)
                    
                
                # objfcutil = CEA_Module_NB.featureclass_utils()
                # field_list = objfcutil.return_field_list('Watershed_STATS_TABLE')
                fieldstr = inLayer2 + '_PCNT'
                if not arcpy.ListFields('Watershed_STATS_TABLE', fieldstr):
                    print ('Joining field '+ fieldstr)
                    # objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, frqtable, wsLinkFld, keepfield )
                    arcpy.JoinField_management('Watershed_STATS_TABLE', wsLinkFld, sum_tab_final, wsLinkFld, [''+fieldstr+''])

            print ('...DONE Stream Order Length.')
            print( '*************WARNING******************')
            print ('**     Check your Results for Stream overlays !!!        **')
            print ('**************************************\n')
            __PrintTime(deltaTime)    


        def placer_ten(inWatershed, inRiparian, in_placer):
            """
            Placer Mining Tenures (Gail Smith)
            :param inWatershed: 
            :param inRiparian: 
            :param in_placer: 
            :return: 
            """


            if int(arcpy.GetCount_management(in_placer)[0]) == 0:
                print('No placer overlap')
                arcpy.AddField_management('Watershed_STATS_TABLE', 'Placer_Score', 'Double', '', '2')
                arcpy.CalculateField_management('Watershed_STATS_TABLE', 'Placer_Score', 0, "PYTHON3")
                return

            arcpy.env.workspace = fgdbLoc
            sum_tab_final = 'frq_score_Stream_Placer'
            if not arcpy.Exists('RU_Stream_Placer'):
                print ('\nStarting placer_ten analysis...')
                weight_lu_tab = str_lkup #r'C:\Users\cfolkers\Documents\WHPOR\Stage\VRI_BNDY.gdb\StreamWght_lookup'
                
                # add stream weight field
                if not arcpy.ListFields(inRiparian, 'Stream_Wght'):
                    arcpy.JoinField_management(inRiparian, 'STREAM_ORDER', weight_lu_tab, 'STREAM_ORD', 'Stream_Wght')
                
                if not arcpy.Exists('Stream_Buff500_temp'):    
                    # Select all streams within 1200m of a placer mine
                    arcpy.MakeFeatureLayer_management(in_placer, 'Placer_layer')  # Frequency won't take a FC
                    arcpy.MakeFeatureLayer_management(inRiparian, 'Streams_layer')
                    arcpy.SelectLayerByLocation_management('Streams_layer', "WITHIN_A_DISTANCE", 'Placer_layer',
                                                        "1200 Meters", 'NEW_SELECTION')
                    if int(arcpy.GetCount_management('Streams_layer')[0]) > 0:
                        print ('    Stream segments selected:', arcpy.GetCount_management('Streams_layer'))
                        # buffer all selected streams by 500m - NOTE that this may create overlapping buffers
                        arcpy.Buffer_analysis('Streams_layer', 'Stream_Buff500_temp', "500 Meters",
                                            "FULL", "ROUND", "LIST", "'Stream_Wght'")
                    else:
                        print ('    No Streams Selected near Placer - double check!')
                        sys.exit()
                    
                if not arcpy.Exists('Streams500_flat_placer'):
                    print ('Flattening stream buffers for placer analysis')
                    # Create Unique List of stream weight buffers and sort smallest to largest
                    s_values = [row[0] for row in sorted(arcpy.da.SearchCursor('Stream_Buff500_temp', 'Stream_Wght',
                                                                            "Stream_Wght is not NULL"))]
                    s_weight_list = set(s_values)  # (0.5,0.75,1)
                    print (s_weight_list)
                    
                    # Flatten buffers / remove overlaps.  Highest weight on top.
                    counter = 1            
                    for sWght in s_weight_list:
                        print ('Processing ', str(sWght))
                        temp_in = 'SWtemp_'+str(counter-1)
                        temp_out = 'SWtemp_'+str(counter)
                        if arcpy.Exists(temp_out):
                            arcpy.Delete_management(temp_out)
                        s_w_query = 'Stream_Wght = ' + str(sWght)
                        arcpy.MakeFeatureLayer_management('Stream_Buff500_temp', 'wtempLyr', s_w_query)
                        if int(arcpy.GetCount_management('wtempLyr')[0]) > 0:
                            if not arcpy.Exists(temp_in):
                                arcpy.CopyFeatures_management('wtempLyr', temp_out)
                            else:
                                arcpy.Update_analysis(temp_in, 'wtempLyr', temp_out, "BORDERS")
                                fin_fc = temp_out
                            counter = counter+1
                        arcpy.Delete_management('wtempLyr')                
                    # Rename final buffer update to Streams500_flat_placer
                    arcpy.Rename_management(fin_fc, "Streams500_flat_placer")
                    
                    # Cleanup temp files
                    delete_list = arcpy.ListFeatureClasses('SWtemp*')
                    # print delete_list
                    for delit in delete_list:
                        arcpy.Delete_management(delit)
                
                if not arcpy.Exists('RU_Stream_Placer'):
                    arcpy.Intersect_analysis([in_placer, 'Streams500_flat_placer', inWatershed], 'RU_Stream_Placer',
                                            "NO_FID", "0.1", "INPUT")

                obj_fc = CEA_Module_NB.featureclass_utils()
                geom_tuple = obj_fc.GetGeometryField('RU_Stream_Placer')
                area_field = geom_tuple[0]

                if not arcpy.ListFields('RU_Stream_Placer', 'Placer_Wght_m2'):
                    arcpy.AddField_management('RU_Stream_Placer', 'Placer_Wght_m2', 'Double', '', '2')
                    arcpy.CalculateField_management('RU_Stream_Placer', 'Placer_Wght_m2',
                                                    "!STREAM_WGHT! * !" + area_field + "!", "PYTHON3")

            if not arcpy.Exists(sum_tab_final):
                print ('  Frequency on Buffered Input Layer - stream length \\ order \\ RU')
                arcpy.Frequency_analysis('RU_Stream_Placer', sum_tab_final, [wsLinkFld, wsAreaM2], "'Placer_Wght_m2'")
                if not arcpy.ListFields(sum_tab_final, 'Placer_Score'):
                    arcpy.AddField_management(sum_tab_final, 'Placer_Score', 'Double', '', '2')
                # expression = "([Placer_Wght_m2]/["+wsAreaM2+"])*100"  #percentage score
                # expression = "[Placer_Wght_m2]/["+wsAreaM2+"]"   #weighted score currently in use
                # arcpy.CalculateField_management(sum_tab_final, 'Placer_Score', expression)
                arcpy.CalculateField_management(sum_tab_final, 'Placer_Score', "!Placer_Wght_m2!/!" + wsAreaM2 + "!",
                                                "PYTHON3")
                
            objfcutil = CEA_Module_NB.featureclass_utils()
            # fieldskeep = [wsLinkFld,'Placer_Score']
            # objfcutil.delete_fields(sum_tab_final, fieldskeep)
            # join the stats table
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, sum_tab_final, wsLinkFld, ['Placer_Score'])
                
            # print '  Cleanup...'
            # delete_list = ['RU_Stream_Placer', 'Stream_Buff500_temp']
            # for input_Layer in delete_list:
            #   if arcpy.Exists(input_Layer):
            #      arcpy.Delete_management(input_Layer)
                    
            print( '...DONE Placer Tenures.')
            __PrintTime(deltaTime)   


        def coal_lease(in_watershed, in_coal):
            """
            Coal Leases - % of watershed unit that is in coal lease (salees)
            :param in_watershed:
            :param in_coal: 
            :return: 
            """
            print ('\nStarting Coal Lease analysis...')
            arcpy.env.workspace = fgdbLoc
            if not arcpy.Exists('frq_score_coal'):
                if not arcpy.Exists('coal_resultant'):
                    arcpy.Intersect_analysis([in_coal, in_watershed], 'coal_resultant')
                    
                    # find the area field for resultant
                    obj_coal = CEA_Module_NB.featureclass_utils()
                    geom_tuple = obj_coal.GetGeometryField("coal_resultant")
                    area_field = geom_tuple[0]
                    
                    if not arcpy.ListFields("coal_resultant", 'Coal_Lease_HA'):
                        arcpy.AddField_management("coal_resultant", 'Coal_Lease_HA', 'DOUBLE')

                    arcpy.CalculateField_management('coal_resultant', 'Coal_Lease_HA',
                                                    "!" + area_field + "!/10000", "PYTHON3")
                
                arcpy.Frequency_analysis("coal_resultant", 'frq_score_coal', [wsLinkFld, wsAreaHa], ['Coal_Lease_HA'])
                arcpy.AddField_management("frq_score_coal", 'Coal_Lease_PCNT', 'DOUBLE')
                arcpy.CalculateField_management('frq_score_coal', 'Coal_Lease_PCNT',
                                                "(!Coal_Lease_HA!/!" + wsAreaHa + "!) * 100", "PYTHON3")
                        
            # objfcutil = CEA_Module_NB.featureclass_utils()
            # fieldskeep = [wsLinkFld,'DDR_Length_km','DDR_Score']
            # objfcutil.delete_fields("frq_score_DDR", fieldskeep)
            
            objfcutil = CEA_Module_NB.featureclass_utils()
            objfcutil.join_table("Watershed_STATS_TABLE", wsLinkFld, "frq_score_coal", wsLinkFld, ['Coal_Lease_PCNT'])
            
            print ('...DONE Coal Leases')
            __PrintTime(deltaTime)


        # ---------------------------------------------------------------------------
        #  END FUNCTIONS
        # ---------------------------------------------------------------------------
        # -------------------------------------------------------------------------------

        # ---------------------------------------------------------------------------
        #  LOOP THROUGH ALL WATERSHED LEVELS AND CALCULATE WATERSHED HAZARD
        # ---------------------------------------------------------------------------
        # -------------------------------------------------------------------------------

        for wtrshd in All_wtrshds:
            print(f"\n--- Processing watershed: {wtrshd} ---")
    
            # 1. Reset ArcPy environment at the beginning of each iteration
            arcpy.ResetEnvironments()
            # # arcpy.env.workspace = fgdbLoc
            # arcpy.env.cellSize = 'DEM_GRID'
            # arcpy.env.snapRaster = 'DEM_GRID'
            arcpy.env.overwriteOutput = True

            arcpy.Delete_management("in_memory")

            if 'Named' in wtrshd:
                typ='Named_Watershed'
                
            elif 'Tributaries' in wtrshd:
                typ='Tributaries'
                
            elif 'WAU' in wtrshd:
                typ='WAU'
            # wtrshd=os.path.join()
            arcpy.env.workspace=os.path.join(inputfolder,r'WatershedData_Omineca.gdb')
            print('=========================This is the new one===================== ')
            print(wtrshd)
            print(typ)
            print('=========================This is the new one===================== ')
            data_name =wtrshd
            # masterWS = wtrshd #os.path.join(inputfolder,r'WatershedData_Omineca.gdb', data_name)        #this one  
            # wtrshd=masterWS
            uniqueValues = [wtrshd] #this one
                        # Output excel table for compiled data
            compiledFGDB = "Compiled_Watershed_Hazard_Summaries_rw"
            outXLSname = data_name + compiledFGDB + '_' + datevar+'.xlsx'
            if os.path.exists(os.path.join(reportDir,outXLSname)):
                print('output spreadsheet already exists, moving on to the next assessemt unit')
            else:
                NamedWatershed= WatershedName.replace(' ','_')
                data_name =NamedWatershed+'_'+typ  #'Hominka_River_WAU'  old var +AOItype 
                print(inputfolder)
                masterWS = os.path.join(inputfolder,r'WatershedData_Omineca.gdb', data_name)        #this one 
                print(masterWS)
                # uniqueValues = [data_name] #this one
                # data_name = 'Hominka_River_Named_Watershed'
                input_gdb=os.path.join(inputfolder,(NamedWatershed+'_Input_Data.gdb'))


                # SET UP VARIABLES for LOOP FOR WATERSHED GROUPS/Assessment Units:
                # NOTE:   Custom data prep (VRI2, Roads, DEM) has not yet been completed for the Cariboo watersheds!!

                # Master Watershed dataset with nested units
                # Final Watershed Unit Dataset
                # data_name = 'Hominka_River_WAU'
                # masterWS = os.path.join(r'N:\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\1_WHPOR_Analyses\2023\6_Hominka\1_SpatialData\1_InputData\WatershedData_Omineca.gdb', data_name)
                # uniqueValues = ['Hominka_River_WAU']
                # Set Watershed source field names.
                wsUnitFld = 'Assess_Uni'        # Assessment Unit/Watershed Group
                wsLinkFld = 'RevRepUni'         # Unique reporting ID
                wsNameFld = 'Report_Nam'        # Watershed Name (may not be unique)
                wsTypeFld = 'Report_Typ'        # Type:  Super Watershed, Large Watershed, Watershed, Basin, Sub-basin, residual
                wsAreaHa = 'RU_Area_ha'
                wsAreaKM2 = 'RU_Area_km2'
                wsAreaM2 = 'RU_Area_m2'


                for uni in uniqueValues:
                    


                    # Strip out any blanks in Name to use as compressed name for FGDB
                    wsUnitName = uni
                    extentVal = uni.replace(' ', '')
                    wsQuery = wsUnitFld + ' = ' + "'" + wsUnitName + "'"
                    print ('\nNow processing:  ' + wsUnitName + ", "+extentVal)

                    # set the output name of the file geodatabase from the above variables
                    setOutputFGDB = extentVal + '_' + analysisVal + '_' + datevar
                    setOutputlibraryFGDB = extentVal + '_' + analysisVal + '_Library'
                    libfgdbLoc = os.path.join(sOutputLoc, setOutputlibraryFGDB) + ".gdb"
                    fgdbLoc = os.path.join(sOutputLoc, setOutputFGDB) + ".gdb"
                    srcLoc = os.path.join(fgdbLoc, 'source')
                    
                    # Watershed Datasets  prepared in create_aoi_bnd()
                    wsNested = fgdbLoc + '\\Watersheds_in_AOI'
                    wsBnd = fgdbLoc + '\\Watersheds_bnd'

                    # the data source dictionary within which analysis sources can be found.
                    # data source variables are set within the applicable def
                    # you can either call the variables from the dictionary, or use them directly as named below
                    dataSourceDict = {}

                    arcpy.env.workspace = fgdbLoc

                    # CALL FUNCTIONS - This is part of the Loop for each Watershed Assessment Area

                    create_fgdb()
                    create_aoi_bnd(wsQuery)
                    create_stats_table()   # THIS WILL DELETE IT IF IT ALREADY EXISTS!
                    datasource_dict = data_prep()

                    create_slope()
                    create_h_poly(dataSourceDict['Elevation'])  # TEMP MODIFIED!! Check
                    alpine_nf(dataSourceDict['VRI2'])
                    bec_zone_analysis(wsNested, datasource_dict['BEC'])
                    # eca(dataSourceDict['VRI2'], dataSourceDict['ROW'], dataSourceDict['Private'], dataSourceDict['BEC'])
                    DDR(wsNested, dataSourceDict['Streams'])
                    open_water(dataSourceDict['Hpoly'], dataSourceDict['OpenWater'])
                    slope60(wsNested, dataSourceDict['slope60'])  # overlays slope 60
                    gsc_geology(wsNested, dataSourceDict['GSC'])
                    # creates gentle over steep as well as steepcoupled slopes. Also summarizes steep coupled slopes
                    gos_steep_coupled_slopes(wsNested, 'DEM_GRID', "GridSlope_50", dataSourceDict['Perimeter'],
                                            dataSourceDict['FWAWSHD'])
                    roads_Analysis(wsNested, dataSourceDict['Roads'], dataSourceDict['Riparian'], dataSourceDict['SteepCoupled_poly'],
                                dataSourceDict['MAPS50K'])
                    harvest_gos(wsNested, dataSourceDict['GOS'], dataSourceDict['Harvested'])
                    
                    
                    
                    stream_order_length(wsNested, dataSourceDict['Riparian'], dataSourceDict['PrivIR'],
                                        dataSourceDict['Harvested'], dataSourceDict['Range'])   
                    # privIR and Range changed from None, and lines in function commented out trying empty FCs to see if that will work 
                    #may be able to get rid of the try except below with empyt FCs, All referneces to PYTHON_9.3 changed to PYTHON3, below changed from 
                    #try to if 
                    # if 'Placer' in dataSourceDict:
                    if arcpy.Exists(dataSourceDict['Placer']):
                        if int(arcpy.GetCount_management(dataSourceDict['Placer'])[0]) > 0:
                            placer_ten(wsNested, dataSourceDict['Riparian'], dataSourceDict['Placer'])
                    else:
                        print ('no placer present')
                        arcpy.AddField_management('Watershed_STATS_TABLE', 'Placer_Score', 'Double', '', '2')
                        arcpy.CalculateField_management('Watershed_STATS_TABLE', 'Placer_Score', 0, "PYTHON3")
                        
                    if arcpy.Exists(dataSourceDict['Coal']):
                        if int(arcpy.GetCount_management(dataSourceDict['Coal'])[0]) > 0:
                            coal_lease(wsNested, dataSourceDict['Coal'])
                        else:
                            print ('no coal present')
                            arcpy.AddField_management('Watershed_STATS_TABLE', 'Coal_Lease_PCNT', 'Double', '', '2')
                            arcpy.CalculateField_management('Watershed_STATS_TABLE', 'Coal_Lease_PCNT', 0, "PYTHON3")
                    else:
                        print ('no coal present')
                        arcpy.AddField_management('Watershed_STATS_TABLE', 'Coal_Lease_PCNT', 'Double', '', '2')
                        arcpy.CalculateField_management('Watershed_STATS_TABLE', 'Coal_Lease_PCNT', 0, "PYTHON3")

                    # if' Private' in dataSourceDict:
                        
                    #============================= Add in lines like above for private and range================================

                    arcpy.env.workspace = fgdbLoc
                    
                    # Replace Null values with Zeros in final stats table
                    print ('\nZeroing Null Fields... ')
                    objnull = CEA_Module_NB.table_utils()
                    objnull.zero_null_values('Watershed_STATS_TABLE')
                    
                    print ('\nAdding Run Date to Watershed_STATS_TABLE...')
                    __AddRunDate('Watershed_STATS_TABLE', "RUN_DATE")

                    print ('\n DONE PROCESSING:  ' + wsUnitName + ", " + extentVal)
                    __PrintTime(deltaTime)

                    # ------------------
                    # Makes the compiled filegeodatabase and copies compiled watersheds and stats table across
                    # Will Overwrite Existing data if it already exists!
                    # ------------------
                    print ('Copying analysis Results to a compiled Master File Geodatabase')
                    
                    # compiledFGDB = "Compiled_Watershed_Hazard_Summaries_rw"
                    compiledfgdbLoc = os.path.join(sOutputLoc, compiledFGDB) + ".gdb"
                    
                    print ('Checking to see if compiled filegeodatabase exists')
                    if not arcpy.Exists(compiledfgdbLoc):
                        arcpy.CreateFileGDB_management(sOutputLoc, compiledFGDB)
                    else:
                        print (compiledfgdbLoc + 'already exists not recreating...\n')
                        
                    # uni_nospace = uni.replace(" ", "")  #extentVal
                    print ('Copying across watershed features to compiled file geodatabase. ' + compiledfgdbLoc + "\\" + extentVal + "_" + 'Watersheds_in_AOI')
                    arcpy.CopyFeatures_management('Watersheds_in_AOI', compiledfgdbLoc + "\\" + extentVal + "_" + 'Watersheds_in_AOI')

                    print ('Copying across Stats Table to compiled file geodatabase. ' + compiledfgdbLoc + "\\" + extentVal + "_" + 'Watershed_STATS_TABLE')
                    arcpy.CopyRows_management('Watershed_STATS_TABLE',
                                            compiledfgdbLoc + "\\" + extentVal + "_" + 'Watershed_STATS_TABLE')

                # --------------------
                # Compiles the data together that are in the filegeodatabase
                print ('Merging data together in compiled file geodatabase')
                arcpy.env.workspace = compiledfgdbLoc
                print (arcpy.env.workspace)
                compxls="Compiled_Watershed_Stats_Table_"+typ
                compliledout="Compiled_Watershed_Features_"+typ

                if arcpy.Exists(compliledout):
                    print ('Deleting Compiled_Watershed_Features')
                    arcpy.Delete_management(compliledout)
                    
                if arcpy.Exists(compxls):
                    arcpy.Delete_management(compxls) 

                print ('The compiled filegeodatabase is ' + compiledfgdbLoc)

                # list feature classes in the current file geodatabase
                search_fc='*'+typ+'*'
                featureclassList = arcpy.ListFeatureClasses(search_fc)
                print ('The following feature classes will be merged together ')
                print (featureclassList)
                arcpy.Merge_management(featureclassList, compliledout)

                # List tables
                tableList = arcpy.ListTables(search_fc)
                print ('The following tables will be appended together')
                print (tableList)
                arcpy.Merge_management(tableList, compxls)

                # Join stats table to compiled spatial data
                objCompilejoin = CEA_Module_NB.featureclass_utils()
                objCompilejoin.join_table(compliledout, wsLinkFld, compxls, wsLinkFld)
                del_field_list = ['FREQUENCY', 'Assess_Uni_1', 'RevRepUni_1', 'Report_Nam_1', 'Report_Typ_1', 'RU_Area_ha_1',
                                'RU_Area_km2_1', 'RU_Area_m2_1']
                for field in del_field_list:
                    arcpy.DeleteField_management(compliledout, field)

                # # Output excel table for compiled data
                # outXLSname = data_name + compiledFGDB + '_' + datevar+'.xlsx'

                # objXL = CEA_Module_NB.excel_utils()
                # objXL.exportTable('Compiled_Watershed_Stats_Table', reportDir, outXLSname)
                outxls=os.path.join(reportDir,outXLSname)
                arcpy.conversion.TableToExcel(compxls,outxls)

                #add in os.remove to delete temp files



                # ---------------------------------------------------------------------------
                print ('\nSCRIPT COMPLETE')
                totalTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
                print ('\n This script took ' + totalTime + ' to run.')