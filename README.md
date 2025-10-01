# WHPOR: Watershed Health Project Omineca Region

**Requirements:**

- Access to the OM NAS drive (\\\\142.27.147.234\\spatialfiles2work) mapped to N:
- Access to the Geospatial GTS (ArcPro and Python 3)
- Access to the OS (T:) Drive on the GTS
- Python Package pypiwin32 (available on some GTS servers but not all…)

**Project Location:** [\\\\142.27.147.234\\spatialfiles2work\\FOR_RNI_RNI_Projects\\WHPOR_Watershed_Analysis](file:///\\142.27.147.234\spatialfiles2work\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis)

## Folder Structure

### WHPOR_Watershed_Analysis - Main Folder

- !WHPOR_Stage - Contains all Prior Documentation, Resources, and scripts
- 1_WHPOR_Analyses - All data that is created and deliverables, sorted by year and watershed
- 2_WHPOR_Model - Contains specific local datasets used in processing
- 3_Outgoing - previous communications, infrequently used

### !WHPOR_Stage

- 1_WHPOR_Documentation - documentation for manually running the WHPOR, and individual processes included in the WHPOR. Be cautious of versions and when the documents were created
- 2_WHPOR_Resources - Templates, layer files, stand-alone scripts from before the automation,

copies of John Rex's presentations, great resources for learning about watersheds and what the WHPOR produces.

- 3_ArcMap_Model - Resources for running the watershed analysis script, currently the automation pulls the watershed input CSV from here and the PCS_Albers.prj file
- **4_WHPOR_Automated - This folder contains all the scripts for the automated WHPOR**
  - **Masters- This folder contains the master copies of the current version of the WHPOR, only access these if you have functional, tested changes to the WHPOR**
  - **Scripts - working copies of the WHPOR SCRIPTS. This folder contains modified scripts for ECA only, Stand-alone scripts, and the WHPOR script folder.**

# Running the AUTOMATED WHPOR

The WHPOR is now a collection of 12 Python files. Some scripts have been around since 2012, modified and upgraded to python3, while others were created within the last year(2023). All of the scripts need to be **in the same folder.** When the main script runs, it will pull all the classes and functions from each other. A breakdown of each of the scripts can be found after the troubleshooting section. To run the WHPOR, you need A watershed name and the watershed key. Often, the watershed name is provided, but the key you will have to look up, the steps to do so are in the following section.

Be aware that anything processed on the Temp drive will be removed once you sign out. If you have 4-day disconnect privileges, you can run the WHPOR over the weekend using disconnect instead of signing out.

**Spatial files must be copied to the NAS drive once the analysis is completed!**

## Deliverables

1x Compiled Spreadsheet

1x Pdf map

Infrequently requested- shapes with spreadsheet data

## Get Watershed Key

The client should provide the watershed name, which is what you will use to look up the watershed key from the BCGW feature class WHSE_BASEMAPPING.FWA_NAMED_WATERSHEDS_POLY, you can use your preferred GIS software if you like, or you can quickly search the watershed by using SQL Developer on the GTS (Directions for setting up SQL Dev can be found [**Here**](file:///\\142.27.147.234\spatialfiles2work\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\!WHPOR_Stage\1_WHPOR_Documentation\SQL_Dev_Intro.docx))

In SQL Dev, use the query:

select \* from WHSE_BASEMAPPING.FWA_NAMED_WATERSHEDS_POLY

where GNIS_NAME LIKE '%Table%'

Replace the string in quotes to whatever watershed you are looking for be sure to keep the % signs on either side. Be aware that there may be multiple watersheds with the same name or have the suffix creek or river. If there are multiple, verify which watershed you are meant to process. The GNIS_Name and Watershed_Key are the variables that are needed to run the WHPOR.


## Preparation before running the WHPOR

- Are the T: and N: drives mapped on your GTS? There may be a mix of UNC paths and mapped drive paths within the processing.
- Navigate to [\\\\142.27.147.234\\spatialfiles2work\\FOR_RNI_RNI_Projects\\WHPOR_Watershed_Analysis\\!WHPOR_Stage\\4_WHPOR_Automated\\Scripts](file:///\\142.27.147.234\spatialfiles2work\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\!WHPOR_Stage\4_WHPOR_Automated\Scripts) and copy the entire WHPOR folder to your T drive or a location on your work area on the W drive

- Once you have copied the script folder to your preferred location, right-click on it and "Open with Code."

- Once in Visual Studio Code (VS or VSC), only one script needs to be interacted with, WHPOR_Fully_Loaded.py. This script will run and call all the other scripts is the only script that needs to be used.

- Open the Fully Loaded .py file. Two variables need to be changed, OG_WatershedName and OG_watershed_key, currently there are found on lines 47 and 48 (circled in red)
- Once the two variables have been changed, you can now run the WHPOR, the button circled in blue.
- After the script starts running, you will be prompted to enter your bcgw username and password. Then you can sit back and relax…. Maybe
- Once the script is complete, it will automatically put the deliverables in [\\\\spatialfiles.bcgov\\Work\\for\\RNI\\RNI\\Projects\\WHPOR_Watershed_Analysis\\ Current](file:///\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\%20Current) Year for the client, **Verify the deliverables are in the folder and are correct and rename the folder with the prefix of the next sequential number**
- Copy all data produced on the T drive from the analysis and paste it into the WHPOR analysis folder under the correct year etc.
- Once you are sure that all data is correct and all files are in the correct location, email the client to tell them you have finished the analysis and that the deliverables are in the folder **xxxxxx**

## Trouble Shooting

### win32com

The script may fail right off the bat because not all geospatial GTS servers have the Python module win32com (picture of the error below)


To fix this, go to your command prompt in the gts by searching cmd in the start menu. Enter the following code and hit enter to install a local copy of pywin32com to your profile.

python -m pip install pypiwin32 --user

To verify you now have access to pypiwin32 you can type the code below into the command prompt to list all packages included in the current Python env

Python -m pip list

Finally, close VS code, open the folder again, and hit the go button.

### No T: Temp Drive

if you don't the script will fail, to regain access to the temp drive, open the command prompt (search cmd in the search bar) and copy and paste the following code  
<br/>%SYSTEMROOT%\\SYSTEM32\\SUBST.EXE T: %TEMP%

After running the command your T drive will be back!

## Script Breakdown

### WHPOR_Fully_Loaded.py

Written by C Folkers 2023

Creates folder structures and controls the entire analysis

### WHPOR_01_Tributary_Watersheds.py

Written by C Folkers 2023

Creates the tributary watersheds by tracing streams backwards from where they enter the mainstream/river and up to the upper reaches of their basins. Based on a script that Noelle wrote but re-tooled to work more efficiently and correctly

### WHPOR_03_DataPrep.py

Written By N Bouvier 2022

Reformatted by Folkers 2023

The script was originally a jupyter notebook, gathers remaining data for watersheds, creates the OM watershed gdb, and creates and fills out new attributes necessary for processing, including unique IDs, stream order etc.

### WHPOR_04_SimplePrep.py

Written by C Folkers 2023

Queries, clips, dissolve all data sources needed for ECA, VRI2 and CEA watershed calculations. It is controlled by a messy spreadsheet called Layer_Master, found [here](file:///\\142.27.147.234\spatialfiles2work\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\!WHPOR_Stage\4_WHPOR_Automated\Input_Spreadsheet\Layer_Master.xlsx)

### WHPOR_05_VRI2_Prep.py

Written by N Bouvier 2022, modified and appended by C Folkers 2023

More data downloading, moving things around

### WHPOR_06_VRI2.py

Written by G MacGregor 2012, revisions by S Lees, C Folkers

Creates updated VRI data that uses RESULTS and FTEN to capture additional forest activities for a more well-rounded image of the vegetated landscape.

### WHPOR_07_ECA.py

Written by C Folkers 2023

Calculates ECA factor and Type, including pine presence, MPB factor, Height factor, and dead percentages

### WHPOR_08_Watershed_Analysis_Prep.py

Written by C Folkers 2023

Transfers files around and fills in spreadsheets with available data, sources and queries.

### WHPOR_09_CEA_watershed_analysis_20220628_V2.py

Written by G MacGregor, S Lees, G Smith 2013

Revisions and Modifications By N Bouvier 2021, C Folkers 2023

This is a modified version of the Thompson Okanagan script to create watershed hazard scores and produce results spreadsheets. It's a beast that is due for an upgrade.

### WHPOR_10_Resultant_Outputs.py

Written by C Folkers 2023

Moves products to final locations, Calculates Final ECA score/rating, Builds complied spreadsheet (Deliverable), creates spatial watershed features with CEA hazard calculations, and produces PDF map(Deliverable)

### overlapmod_py3.py

Written by G MacGregor 2013

Module used in VRI 2 script and possibly in CEA watershed analysis scripts to check any input feature class for polygon overlap, then output a new file or overwrite the existing and clean up overlaps.

### CEA_Module_NB.py

Written by N Bouvier Modified by C Folkers

Various Functions used throughout WHPOR analysis

# Further Work

- Drought Risk Score- John Rex to guide
- Better folder structure
- Make WHPOR_04_SimplePrep.py less messy and organized better
- Organize unique ID
- Delete transitory data
- WHPOR_09 script, loop to use the same gdb instead of creating new ones for each watershed level
- Automatic transfer of data to NAS drive
- Automatic email to client
- Replace wincom32 with something else. It needs the ability to activate formulas in the spreadsheet
- Change Final ECA calcs from script 10 to script 7
