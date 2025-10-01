import os
import shutil
import arcpy
import sys
import pandas as pd
import openpyxl

class wtrshd_prep:
    def __init__(self, wtrshdname, Bfold):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold

        #user Variables
        WatershedName=self.wtrshdname
        BaseFolder=self.Bfold

        #static variables
        NamedWatershed=WatershedName.replace(' ','_')
        inputgdb=NamedWatershed+'_Input_Data.gdb'
        Input_Spatial=os.path.join(BaseFolder,'1_SpatialData')
        input_gdb=os.path.join(Input_Spatial,'1_InputData',inputgdb)
        xlxs_template=r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\Watershed_Inputs_List_V2.csv'
        openpyxl_template=r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\openpyxl'
        prj=r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\PCS_Albers.prj'
        new_dir='4_CEA_Watershed_Analysis'
        xlxs_copy=Input_Spatial+'/'+new_dir+'/Watershed_Inputs_List_V1.2.csv'


        # fucntions to copy xlxs for layer input and verify if layers exist
        #needs to create stage folder within 04 folderinput_gdb
        def copy_prep(wrk):
            new_path=os.path.join(wrk,new_dir)
            # new_path=wrk+'/'+new_dir
            if os.path.exists(new_path):
                print('Directory already exists')
            else:
                print('Directory does not exist!!!')
                os.mkdir(new_path)
        
            xlxs_copy=new_path+r'\Watershed_Inputs_List_V1.2.csv'
            openpyxl_copy=new_path+r'\openpyxl'
            prj_copy=new_path+r'\PCS_Albers.prj'
            shutil.copy(xlxs_template,xlxs_copy)
            print('xlxs Template copied')
            shutil.copy(prj,prj_copy)
            print('Prj copied')
            shutil.copytree(openpyxl_template,openpyxl_copy)
            print('Openpyxl folder copied')
            

        #it is important to have a fresh xlxs spreadsheet or else this won't work 
        def verify_layers(wrkscp):
            arcpy.env.overwriteOutput = True
            arcpy.env.workspace= wrkscp
            fcs=arcpy.ListFeatureClasses('*')
            # can probably get rid of the two lists below and pull from the above list
            vri2=arcpy.ListFeatureClasses('VRI2_resultant*')
            vri2_r=vri2[0]
            vri2=arcpy.ListFeatureClasses('VRI2_Harvested*')
            vri2_h=vri2[0]

            print(fcs)
            df=pd.read_csv(xlxs_copy)
            print(df)

            for index, row in df.iterrows():
                print(row[0],row[1])
                print(index)
                if row[0]=='VRI2':
                    vri2_r
                    if arcpy.Exists(vri2_r):
                        print('VRI2 exists')
                        desc=arcpy.Describe(vri2_r)
                        desc_Path=desc.path+'/'+vri2_r 
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No VRI2')
                    
                elif row[0]=='Harvested':
                    vri2_h
                    if arcpy.Exists(vri2_h):
                        print('VRI2 exists')
                        desc=arcpy.Describe(vri2_h)
                        desc_Path=desc.path+'/'+vri2_h
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Harvest')
                
                elif row[0] == 'Roads':
                    if 'integrated_roads_2021' in fcs:
                        desc=arcpy.Describe('integrated_roads_2021')
                        desc_Path=desc.path+'/integrated_roads_2021'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Roads')

                elif row[0] == 'Streams':
                    if 'DDR' in fcs:
                        desc=arcpy.Describe('DDR')
                        desc_Path=desc.path+'/DDR'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Streams')
                
                elif row[0] == 'Riparian':
                    if 'RIPARIAN' in fcs:
                        desc=arcpy.Describe('RIPARIAN')
                        desc_Path=desc.path+'/RIPARIAN'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Riparian')
                
                elif row[0] == 'Perimeter':
                    if 'GOS' in fcs:
                        desc=arcpy.Describe('GOS')
                        desc_Path=desc.path+'/GOS'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No FWA Perimeters')

                elif row[0] == 'OpenWater':
                    if index==8:
                        if 'FWLKSPL' in fcs:
                            desc=arcpy.Describe('FWLKSPL')
                            desc_Path=desc.path+'/FWLKSPL'
                            print(desc_Path)
                            df.at[index,'loc']=str(desc_Path)
                            # df.at[index,'var']=str(row[0]+'_1')
                        else:
                            df.drop(index, inplace=True)
                            print('No Lakes')        

                    elif index==9:
                        if 'FWWTLNDSPL' in fcs:
                            desc=arcpy.Describe('FWWTLNDSPL')
                            desc_Path=desc.path+'/FWWTLNDSPL'
                            print(desc_Path)
                            df.at[index,'loc']=str(desc_Path)
                            # df.at[index,'var']=str(row[0]+'_2')
                        else:
                            df.drop(index, inplace=True)
                            print('No Wetlands')
                
                    elif index==10:
                        if 'FWMNMDWTRB' in fcs:
                            desc=arcpy.Describe('FWMNMDWTRB')
                            desc_Path=desc.path+'/FWMNMDWTRB'
                            print(desc_Path)
                            df.at[index,'loc']=str(desc_Path)
                            # df.at[index,'var']=str(row[0]+'_3')
                        else:
                            df.drop(index, inplace=True)
                            print('No Manmade Waterbodies')
                
                elif row[0] == 'GSC':
                    if 'QTRNRY_PLY' in fcs:
                        desc=arcpy.Describe('QTRNRY_PLY')
                        desc_Path=desc.path+'/QTRNRY_PLY'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No GSC')
                
                elif row[0] == 'BEC':
                    if 'BEC' in fcs:
                        desc=arcpy.Describe('BEC')
                        desc_Path=desc.path+'/BEC'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No BEC')

                elif row[0] == 'Private':
                    if 'PMBC_PF_O' in fcs:
                        desc=arcpy.Describe('PMBC_PF_O')
                        desc_Path=desc.path+'/PMBC_PF_O'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Private')
                
                elif row[0] == 'Range':
                    if 'FTN_RNG_PY' in fcs:
                        desc=arcpy.Describe('FTN_RNG_PY')
                        desc_Path=desc.path+'/FTN_RNG_PY'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Range')
                
                elif row[0] == 'Placer':
                    if 'MTA_Placer' in fcs:
                        desc=arcpy.Describe('MTA_Placer')
                        desc_Path=desc.path+'/MTA_Placer'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Placer')

                elif row[0] == 'Coal':
                    if 'MTA_Coal' in fcs:
                        desc=arcpy.Describe('MTA_Coal')
                        desc_Path=desc.path+'/MTA_Coal'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Coal')

                elif row[0] == 'IR':
                    if 'IR_CLAB' in fcs:
                        desc=arcpy.Describe('IR_CLAB')
                        desc_Path=desc.path+'/IR_CLAB'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No IR')

                elif row[0] == 'Burn_Hist':
                    if 'H_FIRE_PLY' in fcs:
                        desc=arcpy.Describe('H_FIRE_PLY')
                        desc_Path=desc.path+'/H_FIRE_PLY'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Burn_Hist')
                
                elif row[0] == 'Burn_Curr':
                    if 'C_FIRE_PLY' in fcs:
                        desc=arcpy.Describe('C_FIRE_PLY')
                        desc_Path=desc.path+'/C_FIRE_PLY'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Burn_Curr')
                
                elif row[0] == 'Roads_Row':
                    if 'BCCEF_Integrated_Roads_2021_Buffers' in fcs:
                        desc=arcpy.Describe('BCCEF_Integrated_Roads_2021_Buffers')
                        desc_Path=desc.path+'/BCCEF_Integrated_Roads_2021_Buffers'
                        print(desc_Path)
                        df.at[index,'loc']=str(desc_Path)
                    else:
                        df.drop(index, inplace=True)
                        print('No Roads_Row')
            df.to_csv(xlxs_copy, index=False, header=False)
            

            

        #call functions

        copy_prep(Input_Spatial)
        verify_layers(input_gdb)