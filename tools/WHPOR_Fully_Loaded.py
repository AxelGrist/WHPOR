'''

Date: 2023 07 21
script created by: Cfolkers

the purpose of this script is to create the WHPOR Project and run all assoicated scripts, currently there are 9 scripts and two modules. 
all scripts need to be in the same folder  

'''



import os
import arcpy
import datetime
# import sqlalchemy
from getpass import getpass
import time



#import scripts
import WHPOR_01_Tributary_Watersheds as w1
import WHPOR_03_DataPrep as w3
import WHPOR_04_SimplePrep as w4
import WHPOR_05_VRI2_Prep as w5
import WHPOR_06_VRI2 as w6
import WHPOR_07_ECA as w7
import WHPOR_08_Watershed_Analysis_Prep as w8
import WHPOR_09_CEA_watershed_analysis as w9
import WHPOR_10_Resultant_Outputs as w10




#User Variable - The only thing that needs to be changed
OG_WatershedName='Fraser River'
OG_watershed_key=356364114
OG_custom_aoi_path=r'H:\WHPOR_Test_Polygon\Polygon.shp'  # Example: r'T:\WHPOR_Temp\Custom_AOI\my_aoi.gdb\AOI'
OG_AOIName='WHPOR Test Polygon'  # Custom AOI label used for title/file names only when OG_custom_aoi_path is set



#Static Variables- Don't Touch unless you absolutely have to, like to change the APRX template, wokring directory or input xlsx's
year=str(datetime.datetime.today().year)
# workDir=os.path.join(r'N:\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\1_WHPOR_Analyses',year)
workDir=r'T:\WHPOR_Temp'
CustomAOIUsed=OG_custom_aoi_path not in [None, '']
if CustomAOIUsed and OG_AOIName not in [None, '']:
    OG_RunName=OG_AOIName
else:
    OG_RunName=OG_WatershedName

runname=OG_RunName.replace(' ','_')
print(runname)
aprxtemp=r'\\spatialfiles.bcgov\work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\WHPOR_APRX_Template_20230713\WHPOR_APRX_Template_20230713.aprx'
#eventually this will get changed to the N drive
OG_inputxlslayer=r'T:\WHPOR\Layer_Master.xlsx'
OG_bcgw_username =input('Enter BCGW user name: ')
OG_bcgw_password =getpass(prompt='Enter BCGW password: ')
proj=runname # added for testing with temp drive
OG_BaseFolder=os.path.join(workDir,proj)
check_dir=os.path.join(workDir,runname) #str(dircheck)+'_'+ removed from before watershed name for testing with temp drive
sd=os.path.join(OG_BaseFolder,r'1_SpatialData')
inp=os.path.join(sd,r'1_InputData')
aprxname=os.path.join(inp,(runname+r'.aprx'))
gdbname=(runname+r'.gdb')
gdbPath=os.path.join(inp,gdbname)

''' 
Below lines are commented out for testing purposese, one var above DirNum has a +1 commented out, this is not working correctly and will create to many files if re -run 
another way to achieve the 
'''
OG_BaseFolder=check_dir
sd=os.path.join(OG_BaseFolder,r'1_SpatialData')
inp=os.path.join(sd,r'1_InputData')
aprxname=os.path.join(inp,(runname+r'.aprx'))
gdbname=(runname+r'.gdb')
gdbPath=os.path.join(inp,gdbname)

# Check and create each directory separately
if not os.path.exists(workDir):
    os.mkdir(workDir)
if not os.path.exists(OG_BaseFolder):
    os.mkdir(OG_BaseFolder)
if not os.path.exists(sd):
    os.mkdir(sd)
if not os.path.exists(os.path.join(OG_BaseFolder, r'2_Reports')):
    os.mkdir(os.path.join(OG_BaseFolder, r'2_Reports'))
if not os.path.exists(os.path.join(OG_BaseFolder, r'3_Maps')):
    os.mkdir(os.path.join(OG_BaseFolder, r'3_Maps'))
if not os.path.exists(os.path.join(OG_BaseFolder, r'4_Communications')):
    os.mkdir(os.path.join(OG_BaseFolder, r'4_Communications'))
if not os.path.exists(inp):
    os.mkdir(inp)
if not os.path.exists(os.path.join(sd, r'2_IntermediateData')):
    os.mkdir(os.path.join(sd, r'2_IntermediateData'))
if not os.path.exists(os.path.join(sd, r'3_ResultantData')):
    os.mkdir(os.path.join(sd, r'3_ResultantData'))
print('directory tree created')

# if os.path.exists(check_dir):
#     print('watershed name exists in root folder Check name')
#     OG_BaseFolder=check_dir
    # sd=os.path.join(OG_BaseFolder,r'1_SpatialData')
    # inp=os.path.join(sd,r'1_InputData')
    # aprxname=os.path.join(inp,(watershedname+r'.aprx'))
    # gdbname=(watershedname+r'.gdb')
    # gdbPath=os.path.join(inp,gdbname)
    
# else:
#     os.mkdir(workDir) # added for using temp drive
#     os.mkdir(OG_BaseFolder)
#     os.mkdir(sd)
#     os.mkdir(os.path.join(OG_BaseFolder,r'2_Reports'))
#     os.mkdir(os.path.join(OG_BaseFolder,r'3_Maps'))
#     os.mkdir(os.path.join(OG_BaseFolder,r'4_Communications'))
#     os.mkdir(inp)
#     os.mkdir(os.path.join(sd,r'2_IntermediateData'))
#     os.mkdir(os.path.join(sd,r'3_ResultantData'))
#     print('directory tree created')

#save copy of template in input data and create gdb of watershed name 

if os.path.exists(aprxname):
    print(runname+' APRX exists')
else:
    aprx=arcpy.mp.ArcGISProject(aprxtemp)
    aprx.saveACopy(aprxname)
    print('copying APRX template and renaming')

aprx=arcpy.mp.ArcGISProject(aprxname)
#create named gdb and set as defualt for proj 
if os.path.exists(gdbPath):
        print('GDB exists')
else:
    print('no gdb, creating....')
    arcpy.management.CreateFileGDB(inp, gdbname)
    print(gdbname)
aprx = arcpy.mp.ArcGISProject(aprxname)
print(aprx)
print(aprxname)

foldic=[{'connectionString':inp,'alias':'1_InputData','isHomeFolder':True},{'connectionString':OG_BaseFolder,'alias':proj,'isHomeFolder':False}]

aprx.updateFolderConnections(foldic,True)
#set defualt home folder to spatial data folder 
aprx.homeFolder=sd
aprx.save
print('aprx saved')

print('====================LET IT RIPPPPPPPPPPPPPPPPPPPPPPPPPP!!!!====================')
print(OG_BaseFolder)
print(OG_watershed_key)
print(OG_WatershedName)
print('Run Name:', OG_RunName)
print('Custom AOI Used:', CustomAOIUsed)


startTime = time.time()
START_TIME = time.ctime(time.time())

w1.Tribs(OG_RunName,OG_watershed_key,OG_BaseFolder,OG_bcgw_username,OG_bcgw_password,OG_custom_aoi_path)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 1 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s1time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
w3.DataPrep(OG_RunName,OG_BaseFolder,OG_bcgw_username,OG_bcgw_password,OG_custom_aoi_path)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 3 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s3time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 3 complted in: ' + s3time)
w4.SimplePrep(OG_RunName,OG_BaseFolder,OG_bcgw_username,OG_bcgw_password,OG_inputxlslayer)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 4 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s4time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 4 complted in: ' + s4time)
w5.VRI2_Prep(OG_RunName,OG_BaseFolder,OG_bcgw_username,OG_bcgw_password)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 5 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s5time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 5 complted in: ' + s5time)
w6.VRI2(OG_RunName,OG_BaseFolder)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 6 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s6time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 6 complted in: ' + s6time)
w7.ECA(OG_RunName,OG_BaseFolder,OG_bcgw_username,OG_bcgw_password)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 7 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s7time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 7 complted in: ' + s7time)
w8.wtrshd_prep(OG_RunName,OG_BaseFolder)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 8 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s8time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 8 complted in: ' + s8time)
w9.wtrshd_analysis(OG_RunName,OG_BaseFolder)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 9 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s9time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 9 complted in: ' + s9time)
w10.Results(OG_RunName,OG_BaseFolder,OG_AOIName,OG_custom_aoi_path)
print('=========================================================')
print('---------------------------------------------------------')
print('********************SCRIPT 10 COMPLETE********************')
print('---------------------------------------------------------')
print('=========================================================')
s10time = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))
print ('Script 10 complted in: ' + s10time)
totalTime = time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))


print('-----------------Duration for each script to complete----------------')
print ('Script 1 complted in: ' + s1time)
print ('Script 3 complted in: ' + s3time)
print ('Script 4 complted in: ' + s4time)
print ('Script 5 complted in: ' + s5time)
print ('Script 6 complted in: ' + s6time)
print ('Script 7 complted in: ' + s7time)
print ('Script 8 complted in: ' + s8time)
print ('Script 9 complted in: ' + s9time)
print ('Script 10 complted in: '+ s10time)
print ('The WHPOR Took ' + totalTime + ' to run.')



