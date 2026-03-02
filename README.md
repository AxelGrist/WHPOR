# Watershed Health Project: Omineca Region (WHPOR)

## Overview

The **Watershed Health Project Omineca Region (WHPOR)** is a GIS-based watershed hazard assessment tool developed by the BC Ministry of Forests as part of the provincial Cumulative Effects Framework (CEF). It provides standardized relative hazard assessments across Watershed Assessment Units (WAU) for three key hazard types:

### Hazard Types Assessed

| Hazard | Description | Key Indicators |
|--------|-------------|----------------|
| **Streamflow Hazard** | Likelihood of increased peak flow, particularly during spring snowmelt | Equivalent Clearcut Area (ECA), BEC zone snow levels, drainage density, wetland/lake attenuation |
| **Sediment Hazard** | Likelihood of increased sediment generation and delivery to streams | Road density, stream crossing density, roads on steep slopes, roads near streams, terrain stability, gentle-over-steep terrain |
| **Riparian Hazard** | Likelihood of disturbance altering freshwater and terrestrial riparian attributes | Forest harvesting intrusion within 20m of streams, range tenures, private land parcels |

### Key Concepts

- **Equivalent Clearcut Area (ECA)**: Proportion of watershed with forest canopy disturbance (harvesting, wildfire, beetle kill) factored by hydrological recovery
- **Watershed Assessment Units (WAU)**: Standardized areas of 2,000-10,000 ha (target 3,000 ha) emulating third-order watersheds at 1:50,000 scale
- **Attenuation Potential**: Watershed's ability to buffer response at outlet based on wetlands, lakes, drainage density, and slope

### Reference Documentation

For the full methodology, see: [Current Condition Report for GIS-Based Watershed Hazard in the Omineca Region (Rex et al., 2022)](https://www2.gov.bc.ca/assets/gov/environment/natural-resource-stewardship/cumulative-effects/omineca-region/cef-ominecawatershedhazardassessment-ccr-2024.pdf)

---

## Requirements

- Access to the OM NAS drive (`\\142.27.147.234\spatialfiles2work`) mapped to N:
- Access to the Geospatial GTS (ArcGIS Pro and Python 3)
- Access to the OS (T:) Drive on the GTS
- Python package `pywin32` (may require manual installation on some GTS servers)

**Project Location:** [\\\\142.27.147.234\\spatialfiles2work\\FOR_RNI_RNI_Projects\\WHPOR_Watershed_Analysis](file:///\\142.27.147.234\spatialfiles2work\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis)

## Folder Structure

### WHPOR_Watershed_Analysis (Main Folder)

- `!WHPOR_Stage/` - Documentation, resources, and scripts
- `1_WHPOR_Analyses/` - Output data and deliverables, organized by year and watershed
- `2_WHPOR_Model/` - Local datasets used in processing
- `3_Outgoing/` - Archived communications

### !WHPOR_Stage

- `1_WHPOR_Documentation/` - Documentation for manually running the WHPOR and individual processes. Note: verify document versions before use.
- `2_WHPOR_Resources/` - Templates, layer files, stand-alone scripts, and reference presentations.
- `3_ArcMap_Model/` - Legacy resources; automation pulls watershed input CSV and PCS_Albers.prj from here.
- `4_WHPOR_Automated/` - **Automated WHPOR scripts**
  - `Masters/` - Master copies of current version (modify only with tested changes)
  - `Scripts/` - Working copies including ECA-only and stand-alone variants

## Running the Automated WHPOR

The WHPOR consists of 12 Python modules that must be located in the same folder. The main script (`WHPOR_Fully_Loaded.py`) orchestrates all other modules. To run the WHPOR, you need:

1. A watershed name (provided by the client)
2. A watershed key (lookup procedure described below)

> **Warning:** Data processed on the T: drive is deleted upon sign-out. Use disconnect privileges for multi-day processing.

> **Important:** Copy all spatial files to the NAS drive upon completion.

## Deliverables

| Output | Description |
|--------|-------------|
| **Compiled Spreadsheet** | Excel workbook with hazard scores for Named Watershed, Tributaries, and WAU tabs |
| **PDF Map** | WHPOR Results Map showing hazard classifications |
| **Geodatabase** | `Compiled_Watershed_Hazard_Summaries_rw.gdb` containing spatial polygon features with all hazard attributes (located in `1_SpatialData\3_ResultantData\`) |

**Note:** The geodatabase contains the same data as the spreadsheet but with polygon geometry, allowing spatial visualization in ArcGIS. The `RevRepUni` field links spreadsheet rows to spatial features.

## Get Watershed Key

Look up the watershed key from `WHSE_BASEMAPPING.FWA_NAMED_WATERSHEDS_POLY` using the watershed name provided by the client. Use SQL Developer on the GTS or your preferred GIS software.

**SQL Query:**

```sql
SELECT * FROM WHSE_BASEMAPPING.FWA_NAMED_WATERSHEDS_POLY
WHERE GNIS_NAME LIKE '%WatershedName%'
```

Replace the search term while keeping the `%` wildcards. Note: Multiple watersheds may share the same name (e.g., with "Creek" or "River" suffix). Verify you have the correct watershed before proceeding.

## Preparation

1. Verify T: and N: drives are mapped on your GTS session.
2. Copy the WHPOR folder from `\\142.27.147.234\spatialfiles2work\FOR_RNI_RNI_Projects\WHPOR_Watershed_Analysis\!WHPOR_Stage\4_WHPOR_Automated\Scripts` to your T: or W: drive.
3. Open the folder in Visual Studio Code (right-click → "Open with Code").
4. Open `WHPOR_Fully_Loaded.py` and update lines 47-48:
   - `OG_WatershedName` - the watershed name
   - `OG_watershed_key` - the watershed key from BCGW
5. Run the script (F5 or Run button).
- After the script starts, enter your BCGW username and password when prompted.
- Upon completion, deliverables are automatically placed in the current year folder at `\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\`
- Verify deliverables are correct and rename the folder with the next sequential number prefix.
- Copy all T: drive data to the appropriate WHPOR analysis folder.
- Notify the client via email with the deliverables folder location.

## Troubleshooting

### win32com Module Missing

The script may fail immediately if the `win32com` module is not installed. To resolve:

```cmd
python -m pip install pywin32 --user
```

Verify installation:

```cmd
python -m pip list
```

Restart VS Code and run the script again.

### T: Drive Not Available

If the T: drive is missing, restore it by running this command in Command Prompt:

```cmd
%SYSTEMROOT%\SYSTEM32\SUBST.EXE T: %TEMP%
```

## Script Reference

| Script | Purpose |
|--------|--------|
| `WHPOR_Fully_Loaded.py` | Main controller - creates folder structures and orchestrates all modules |
| `WHPOR_01_Tributary_Watersheds.py` | Generates tributary watersheds by tracing streams from confluence to headwaters |
| `WHPOR_03_DataPrep.py` | Downloads watershed data, creates OM watershed GDB, populates attributes (IDs, stream order) |
| `WHPOR_04_SimplePrep.py` | Queries, clips, and dissolves data sources for ECA, VRI2, and CEA calculations |
| `WHPOR_05_VRI2_Prep.py` | Prepares and stages VRI data for processing |
| `WHPOR_06_VRI2.py` | Creates updated VRI using RESULTS and FTEN to capture additional forest activities |
| `WHPOR_07_ECA.py` | Calculates ECA factor and type (pine presence, MPB factor, height factor, dead %) |
| `WHPOR_08_Watershed_Analysis_Prep.py` | Stages files and populates input spreadsheets with data sources |
| `WHPOR_09_CEA_watershed_analysis.py` | Calculates watershed hazard scores and generates results spreadsheets |
| `WHPOR_10_Resultant_Outputs.py` | Generates deliverables: final ECA scores, compiled spreadsheet, spatial features, PDF map |
| `overlapmod_py3.py` | Utility module for detecting and resolving polygon overlaps |
| `CEA_Module_NB.py` | Shared utility functions used throughout WHPOR analysis |

## Required Source Data

The WHPOR scripts require several large data files that are not included in this repository due to size constraints. These files are located on the network drive:

**Location:** `\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\`

| File/Folder | Description | Size |
|-------------|-------------|------|
| `bc25fill/` | DEM raster (filled) | ~2.6 GB |
| `bc25per2/` | DEM raster (percent slope) | ~1.5 GB |
| `2_FWA/` | Freshwater Atlas data | ~756 MB |
| `FWA_BC.gdb` | Freshwater Atlas geodatabase | ~161 MB |
| `VRI_BNDY.gdb` | VRI boundary lookup tables (StreamWght_lookup) | ~19 MB |
| `Maps50K.gdb` | 50K mapsheet grid | ~2 MB |
| `WHPOR_APRX_Template_20230713/` | ArcGIS Pro map template | ~1 MB |
| `Compiled_Watershed_Hazard_Summaries_Master8.xlsx` | Output spreadsheet template | ~2 MB |
| `Layer_Master.xlsx` | Data layer configuration | <1 MB |
| `Watershed_Inputs_List_V2.csv` | Watershed input parameters | <1 MB |
| `BCCEF_Buffer_Distance_Table.csv` | Buffer distance lookup | <1 MB |
| `Omineca_BEC_v12_Rating_Classification.csv` | BEC classification ratings | <1 MB |
| `PCS_Albers.prj` | Projection file | <1 KB |

Copy the entire `source_data` folder to your working location, or ensure your scripts point to the network path.

## Roadmap

- [ ] Drought Risk Score integration
- [ ] Refactor folder structure
- [ ] Refactor WHPOR_04_SimplePrep.py
- [ ] Standardize unique ID handling
- [ ] Clean up transitory data
- [ ] Optimize WHPOR_09 to use single GDB per run
- [ ] Automatic NAS drive transfer
- [ ] Automatic client notification
- [ ] Replace win32com dependency
- [ ] Move final ECA calculations from Module 10 to Module 07

# Authors

Original developers of the WHPOR scripts:

- Mark McGirr - Original VRI programming
- Will Burt - Original VRI programming  
- Graham MacGregor - VRI2 script, CEA watershed analysis, overlap module (2012-2013)
- Sasha Lees - VRI2 revisions, MPB criteria, coal lease scoring (2014)
- Gail Smith - CEA watershed analysis (2013)
- Noelle Bouvier - CEA modifications, geometry field flexibility (2021-2022)
- C. Folkers - Python 3 migration, automation framework (2023)