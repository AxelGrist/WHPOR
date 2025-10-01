
# Import python libraries

import arcpy
import pandas as pd
from getpass import getpass
from arcgis.features import GeoAccessor, GeoSeriesAccessor
import os
import sys 

# FullyLoaded = r'W:\FOR\RNI\RNI\General_User_Data\CFolkers\Scripts\Python\WHPOR\WHPOR_Fully_Loaded.py'
# if FullyLoaded not in sys.path:
#     sys.path.append(FullyLoaded)

# import WHPOR_Fully_Loaded as WHPOR

class DataPrep:
    def __init__(self, wtrshdname, Bfold, username, password):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold
        self.username=username
        self.password=password

        #user Variables
        WatershedName= self.wtrshdname     #WHPOR.OG_WatershedName
        BaseFolder= self.Bfold        #WHPOR.OG_BaseFolder
        #staic Variables
        NamedWatershed=str(WatershedName.replace(' ','_'))+'.gdb'
        inputdataPath=os.path.join(BaseFolder,r'1_SpatialData\1_InputData') 
        initial_gdb_path = os.path.join(inputdataPath,NamedWatershed)
        print(NamedWatershed)
        print(inputdataPath)
        print(initial_gdb_path)

        #get BCGW credientials 
        bcgw_username =self.username=username #input('Enter BCGW user name: ')
        bcgw_password =self.password=password# getpass(prompt='Enter BCGW password: ')


        arcpy.env.overwriteOutput = True
        #Create GDB
        parent_folder = current_workspace = arcpy.env.workspace=initial_gdb_path
        gdb_flag = True

        while gdb_flag == True: 
            parent_folder = os.path.split(parent_folder)[0]
            if not '.gdb' in parent_folder:
                gdb_flag = False

        #create AOI gdb
        aoi_fgdb_name = r'WatershedData_Omineca.gdb'
        # arcpy.management.CreateFileGDB(parent_folder, aoi_fgdb)
        aoi_fgdb = os.path.join(inputdataPath,aoi_fgdb_name)
        print(aoi_fgdb)
        if arcpy.Exists(aoi_fgdb):
            print('WatershedData_Omineca.gdb already exists')
        else:
            arcpy.management.CreateFileGDB(inputdataPath,aoi_fgdb_name)
            

        #Copy Feature Classes
        datasets = arcpy.ListDatasets(feature_type='feature')
        datasets = [''] + datasets if datasets is not None else []

        featureclass_list = []

        for ds in datasets:
            for fc in arcpy.ListFeatureClasses(feature_dataset=ds):
                if '_Named_Watershed' in fc:
                    named_watershed_file = fc
                    arcpy.conversion.FeatureClassToFeatureClass(in_features=fc, out_path=aoi_fgdb, out_name=fc)
                if '_Tributaries' in fc:
                    arcpy.conversion.FeatureClassToFeatureClass(in_features=fc, out_path=aoi_fgdb, out_name=fc) 


        with arcpy.da.SearchCursor(named_watershed_file, ['FWA_WATERSHED_CODE','GNIS_NAME']) as cursor:
            for row in cursor:
                fwa_watershed_code = row[0]
                gnis_name = row[1]
        print(fwa_watershed_code, gnis_name)

        code_split_list = fwa_watershed_code.split("-")
        code_join_list = []



        for code in code_split_list:
            if int(code) != 0:
                code_join_list.append(code)

        code_string = '-'.join(code_join_list)
        code_sql = "FWA_WATERSHED_CODE LIKE '" + code_string + "%'"
        print(code_sql)



        #Export WAUs
        wau_watershed_file = gnis_name.replace(' ', '_') + '_WAU'
        print(wau_watershed_file)

        arcpy.env.workspace = aoi_fgdb

        """
        Function to connect to the BCGW and return a feature layer for the requested dataset.
        Required variables: 1. username 2. password 3. aoi layer to clip features to
        Parameters: 1. the dataset's object name 2. SQL 3. output layer name 4. Selection by Location AOI, 5. AOI spatial relationships
        """
        def bcgw_Feature_Layer(object_name, sql, out_name, aoi_layer, relationship):
            data_conn_str = arcpy.CreateDatabaseConnectionString_management(database_platform = 'ORACLE',
                                                                            instance = 'bcgw.bcgov/idwprod1.bcgov',
                                                                            account_authentication = 'DATABASE_AUTH',
                                                                            username = bcgw_username,
                                                                            password = bcgw_password,
                                                                            database = "",
                                                                            object_name = object_name)

            bcgw_fl = arcpy.MakeFeatureLayer_management(in_features = data_conn_str,
                                                        out_layer = object_name,
                                                        where_clause = sql)
            
            if aoi_layer is not None:
                bcgw_fl = arcpy.SelectLayerByLocation_management(in_layer = bcgw_fl,
                                                                overlap_type = relationship,
                                                                select_features = aoi_layer)
            
            arcpy.arcpy.FeatureClassToFeatureClass_conversion(in_features = bcgw_fl,
                                                            out_path = arcpy.env.workspace,
                                                            out_name = out_name)
                                                    
            return
        #Call Fucntion from Above
        bcgw_Feature_Layer(object_name = 'WHSE_BASEMAPPING.FWA_ASSESSMENT_WATERSHEDS_POLY',
                        sql = code_sql,
                        out_name = wau_watershed_file,
                        aoi_layer = None,
                        relationship = None)


        #Calculate Fields
        # for each layer in aoi_fgcb calculate standard fields
        input_data = arcpy.ListFeatureClasses()
        print(input_data)


        # Create fields
        fields_table = [['Report_Typ', 'TEXT'], ['Report_Nam', 'TEXT'], ['Report_Uni', 'DOUBLE'], 
                        ['Assess_Uni', 'TEXT'], ['RevRepUni', 'DOUBLE'], ['RU_Area_ha', 'DOUBLE'],
                        ['RU_Area_m2', 'DOUBLE'], ['RU_Area_km2', 'DOUBLE']]

        # Calculate standard fields
        calculate_table = [['Report_Uni', '!ObjectID!'], ['RevRepUni', '!ObjectID! + 10000'], ['RU_Area_ha', '!SHAPE.AREA@HECTARES!'],
                        ['RU_Area_m2', '!SHAPE.AREA@SQUAREMETERS!'], ['RU_Area_km2', '!SHAPE.AREA@SQUAREKILOMETERS!']]

        cursor_field ='Assess_Uni'

        for data in input_data:
            assess_uni_value = arcpy.Describe(data).name
            
            arcpy.management.AddFields(in_table = data, field_description = fields_table)
            
            arcpy.CalculateFields_management(in_table = data,
                                            expression_type = 'PYTHON3',
                                            fields = calculate_table)
            
            with arcpy.da.UpdateCursor(data, cursor_field) as cursor:
                for row in cursor:
                    row[0] = assess_uni_value
                    cursor.updateRow(row)



        def name_type_field_calc(data, cursor_fields):
            
            none_flag = False
            if cursor_fields[1] is None:
                none_flag = True
                cursor_fields = cursor_fields[0]
            
            with arcpy.da.UpdateCursor(data, cursor_fields) as cursor:
                for row in cursor:
                    if not none_flag:
                        field_value = row[1]
                        if len(cursor_fields) == 3:
                            field_value = field_value + ' ' + str(int(row[2]))

                        row[0] = field_value
                        cursor.updateRow(row)
                    else:
                        row[0] = 0 
                        cursor.updateRow(row)

        for data in input_data:
            if '_Named_Watershed' in data:
                report_nam_field = ['GNIS_NAME']
                report_typ_field = ['Stream_Order']
            elif '_Tributaries' in data:
                report_nam_field = ['Assess_Uni', 'Report_Uni']
                report_typ_field = [None]  
            else:
                report_nam_field = ['Assess_Uni', 'Report_Uni']
                report_typ_field = ['Watershed_Order']
            
            cursor_fields = ['Report_Nam'] + report_nam_field
            print(data, cursor_fields)
            name_type_field_calc(data, cursor_fields)
            
            cursor_fields = ['Report_Typ'] + report_typ_field
            print(data, cursor_fields)
            name_type_field_calc(data, cursor_fields)

            print('Done')