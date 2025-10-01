'''
Script to preform the simple prep for the WHPOR and ECA calculations
python 3.x
Created by CFOLKERS 20230301
'''

import arcpy
import getpass
import pandas 
import os
import sys
from getpass import getpass

class SimplePrep:
    def __init__(self, wtrshdname, Bfold, username, password, xlsly):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold
        self.username=username
        self.password=password
        self.xlsly=xlsly

        #user Variables
        WatershedName=self.wtrshdname
        BaseFolder=self.Bfold

        #static variables
        Watershed_Name=WatershedName.replace(' ','_')
        print(Watershed_Name)
        output_folder= os.path.join(BaseFolder,r'1_SpatialData\1_InputData')
        print(output_folder)
        Named_Watershed=str(Watershed_Name+'_Named_Watershed')
        print(Named_Watershed) 
        AOIpoly= os.path.join(output_folder,'WatershedData_Omineca.gdb',Named_Watershed)
        print(AOIpoly)
        gdbname= Watershed_Name +'_Input_Data.gdb'
        print(gdbname)


        # inputxlslayer=self.xlsly
        inputxlslayer=r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\Layer_Master.xlsx'
        # rating_class=r'N:\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\2_WHPOR_Model\1_Data\5_BEC\Omineca_BEC_v12_Rating_Classification.xlsx\Data$'
        rating_class=r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\Omineca_BEC_v12_Rating_Classification.csv'
        bccef_buf=r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\BCCEF_Buffer_Distance_Table.csv'
        gdbPath= output_folder+ '\\' +gdbname
        sdeloc=output_folder+r'\bcgw.bcgov.sde'

        #validate
        if not arcpy.Exists(AOIpoly):
            print('The AOI layer does not exist')

        #Function to create database connection and create gdb if needed and set paths
        def bd_gbd (outputfolder):
            bcgw_username = self.username
            bcgw_password = self.password
            try:
                arcpy.CreateDatabaseConnection_management(out_folder_path=outputfolder, out_name='bcgw.bcgov.sde',database_platform='ORACLE', instance='bcgw.bcgov/idwprod1.bcgov',
                account_authentication='DATABASE_AUTH', username=bcgw_username, password=bcgw_password, save_user_pass='DO_NOT_SAVE_USERNAME')
                print(' new SDE connection')
            except:
                print('Database connection already exists')
            if os.path.exists(gdbPath):
                print('GDB exists')
            else:
                print('no gdb, creating....')
                arcpy.management.CreateFileGDB(outputfolder, gdbname)
                print('gdb created')
            arcpy.env.workspace=str(gdbPath)
            print('set path')



        #function to read data spreadsheet and process layers based on AOI 
        def doit(AOI):

            df=pandas.read_excel(io= inputxlslayer, header=0 )
            i = 0
            for index, row in df.iterrows():
                i += 1
                print(i)
                tempname=(str(row[3])+'TEMPCLIP')
                if row[1]=='BCGW':
                    layerpath=sdeloc+'\\'+str(row[0])
                    print(row[3])
                elif row[1]=='Local':
                    layerpath=output_folder+gdbname+'\\'+str(row[0])
                    print(row[3])
                else:
                    layerpath=os.path.join(str(row[1]), str(row[0]))
                    print(row[3])
                    if not arcpy.Exists(layerpath):
                        print('The input layer does not exist')

                # Processing 
                if row[4]=='clip':
                    selection=arcpy.management.SelectLayerByLocation(layerpath, 'INTERSECT', AOI)
                    matchcount=int(arcpy.management.GetCount(selection)[0])
                    if matchcount== 0:
                        arcpy.management.CreateFeatureclass(gdbPath, str(row[3]), 'POLYGON')
                        print('no features in selection')
                    else:
                        print(str(matchcount),' Features in selection')
                        arcpy.analysis.Clip(selection, AOI, str(row[3]))
                    print(row[3])
        
                elif row[4]=='selectlocationattributes':
                    selection=arcpy.management.SelectLayerByLocation(layerpath, 'INTERSECT', AOI)
                    matchcount=int(arcpy.management.GetCount(selection)[0])

                    if matchcount== 0:
                        arcpy.management.CreateFeatureclass(gdbPath, str(row[3]), 'POLYGON')
                        print('no features in selection')
                    else:
                        arcpy.analysis.Clip(layerpath, AOI, tempname)
                        print(str(matchcount),' Features in selectlocationattributes selection')
                        print('Clipping Subset, with Where Clause')
                        arcpy.conversion.FeatureClassToFeatureClass(in_features=tempname, out_path=gdbPath, out_name=row[3], where_clause= row[2])
                        print('Done Clip')
                        arcpy.management.Delete(tempname)

                elif row[4]=='featuretoline':
                    #potential discrepency between documentions, newest says  no riparian and no dissolve, older includes rip and dissolve?
                    fl=[]
                    datasets= arcpy.ListFeatureClasses()
                    for f in datasets:
                        print(f)
                        if f == 'FWWTLNDSPL':
                            fl.append(f)
                        elif f == 'RIPARIAN':
                            fl.append(f)
                        elif f == 'FWLKSPL':
                            fl.append(f)
                        elif f == 'FWMNMDWTRB':
                            fl.append(f)
                    # print(fl)
                    # print(type(fl))
                    arcpy.management.FeatureToLine(in_features= fl, out_feature_class= row[3], cluster_tolerance=0.001,attributes='NO_ATTRIBUTES')
                    # arcpy.management.Dissolve(in_features= 'FeatureToLineTemp',out_feature_class= str(row[3]), multi_part= 'SINGLE_PART')
                    # arcpy.management.Delete('FeatureToLineTemp')

                elif row[4]=='clipdissolve':
                    selection=arcpy.management.SelectLayerByLocation(layerpath, 'INTERSECT', AOI)
                    if len(row[2])!=0:
                            arcpy.conversion.FeatureClassToFeatureClass(in_features=selection, out_path=gdbPath, out_name=tempname, where_clause= row[2])
                    else:
                        print('No SQL')       
                    matchcount=int(arcpy.management.GetCount(tempname)[0])
                    if matchcount== 0:
                        arcpy.management.CreateFeatureclass(gdbPath, str(row[3]), 'POLYGON')
                        print('no features in selection')
                        arcpy.management.Delete(selection)
                        arcpy.management.Delete(tempname)
                    else:
                        print(str(matchcount),' Features in selection')
                        temp2=tempname+"_2"
                        arcpy.analysis.Clip(tempname, AOI, temp2 )
                        # if row[5] == 'None':
                        #     print(row[5])
                        #     arcpy.management.Dissolve(in_features=temp2, out_feature_class= row[3],multi_part= 'MULTI_PART')
                        #     arcpy.management.Delete(tempname)
                        #     arcpy.management.Delete(temp2)
                        #     # try:
                            
                        #     # except:
                        #         # arcpy.management.Dissolve(tempname, row[3],'SINGLE_PART')
                        # else:
                        #     print(row[5])
                        #     arcpy.management.Dissolve(in_features=temp2, out_feature_class= row[3],dissolve_field=row[5],multi_part= 'MULTI_PART')
                        #     arcpy.management.Delete(tempname)
                        #     arcpy.management.Delete(temp2)
                        try:
                            print(row[5])
                            arcpy.management.Dissolve(in_features=temp2, out_feature_class= row[3],dissolve_field=row[5],multi_part= 'MULTI_PART')
                            arcpy.management.Delete(tempname)
                            arcpy.management.Delete(temp2)
                           
                        except:
                            arcpy.management.Dissolve(in_features=temp2, out_feature_class= row[3],multi_part= 'MULTI_PART')
                            arcpy.management.Delete(tempname)
                            arcpy.management.Delete(temp2)

                elif row[4]=='clipandjoin':
                    selection=arcpy.management.SelectLayerByLocation(layerpath, 'INTERSECT', AOI)
                    matchcount=int(arcpy.management.GetCount(selection)[0])

                    if matchcount== 0:
                        arcpy.management.CreateFeatureclass(gdbPath, str(row[3]), 'POLYGON')
                        print('no features in selection')
                    else:
                        print(str(matchcount),' Features in selection')
                        arcpy.analysis.Clip(selection, AOI, tempname)
                        val_res = arcpy.management.ValidateJoin(tempname, 'BGC_LABEL',rating_class,'BGC_LABEL')
                        joined = arcpy.AddJoin_management(tempname, 'BGC_LABEL',rating_class,'BGC_LABEL')
                        arcpy.CopyFeatures_management(joined,row[3])
                        print('Table Joined')
                        #add field for listfields for next twi fields
                        ratingf=(arcpy.ListFields(row[3], '*2022_Rating*')[0]).name
                        ratingf='!'+ratingf+'!'
                        classf=(arcpy.ListFields(row[3], '*2022_Class*')[0]).name
                        classf='!'+classf+'!'
                        print(ratingf)
                        print(classf)
                       

                        arcpy.management.CalculateField(in_table= row[3], field='BEC_Weighting', expression=ratingf, expression_type='PYTHON3',field_type='DOUBLE')
                        print('calculate BEC_Weighting')
                        arcpy.management.CalculateField(in_table= row[3], field= 'BEC_MOIST_CLS', expression= classf, expression_type= 'PYTHON3', field_type= 'TEXT')
                        print('calculate BEC_MOIST_CLS')
                        arcpy.management.Delete(tempname)
                        print('BEC complete with join')

                elif row[4]=='roadbuffer':
                    selection=arcpy.management.SelectLayerByLocation(layerpath, 'INTERSECT', AOI)
                    matchcount=int(arcpy.management.GetCount(selection)[0])

                    expression= 'road_type(!BCGW_SOURCE!, !DRA_ROAD_CLASS!, !DRA_ROAD_SURFACE!, !DRA_NUMBER_OF_LANES!, !FTEN_LIFE_CYCLE_STATUS_CODE!, !FTEN_FILE_TYPE_DESCRIPTION!)'

                    codeblock = """def road_type(in_source, rd_class, rd_surf, rd_lane, ften_status, ften_desc):
                        if in_source == 'WHSE_BASEMAPPING.TRANSPORT_LINE':
                            road_type_string = rd_class + ' - ' + rd_surf + '  ' + str(rd_lane)
                        elif in_source == 'WHSE_FOREST_TENURE.FTEN_ROAD_SECTION_LINES_SVW':
                            road_type_string = ften_status.title() + ', ' + ften_desc
                        elif in_source == 'WHSE_FOREST_VEGETATION.RSLT_FOREST_COVER_INV_SVW':
                            road_type_string = 'RSLT_FOREST_COVER_INV_SVW'
                        elif in_source == 'WHSE_FOREST_TENURE.ABR_ROAD_SECTION_LINE':
                            road_type_string = 'WHSE_FOREST_TENURE.ABR_ROAD_SECTION_LINE'
                        else:
                            road_type_string = 'No Type Match'
                        return road_type_string
                    """

                    if matchcount== 0:
                        arcpy.management.CreateFeatureclass(gdbPath, str(row[3]), 'POLYGON')
                        print('no features in selection')
                    else:
                        print(str(matchcount),' Features in selection')
                        arcpy.analysis.Clip(selection, AOI, tempname)
                        arcpy.management.AddField(tempname, 'Road_Type', "TEXT")
                        arcpy.management.CalculateField(tempname, 'Road_Type', expression, 'PYTHON3', codeblock)
                        val_res = arcpy.management.ValidateJoin(tempname, 'Road_Type',bccef_buf,'Road_Type')
                        joined = arcpy.AddJoin_management(tempname, 'Road_Type',bccef_buf,'Road_Type')
                        print('Table joined')
                        arcpy.CopyFeatures_management(joined,row[3])
                        arcpy.management.CalculateField(in_table= row[3], field= 'Road_Buffer_M',expression='!BCCEF_Buffer_Distance_Table_csv_Buffer_M!',expression_type='PYTHON3',field_type='DOUBLE')
                        arcpy.analysis.Buffer(in_features= row[3],out_feature_class= (str(row[3])+'_Buffers'),buffer_distance_or_field= 'Road_Buffer_M') #does it need to be dissoled as well?
                        print('Features Buffer and Dissolve')
                        arcpy.management.Delete(tempname)
                        print()
            print('Done')

        def xings(out_folder):
            gdbPath= out_folder+ '\\' +gdbname
            arcpy.env.workspace=gdbPath
            arcpy.env.overwriteOutput = True
            intersect_List=[]
            stream=arcpy.ListFeatureClasses('DDR')
            # print(stream[0])
            intersect_List.append(stream[0])
            roads=arcpy.ListFeatureClasses('BCCEF_Integrated_Roads_2021')
            # print(roads[0])
            intersect_List.append(roads[0])
            print(intersect_List)
            arcpy.analysis.Intersect(in_features=intersect_List, out_feature_class='XINGS',join_attributes='ALL',output_type='POINT')
            print('xings!!!!')
        3
        #call functions 
        bd_gbd (output_folder)
        doit(AOIpoly)
        xings(output_folder)
