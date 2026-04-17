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
|       RecoverResults("Stuart River", r"T:\WHPOR_Temp\Stuart_River", "Stuart River AOI")                 |
|       RecoverResults("Stuart River", r"T:\WHPOR_Temp\Stuart_River", "Stuart River AOI", r"T:\...\AOI") |
=============================================================================================================
'''
import arcpy
import os 
import shutil 
import datetime
import math 

class RecoverResults:
    def __init__(self, wtrshdname, Bfold, aoi_name=None, custom_aoi_path=None):
        self.wtrshdname = wtrshdname
        self.Bfold = Bfold
        self.aoi_name = aoi_name
        self.custom_aoi_path = custom_aoi_path

        # User Variables
        WatershedName = self.wtrshdname
        BaseFolder = self.Bfold
        AOIName = self.aoi_name
        CustomAOIPath = self.custom_aoi_path
        CustomAOIUsed = CustomAOIPath not in [None, '']
        OutputLabel = AOIName if CustomAOIUsed and AOIName not in [None, ''] else WatershedName
        MapTitleName = OutputLabel
        
        # Static variables  
        watershedname = WatershedName.replace(' ', '_')
        outputlabel = OutputLabel.replace(' ', '_')
        today = datetime.datetime.today().strftime(r'%Y%m%d')
        year = str(datetime.datetime.today().year)
        unq_fol = BaseFolder.split("\\")[-1]
        
        outrslt = os.path.join(BaseFolder, r'1_SpatialData\3_ResultantData\Compiled_Watershed_Hazard_Summaries_rw.gdb')
        rprtFolder = os.path.join(BaseFolder, r'2_Reports')
        
        aprxname = os.path.join(BaseFolder, r'1_SpatialData\1_InputData', (watershedname + '.aprx'))
        aprxtemp = r'\\spatialfiles.bcgov\Work\for\RNI\RNI\Projects\WHPOR_Watershed_Analysis\working\source_data\WHPOR_APRX_Template_20230713\WHPOR_APRX_Template_20230713.aprx'
        
        mapname = (OutputLabel + r' WHPOR Results Map ' + today + '.pdf')
        mapout = os.path.join(BaseFolder, r'3_Maps', mapname)
        tempname = (outputlabel + r'_Compiled_Watershed_Hazard_Summaries_' + today + r'.xlsx')
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
            title.text = MapTitleName + ':\nWHPOR Results'
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
            else:
                new_scale = scale
            print(new_scale)
            
            # Apply 10% zoom-out and re-round to a clean map scale.
            zoomed_scale = int(new_scale * 1.10)
            if len(str(zoomed_scale)) == 4:
                final_scale = math.ceil(zoomed_scale / 500) * 500
            elif len(str(zoomed_scale)) == 5:
                final_scale = math.ceil(zoomed_scale / 5000) * 5000
            elif len(str(zoomed_scale)) == 6:
                final_scale = math.ceil(zoomed_scale / 50000) * 50000
            elif len(str(zoomed_scale)) == 7:
                final_scale = math.ceil(zoomed_scale / 500000) * 500000
            elif len(str(zoomed_scale)) == 8:
                final_scale = math.ceil(zoomed_scale / 5000000) * 5000000
            else:
                final_scale = zoomed_scale

            # Set map scale
            mfrm.camera.scale = int(final_scale)
            print('scale rounded from ', scale, ' to ', new_scale)
            print('scale after 10% zoom out ', final_scale)
            
            # Constrain scale bar to the map frame so it cannot run off-frame.
            scaleBar = lyout.listElements("MAPSURROUND_ELEMENT", 'Alternating Scale Bar')[0]
            # Re-apply a known labeled alternating style if available.
            try:
                if hasattr(scaleBar, 'applyStyleItem'):
                    applied_style = False
                    style_names = ['ArcGIS 2D', 'ArcGIS 2D (System)', 'ArcGIS']
                    style_classes = ['Scale_Bar', 'Scale_bar', 'SCALE_BAR', 'Scale Bar']
                    style_wildcards = ['Alternating Scale Bar*', 'Double Alternating Scale Bar*', 'Alternating*', '*Scale Bar*']
                    for st in style_names:
                        if applied_style:
                            break
                        for sc in style_classes:
                            if applied_style:
                                break
                            for wc in style_wildcards:
                                try:
                                    items = aprx.listStyleItems(st, sc, wc)
                                    if items:
                                        scaleBar.applyStyleItem(items[0])
                                        applied_style = True
                                        print('Scale bar style applied:', st, sc, items[0].name)
                                        break
                                except Exception:
                                    pass
                    if not applied_style:
                        print('No labeled scale bar style item found; keeping existing style')
            except Exception as e:
                print('Scale bar style apply skipped:', e)

            frame_left = mfrm.elementPositionX
            frame_bottom = mfrm.elementPositionY
            frame_right = frame_left + mfrm.elementWidth
            frame_top = frame_bottom + mfrm.elementHeight

            left_margin = 0.05
            right_margin = 0.10
            y_margin = 0.05
            target_y = 2.45
            right_label_buffer = 0.70
            left_limit = frame_left + left_margin
            frame_right_limit = frame_right - right_margin
            right_limit = frame_right_limit

            # Align scale bar right edge with north arrow x when available.
            north_arrow_elements = lyout.listElements("MAPSURROUND_ELEMENT", "*North*")
            if not north_arrow_elements:
                north_arrow_elements = lyout.listElements("MAPSURROUND_ELEMENT", "*north*")
            if north_arrow_elements:
                north_arrow_x = north_arrow_elements[0].elementPositionX
                if left_limit + 0.5 < north_arrow_x <= frame_right_limit:
                    right_limit = north_arrow_x
                    print('Scale bar right edge aligned to north arrow x:', round(north_arrow_x, 3))
                else:
                    print('North arrow x outside safe range; using frame right limit')
            else:
                print('North arrow element not found; using frame right limit')

            if right_limit <= left_limit + 0.5:
                right_limit = frame_right_limit

            label_safe_right = right_limit - right_label_buffer
            if label_safe_right <= left_limit + 0.5:
                label_safe_right = frame_right_limit - right_label_buffer

            max_allowed_width = max(0.8, label_safe_right - left_limit)
            target_width = max(0.8, mfrm.elementWidth * 0.35)
            desired_width = min(target_width, max_allowed_width)
            target_total_km = max(0.2, (final_scale * desired_width * 0.0254) / 1000.0)
            division_km = max(0.05, target_total_km / 4.0)

            # Keep a visible alternating pattern and prevent width auto-growth.
            try:
                scalebar_cim = scaleBar.getDefinition('V3')
                if hasattr(scalebar_cim, 'fittingStrategy'):
                    try:
                        scalebar_cim.fittingStrategy = 'AdjustDivision'
                    except Exception:
                        scalebar_cim.fittingStrategy = 0
                if hasattr(scalebar_cim, 'divisions'):
                    scalebar_cim.divisions = 4
                if hasattr(scalebar_cim, 'division'):
                    scalebar_cim.division = division_km
                if hasattr(scalebar_cim, 'subdivisions'):
                    scalebar_cim.subdivisions = 0
                if hasattr(scalebar_cim, 'labelFrequency'):
                    try:
                        scalebar_cim.labelFrequency = 'Divisions'
                    except Exception:
                        scalebar_cim.labelFrequency = 3
                if hasattr(scalebar_cim, 'displayFirstOutside'):
                    scalebar_cim.displayFirstOutside = True
                if hasattr(scalebar_cim, 'displayLastOutside'):
                    scalebar_cim.displayLastOutside = True
                if hasattr(scalebar_cim, 'markFrequency'):
                    try:
                        scalebar_cim.markFrequency = 'None'
                    except Exception:
                        scalebar_cim.markFrequency = 0
                if hasattr(scalebar_cim, 'divisionMarkHeight'):
                    scalebar_cim.divisionMarkHeight = 0
                if hasattr(scalebar_cim, 'subdivisionMarkHeight'):
                    scalebar_cim.subdivisionMarkHeight = 0
                if hasattr(scalebar_cim, 'labelGap'):
                    scalebar_cim.labelGap = 1.5
                if hasattr(scalebar_cim, 'unitLabelGap'):
                    scalebar_cim.unitLabelGap = 1.5
                if hasattr(scalebar_cim, 'units'):
                    try:
                        scalebar_cim.units = {'uwkid': 9036}
                    except Exception:
                        try:
                            scalebar_cim.units = {'wkid': 9036}
                        except Exception:
                            pass
                if hasattr(scalebar_cim, 'showLabels'):
                    scalebar_cim.showLabels = True
                if hasattr(scalebar_cim, 'showDivisionLabels'):
                    scalebar_cim.showDivisionLabels = True
                if hasattr(scalebar_cim, 'showFirstLabel'):
                    scalebar_cim.showFirstLabel = True
                if hasattr(scalebar_cim, 'showLastLabel'):
                    scalebar_cim.showLastLabel = True
                if hasattr(scalebar_cim, 'showUnitLabel'):
                    scalebar_cim.showUnitLabel = True
                if hasattr(scalebar_cim, 'unitLabel'):
                    scalebar_cim.unitLabel = 'km'
                if hasattr(scalebar_cim, 'unitLabelPosition'):
                    try:
                        scalebar_cim.unitLabelPosition = 'AfterBar'
                    except Exception:
                        scalebar_cim.unitLabelPosition = 4
                if hasattr(scalebar_cim, 'labelSymbol') and hasattr(scalebar_cim, 'unitLabelSymbol'):
                    if scalebar_cim.unitLabelSymbol:
                        scalebar_cim.labelSymbol = scalebar_cim.unitLabelSymbol
                if hasattr(scalebar_cim, 'numberFormat') and scalebar_cim.numberFormat:
                    if hasattr(scalebar_cim.numberFormat, 'roundingValue'):
                        if division_km >= 1:
                            scalebar_cim.numberFormat.roundingValue = 1
                        elif division_km >= 0.1:
                            scalebar_cim.numberFormat.roundingValue = 0.1
                        else:
                            scalebar_cim.numberFormat.roundingValue = 0.01
                if hasattr(scalebar_cim, 'labelPosition'):
                    try:
                        scalebar_cim.labelPosition = 'Above'
                    except Exception:
                        scalebar_cim.labelPosition = 0
                available_label_props = [
                    p for p in [
                        'displayFirstOutside', 'displayLastOutside', 'labelFrequency', 'labelPosition',
                        'labelSymbol', 'unitLabel', 'unitLabelPosition', 'unitLabelSymbol', 'numberFormat'
                    ] if hasattr(scalebar_cim, p)
                ]
                print('Scale bar CIM label props available:', available_label_props)
                scaleBar.setDefinition(scalebar_cim)
                print('Scale bar divisions, fitting strategy, and labels set (division_km=', round(division_km, 3), ')')
            except Exception as e:
                print('Scale bar division update skipped:', e)

            try:
                scaleBar.setAnchor("BOTTOM_RIGHT_CORNER")
            except Exception:
                pass

            scaleBar.elementWidth = desired_width
            scaleBar.elementPositionX = right_limit
            min_y = frame_bottom + y_margin
            max_y = max(min_y, frame_top - scaleBar.elementHeight - y_margin)
            scaleBar.elementPositionY = max(min_y, min(target_y, max_y))

            # Re-clamp after CIM updates in case the style recalculates width.
            if scaleBar.elementWidth > max_allowed_width:
                scaleBar.elementWidth = max_allowed_width

            left_edge = scaleBar.elementPositionX - scaleBar.elementWidth
            if left_edge < left_limit:
                scaleBar.elementWidth = max(0.8, scaleBar.elementPositionX - left_limit)
                left_edge = scaleBar.elementPositionX - scaleBar.elementWidth

            print('Scale bar constrained to frame: left', round(left_edge, 3), 'right', round(scaleBar.elementPositionX, 3), 'target_right', round(right_limit, 3), 'frame_right', round(frame_right - right_margin, 3), 'width', round(scaleBar.elementWidth, 3))
            
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

            map_nm_like = (OutputLabel + r' WHPOR Results Map ' + str(year))
            for root, dirs, files in os.walk(os.path.join(BaseFolder, r'3_Maps')):
                for file in files:
                    if file.startswith(map_nm_like):
                        shutil.copy(mapout, os.path.join(final_location, mapname))
            
            rprt_nm_like = (outputlabel + r'_Compiled_Watershed_Hazard_Summaries_' + str(year))
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
    aoi_name = watershed_name
    custom_aoi_path = None
    
    print("Starting WHPOR Module 10 Recovery...")
    print("Make sure ArcGIS Pro is CLOSED!\n")
    
    RecoverResults(watershed_name, base_folder, aoi_name, custom_aoi_path)
