'''
=============================================================================================================
|   Standalone Recovery script for WHPOR_10_Resultant_Outputs.py                                                      |
|   Runs only the maps() and copDevs() functions after a failed run                                        |
|                                                                                                          |
|   IMPORTANT: Close ArcGIS Pro before running this script!                                                |
|                                                                                                          |
|   Usage:                                                                                                 |
|       from WHPOR_10_Recovery import RecoverResults                                                       |
|       RecoverResults("Stuart River", r"T:\WHPOR_Temp\Stuart_River")                                      |
=============================================================================================================
'''
import arcpy
import os 
import shutil 
import datetime
import math 

class RecoverResults:
    def __init__(self, wtrshdname, Bfold):
        self.wtrshdname = wtrshdname
        self.Bfold = Bfold

        # User Variables
        WatershedName = self.wtrshdname
        BaseFolder = self.Bfold
        
        # Static variables  
        watershedname = WatershedName.replace(' ', '_')
        today = datetime.datetime.today().strftime(r'%Y%m%d')
        year = str(datetime.datetime.today().year)
        unq_fol = BaseFolder.split("\\")[-1]
        
        outrslt = os.path.join(BaseFolder, r'1_SpatialData\3_ResultantData\Compiled_Watershed_Hazard_Summaries_rw.gdb')
        rprtFolder = os.path.join(BaseFolder, r'2_Reports')
        
        aprxname = os.path.join(BaseFolder, r'1_SpatialData\1_InputData', (watershedname + '.aprx'))
        aprxtemp = r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\WHPOR_APRX_Template_20230713\WHPOR_APRX_Template_20230713.aprx'
        
        mapname = (WatershedName + r' WHPOR Results Map ' + today + '.pdf')
        mapout = os.path.join(BaseFolder, r'3_Maps', mapname)
        tempname = (watershedname + r'_Compiled_Watershed_Hazard_Summaries_' + today + r'.xlsx')
        report_out = os.path.join(rprtFolder, tempname)
        
        arcpy.env.overwriteOutput = True
        clientdir = os.path.join(r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis', year, unq_fol)

        def maps(proProj):
            # Get final watershed data 
            arcpy.env.workspace = outrslt
            print(f"Today's date: {today}")
            namelook = '*Named_' + str(year) + '*'
            triblook = '*Tributaries_' + str(year) + '*'
            waulook = '*WAU_' + str(year) + '*'

            # Set project aprx as working aprx, and select results maps
            print(f"Opening ArcGIS Project: {aprxname}")
            aprx = arcpy.mp.ArcGISProject(aprxname)
            rslt_map = aprx.listMaps('*WHPOR Results Map*')
            rslt_map = rslt_map[0]
            print('-----------------------name of map-----------------------')
            print(rslt_map.name)
            print('-----------------------name of map-----------------------')

            # Get all layers that need data sources changed to new outputs
            named_map_lyrs = rslt_map.listLayers('*Watershed*')
            Trib_map_lyrs = rslt_map.listLayers('*Tributaries*')
            WAU_map_lyrs = rslt_map.listLayers('*WAU*')
            xing_den_map_lyrs = rslt_map.listLayers('Stream Crossing Categories')
            print(len(named_map_lyrs))
            print(len(Trib_map_lyrs))
            print(len(WAU_map_lyrs))
            print(len(xing_den_map_lyrs))

            changelst = []
            rsltlst = []
            
            # Get the named watershed final FC and rename all fields to remove any prefixes 
            rslt_name = arcpy.ListFeatureClasses(namelook)
            if len(rslt_name) > 0:
                rslt_name = rslt_name[0]
                rsltlst.append(rslt_name)
                changelst.append(named_map_lyrs)
            else:
                for f in named_map_lyrs:
                    rslt_map.removeLayer(f)
                    print('map layer deleted no named watershed')

            rslt_trib = arcpy.ListFeatureClasses(triblook)
            if len(rslt_trib) > 0:
                rslt_trib = rslt_trib[0]
                rsltlst.append(rslt_trib)
                changelst.append(Trib_map_lyrs)
            else:
                for f in Trib_map_lyrs:
                    rslt_map.removeLayer(f)
                    print('map layer deleted no tribs')

            rslt_wau = arcpy.ListFeatureClasses(waulook)
            if len(rslt_wau) > 0:
                rslt_wau = rslt_wau[0]
                rsltlst.append(rslt_wau)
                changelst.append(WAU_map_lyrs)
            else:
                for f in WAU_map_lyrs:
                    rslt_map.removeLayer(f)
                    print('map layer deleted no waus')

            # Get fields and alter - skip if already renamed
            flds = ['ECASc', 'FSRSc', 'HzRd', 'Psd', 'PsdSc', 'PsdCl', 'RipSc', 'SWHzAr', 'SWHzS', 'SWSHSc', 'StreamSc', 'RevRepUni']
            fnms = ['ECA_Score', 'FSR_XINGS_Score', 'Hazard_Rating', 'Percent_Sediment_Delivery', 'Percent_Sediment_Delivery_Score',
                    'Peak_Sediment_Delivery_Class', 'Riparian_Score', 'StreamWorks_Hazard_Area_Score', 'StreamWorks_Hazard_Score',
                    'Streamworks_Hazard_Sum_Score', 'Streamflow_Score', 'RevRepUni']
            
            for fc in rsltlst:
                print(fc)
                existing_fields = [f.name for f in arcpy.ListFields(fc)]
                for (og, fn) in zip(flds, fnms):
                    if og in existing_fields:
                        arcpy.management.AlterField(in_table=fc, field=og, new_field_name=fn, new_field_alias=fn)
                        print(f'field altered: {og} -> {fn}')
                    else:
                        print(f'field {og} not found (likely already renamed), skipping')
           
            for (lyrs, nm) in zip(changelst, rsltlst):
                print(nm)
                for l in lyrs:
                    origConnPropDict = l.connectionProperties
                    newConnPropDict = {'connection_info': {'database': outrslt},
                            'dataset': nm,
                            'workspace_factory': 'File Geodatabase'}
                    l.updateConnectionProperties(origConnPropDict, newConnPropDict)
                    print(l)
                # Use saveACopy instead of save to avoid lock issues
                try:
                    print(f"Attempting to save .aprx file at: {aprx.filePath}")
                    aprx.save()
                except OSError as e:
                    backup_path = aprx.filePath.replace('.aprx', f'_backup_{today}.aprx')
                    print(f"Save failed, attempting saveACopy to: {backup_path}")
                    aprx.saveACopy(backup_path)
                    print(f"Saved copy to: {backup_path}")

            # Update xing connection properties 
            origConnPropDict = xing_den_map_lyrs[0].connectionProperties
            newConnPropDict = {'connection_info': {'database': outrslt},
                            'dataset': rslt_name,
                            'workspace_factory': 'File Geodatabase'}
            xing_den_map_lyrs[0].updateConnectionProperties(origConnPropDict, newConnPropDict)

            print('WAU watershed connections changed')
            try:
                print(f"Attempting to save .aprx file at: {aprx.filePath}")
                aprx.save()
            except OSError as e:
                backup_path = aprx.filePath.replace('.aprx', f'_backup2_{today}.aprx')
                print(f"Save failed, attempting saveACopy to: {backup_path}")
                aprx.saveACopy(backup_path)

            # Set map elements
            lyout = aprx.listLayouts('WHPOR Results Map')[0]
            mfrm = lyout.listElements("MAPFRAME_ELEMENT")[0]
            
            title = lyout.listElements('TEXT_ELEMENT', 'Title')[0]
            title.text = WatershedName + ':\nWHPOR Results'
            scaleBar = lyout.listElements("MAPSURROUND_ELEMENT", 'Alternating Scale Bar')[0]
            print('Title updated')

            # Zoom to watershed AOI
            unq1 = [f.name for f in arcpy.ListFields(named_map_lyrs[0], '*RevRepuni')][0]
            exprs = unq1 + ' IS NOT NULL'
            arcpy.management.SelectLayerByAttribute(named_map_lyrs[0], 'NEW_SELECTION', exprs)
            mfrm.camera.setExtent(mfrm.getLayerExtent(named_map_lyrs[0]))
            scale = int(mfrm.camera.scale)
            arcpy.SelectLayerByAttribute_management(named_map_lyrs[0], "CLEAR_SELECTION")
            print(scale)
            print(len(str(scale)))
            
            # Round map scale 
            if len(str(scale)) == 4:
                new_scale = math.ceil(scale / 500) * 500
            elif len(str(scale)) == 5:
                new_scale = math.ceil(scale / 5000) * 5000
            elif len(str(scale)) == 6:
                new_scale = math.ceil(scale / 50000) * 50000
            elif len(str(scale)) == 7:
                new_scale = math.ceil(scale / 500000) * 500000
            elif len(str(scale)) == 8:
                new_scale = math.ceil(scale / 5000000) * 5000000
            print(new_scale)
            
            # Set map scale
            mfrm.camera.scale = int(new_scale)
            print('scale rounded from ', scale, ' to ', new_scale)
            
            # Set Scale Bar
            scaleBar = lyout.listElements("MAPSURROUND_ELEMENT", 'Alternating Scale Bar')[0]
            mf = scaleBar.mapFrame
            xpos = mf.elementWidth - scaleBar.elementWidth - 0.05
            scaleBar.elementPositionX = xpos
            scaleBar.elementPositionY = 2.45
            
            try:
                print(f"Attempting to save .aprx file at: {aprx.filePath}")
                aprx.save()
            except OSError as e:
                backup_path = aprx.filePath.replace('.aprx', f'_backup3_{today}.aprx')
                print(f"Save failed, attempting saveACopy to: {backup_path}")
                aprx.saveACopy(backup_path)
            
            print('Scale Bar Adjusted')
            print('export map')
            lyout.exportToPDF(mapout)
            print('Layout exported to ', mapout)
            
            try:
                print(f"Attempting final save of .aprx file at: {aprx.filePath}")
                aprx.save()
            except OSError as e:
                final_backup = aprx.filePath.replace('.aprx', f'_final_{today}.aprx')
                print(f"Final save failed, saving copy to: {final_backup}")
                aprx.saveACopy(final_backup)
                print(f"NOTE: Original .aprx could not be updated. Changes saved to: {final_backup}")
                print("You may need to manually copy this file over the original after closing ArcGIS Pro.")

        def copDevs(final_location):
            if not os.path.exists(final_location):
                os.makedirs(final_location)

            map_nm_like = (WatershedName + r' WHPOR Results Map ' + str(year))
            for root, dirs, files in os.walk(os.path.join(BaseFolder, r'3_Maps')):
                for file in files:
                    if file.startswith(map_nm_like):
                        shutil.copy(mapout, os.path.join(final_location, mapname))
            
            rprt_nm_like = (watershedname + r'_Compiled_Watershed_Hazard_Summaries_' + str(year))
            for root, dirs, files in os.walk(rprtFolder):
                for file in files:
                    if file.startswith(rprt_nm_like):
                        shutil.copy(os.path.join(rprtFolder, file), os.path.join(final_location, tempname))

            print('MAP and Spreadsheet copied to final location')
            print('\n\n\n\n\n\n\n\n\n\n\n')
            print('==========================================================================================================================================================================================')
            print('****************FINAL DELIVERABLES****************FINAL DELIVERABLES****************FINAL DELIVERABLES****************FINAL DELIVERABLES****************FINAL DELIVERABLES****************')
            print('==========================================================================================================================================================================================')
            print(mapout)
            print(report_out)
            print(outrslt)
            print('Client Directory with deliverables in place')
            print(clientdir)
            print('==========================================================================================================================================================================================')
            print('RECOVERY COMPLETE!')
            print('==========================================================================================================================================================================================')

        # ===== Call Functions =====
        print("=" * 80)
        print("WHPOR Module 10 Recovery Script")
        print("=" * 80)
        print(f"Watershed: {WatershedName}")
        print(f"Base Folder: {BaseFolder}")
        print(f"APRX File: {aprxname}")
        print("=" * 80)
        print("\nIMPORTANT: Make sure ArcGIS Pro is CLOSED before continuing!\n")
        
        maps(aprxtemp)
        copDevs(clientdir)


# Direct execution
if __name__ == "__main__":
    # Change these values to match your failed run
    watershed_name = "Stuart River"
    base_folder = r"T:\WHPOR_Temp\Stuart_River"
    
    print("Starting WHPOR Module 10 Recovery...")
    print("Make sure ArcGIS Pro is CLOSED!\n")
    
    RecoverResults(watershed_name, base_folder)
