# Import python libraries
import arcpy
import shutil
from getpass import getpass
import os
import sys

class VRI2_Prep:
    def __init__(self, wtrshdname, Bfold, username, password): #, xlsly removed?
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold
        self.username=username
        self.password=password
        # self.xlsly=xlsly
    

        #user Variables
        WatershedName=self.wtrshdname
        BaseFolder=self.Bfold

        #Static Variables 
        Watershed_Name=WatershedName.replace(' ','_')
        output_folder= os.path.join(BaseFolder,r'1_SpatialData\1_InputData')
                            #ex r'N:\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\1_WHPOR_Analyses\2023\5_Walker\1_SpatialData'
        Wgdb=os.path.join(output_folder,'WatershedData_Omineca.gdb')
        bcgw_username = self.username
        bcgw_password = self.password
        aoi_fgdb = r'Python_Geodatabase.gdb'
 

        arcpy.env.workspace =output_folder

        #Create AOI Data 
        # in home directory create '3_VRI_Update' subdirectory
        parent_folder = arcpy.env.workspace
        gdb_flag = True

        while gdb_flag == True: 
            parent_folder = os.path.split(parent_folder)[0]
            if not '.gdb' in parent_folder:
                gdb_flag = False

        vri2_dir = '3_VRI_Update'
        path = os.path.join(parent_folder, vri2_dir)
        if os.path.exists(path):
            print(' Directory Exists')
        else:   
            os.makedirs(path)


        # make gdb Python_Geodatabase.gdb
        gdbpath=os.path.join(path,aoi_fgdb)
        if os.path.exists(gdbpath):
            print('gdb already exists')
            python_gdb=gdbpath
        else:
            python_gdb = arcpy.management.CreateFileGDB(path, aoi_fgdb)
            print('no gdb path')
            print(path)
            print(aoi_fgdb)
            python_gdb=os.path.join(path, aoi_fgdb)



        # copy named watershed as AOI
        # arcpy.env.workspace = parent_folder
        # workspace = arcpy.ListWorkspaces('WatershedData_Omineca.gdb')[0]
        arcpy.env.workspace = Wgdb
        # print(workspace)
        fc = arcpy.ListFeatureClasses('*Named_Watershed')[0]
        print(fc)
        arcpy.env.workspace = python_gdb
        fc=Wgdb+'/'+fc
        aoi_fc = fc #arcpy.conversion.FeatureClassToFeatureClass(in_features=fc, out_path=python_gdb, out_name='AOI')
        
        # try:
        #     aoi_fc=arcpy.management.Dissolve(in_features=fc,out_feature_class=fr"{python_gdb}/AOI")
        #     # arcpy.management.CalculateField(in_table=fr"{python_gdb}/AOI",field='WATERSHED_KEY',expression=10001,expression_type="PYTHON3",)
        # except:
        aoi_fc = arcpy.conversion.FeatureClassToFeatureClass(in_features=fc, out_path=python_gdb, out_name='AOI')
        print('Copy AOI')

        # created field 'AOI_Tile' and calculate as Assess_Uni
        assess_uni=arcpy.ListFields(aoi_fc, 'Assess_Uni*')[0]
        arcpy.management.AddField(in_table=aoi_fc, field_name='AOI_Tile', field_type='TEXT')
        with arcpy.da.UpdateCursor(aoi_fc, ['Assess_Uni', 'AOI_Tile']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        print('AOI Tile')


        #Export BCGW Data
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


        #Call Function 
        bcgw_Feature_Layer(object_name = 'WHSE_FOREST_TENURE.FTEN_CUT_BLOCK_POLY_SVW',
                        sql = None,
                        out_name = 'FTEN_CUT_BLOCK_POLY_SVW',
                        aoi_layer = aoi_fc,
                        relationship = 'INTERSECT')
        print('WHSE_FOREST_TENURE.FTEN_CUT_BLOCK_POLY_SVW')

        bcgw_Feature_Layer(object_name = 'WHSE_FOREST_VEGETATION.RSLT_FOREST_COVER_INV_SVW',
                        sql = None,
                        out_name = 'RSLT_FOREST_COVER_INV_SVW',
                        aoi_layer = aoi_fc,
                        relationship = 'INTERSECT')
        print('WHSE_FOREST_VEGETATION.RSLT_FOREST_COVER_INV_SVW')

        bcgw_Feature_Layer(object_name = 'WHSE_FOREST_VEGETATION.RSLT_OPENING_SVW',
                        sql = None,
                        out_name = 'RSLT_OPENING_SVW',
                        aoi_layer = aoi_fc,
                        relationship = 'INTERSECT')
        print('WHSE_FOREST_VEGETATION.RSLT_OPENING_SVW')

        bcgw_Feature_Layer(object_name = 'WHSE_FOREST_VEGETATION.VEG_COMP_LYR_R1_POLY',
                        sql = None,
                        out_name = 'VEG_R1_PLY',
                        aoi_layer = aoi_fc,
                        relationship = 'INTERSECT')
        print('WHSE_FOREST_VEGETATION.VEG_COMP_LYR_R1_POLY')
        #Create Function 
        """
        Function to connect to the BCGW and return a table layer for the requested dataset.
        """
        def bcgw_Table_Layer(object_name, out_name):
            data_conn_str = arcpy.CreateDatabaseConnectionString_management(database_platform = 'ORACLE',
                                                                            instance = 'bcgw.bcgov/idwprod1.bcgov',
                                                                            account_authentication = 'DATABASE_AUTH',
                                                                            username = bcgw_username,
                                                                            password = bcgw_password,
                                                                            database = "",
                                                                            object_name = object_name)
            
            bcgw_tv = arcpy.MakeTableView_management(in_table = data_conn_str,
                                                    out_view = object_name)
            
            arcpy.CopyRows_management(in_rows = bcgw_tv,
                                    out_table = out_name)
            
            return


        #Call Function 
        bcgw_Table_Layer(object_name = 'WHSE_FOREST_VEGETATION.RSLT_OPENING_VW',
                        out_name = 'RSLT_OPENING_VW')
        print ('WHSE_FOREST_VEGETATION.RSLT_OPENING_VW')

        #Delete in a few runs 20230707

        # #Copy Py files and create data folder
        data_path = os.path.join(path, 'data')
        os.makedirs(data_path)

        print('Done')