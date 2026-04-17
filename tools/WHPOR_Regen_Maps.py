'''
=============================================================================================================
|   Standalone Map Regeneration Script for WHPOR                                                                      |
|   Regenerates PDF maps from existing .aprx files with zoom-out fix                                       |
|                                                                                                          |
|   IMPORTANT: Close ArcGIS Pro before running this script!                                                |
|                                                                                                          |
|   Usage:                                                                                                 |
|       python WHPOR_Regen_Maps.py                                                                         |
=============================================================================================================
'''
import arcpy
import os 
import datetime
import math 

# Configuration
BASE_PATH = r"W:\FOR\RNI\RNI\Projects\WHPOR_Watershed_Analysis\2026\JPRF"
ZOOM_OUT_FACTOR = 1.10  # 10% zoom out (increase scale by 10%)

# Watersheds to process - tuple of (folder_name, display_name)
WATERSHEDS = [
    ("Babine_River", "Babine River"),
    ("Kilner_Creek", "Kilner Creek"),
    ("Nation_River", "Nation River"),
    ("Stuart_River", "Stuart River"),
]

def regenerate_map(folder_name, watershed_name):
    """Regenerate a single watershed map with zoom-out fix"""
    
    print("=" * 70)
    print(f"Processing: {watershed_name}")
    print("=" * 70)
    
    # Build paths
    base_folder = os.path.join(BASE_PATH, folder_name)
    aprx_path = os.path.join(base_folder, "1_SpatialData", "1_InputData", f"{folder_name}.aprx")
    maps_folder = os.path.join(base_folder, "3_Maps")
    
    # Check if aprx exists
    if not os.path.exists(aprx_path):
        print(f"  [ERROR] APRX not found: {aprx_path}")
        return False
    
    print(f"  Opening: {aprx_path}")
    
    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
    except Exception as e:
        print(f"  [ERROR] Could not open APRX: {e}")
        return False
    
    # Get the results map
    rslt_maps = aprx.listMaps('*WHPOR Results Map*')
    if not rslt_maps:
        print(f"  [ERROR] No 'WHPOR Results Map' found in project")
        return False
    
    rslt_map = rslt_maps[0]
    print(f"  Map: {rslt_map.name}")
    
    # Get layers for extent calculation
    named_map_lyrs = rslt_map.listLayers('*Watershed*')
    if not named_map_lyrs:
        print(f"  [ERROR] No watershed layers found")
        return False
    
    print(f"  Found {len(named_map_lyrs)} watershed layers")
    
    # Get layout
    layouts = aprx.listLayouts('WHPOR Results Map')
    if not layouts:
        print(f"  [ERROR] No 'WHPOR Results Map' layout found")
        return False
    
    lyout = layouts[0]
    mfrm = lyout.listElements("MAPFRAME_ELEMENT")[0]
    final_scale = int(mfrm.camera.scale)
    
    # Update title
    title_elements = lyout.listElements('TEXT_ELEMENT', 'Title')
    if title_elements:
        title = title_elements[0]
        title.text = f"{watershed_name}:\nWHPOR Results"
        print(f"  Title updated")
    
    # Zoom to watershed AOI
    try:
        # Find RevRepUni field
        rev_fields = [f.name for f in arcpy.ListFields(named_map_lyrs[0], '*RevRepuni')]
        if rev_fields:
            unq1 = rev_fields[0]
            exprs = f"{unq1} IS NOT NULL"
            arcpy.management.SelectLayerByAttribute(named_map_lyrs[0], 'NEW_SELECTION', exprs)
        
        # Set extent to layer
        mfrm.camera.setExtent(mfrm.getLayerExtent(named_map_lyrs[0]))
        original_scale = int(mfrm.camera.scale)
        
        # Clear selection
        arcpy.management.SelectLayerByAttribute(named_map_lyrs[0], "CLEAR_SELECTION")
        
        print(f"  Original scale: 1:{original_scale:,}")
        
        # Round map scale (same logic as original)
        scale = original_scale
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
        
        # Apply zoom-out factor
        zoomed_scale = int(new_scale * ZOOM_OUT_FACTOR)
        
        # Round the zoomed scale to nice number
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
        
        mfrm.camera.scale = final_scale
        print(f"  Rounded scale: 1:{new_scale:,}")
        print(f"  With {int((ZOOM_OUT_FACTOR-1)*100)}% zoom out: 1:{final_scale:,}")
        
    except Exception as e:
        print(f"  [WARNING] Could not adjust zoom: {e}")
        print(f"  Using existing extent")
    
    # Adjust scale bar position
    try:
        scaleBar = lyout.listElements("MAPSURROUND_ELEMENT", 'Alternating Scale Bar')[0]
        mf = scaleBar.mapFrame

        try:
            mfrm.camera.scale = int(final_scale)
        except Exception:
            pass
        try:
            scale_for_bar = float(mfrm.camera.scale)
        except Exception:
            scale_for_bar = float(final_scale)
        if scale_for_bar <= 0:
            scale_for_bar = float(final_scale)
        print(f"  Scale used for scale bar calculations: {round(scale_for_bar, 3)}")

        max_allowed_width = max(0.8, mf.elementWidth - 0.75)
        target_width = max(0.8, scaleBar.elementWidth)
        scaleBar.elementPositionY = 2.45

        target_total_km = max(0.2, (scale_for_bar * target_width * 0.0254) / 1000.0)
        division_km = max(0.05, target_total_km / 4.0)

        # Adaptive units: switch to meters for small extents to avoid 0,0,0,0,1 km labels.
        use_meters = (target_total_km < 1.0) or (division_km < 0.25)
        if use_meters:
            meter_div_raw = division_km * 1000.0
            meter_div_candidates = [10, 20, 25, 50, 100, 200, 250, 500, 1000]
            unit_label = 'm'
            unit_wkid = 9001
            unit_name = 'Meters'
            unit_to_m = 1.0
            raw_division = meter_div_raw
        else:
            km_div_candidates = [0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10]
            unit_label = 'km'
            unit_wkid = 9036
            unit_name = 'Kilometers'
            unit_to_m = 1000.0
            raw_division = division_km

        division_candidates = meter_div_candidates if use_meters else km_div_candidates
        candidate_choices = []
        for candidate in division_candidates:
            candidate_width = (candidate * 4.0 * unit_to_m) / (scale_for_bar * 0.0254)
            if candidate_width <= (max_allowed_width + 0.001):
                candidate_choices.append((abs(candidate_width - target_width), abs(candidate - raw_division), candidate, candidate_width))

        if len(candidate_choices) > 0:
            candidate_choices.sort(key=lambda x: (x[0], x[1]))
            _, _, division_value, desired_width = candidate_choices[0]
        else:
            division_value = division_candidates[0]
            desired_width = (division_value * 4.0 * unit_to_m) / (scale_for_bar * 0.0254)

        desired_width = max(0.8, min(max_allowed_width, desired_width))

        if use_meters:
            rounding_value = 1
        elif division_value >= 1:
            rounding_value = 1
        elif division_value >= 0.1:
            rounding_value = 0.1
        else:
            rounding_value = 0.01

        try:
            scalebar_cim = scaleBar.getDefinition('V3')
            if hasattr(scalebar_cim, 'fittingStrategy'):
                try:
                    scalebar_cim.fittingStrategy = 'AdjustFrame'
                except Exception:
                    try:
                        scalebar_cim.fittingStrategy = 'AdjustDivision'
                    except Exception:
                        pass
            if hasattr(scalebar_cim, 'divisions'):
                scalebar_cim.divisions = 4
            if hasattr(scalebar_cim, 'division'):
                scalebar_cim.division = division_value
            if hasattr(scalebar_cim, 'subdivisions'):
                scalebar_cim.subdivisions = 0
            if hasattr(scalebar_cim, 'showLabels'):
                scalebar_cim.showLabels = True
            if hasattr(scalebar_cim, 'showDivisionLabels'):
                scalebar_cim.showDivisionLabels = True
            if hasattr(scalebar_cim, 'showUnitLabel'):
                scalebar_cim.showUnitLabel = True
            if hasattr(scalebar_cim, 'unitLabel'):
                scalebar_cim.unitLabel = unit_label
            if hasattr(scalebar_cim, 'unitLabelPosition'):
                try:
                    scalebar_cim.unitLabelPosition = 'AfterBar'
                except Exception:
                    scalebar_cim.unitLabelPosition = 4
            if hasattr(scalebar_cim, 'units'):
                try:
                    scalebar_cim.units = {'uwkid': unit_wkid}
                except Exception:
                    try:
                        scalebar_cim.units = {'wkid': unit_wkid}
                    except Exception:
                        try:
                            scalebar_cim.units = unit_name
                        except Exception:
                            pass
            if hasattr(scalebar_cim, 'numberFormat') and scalebar_cim.numberFormat:
                if hasattr(scalebar_cim.numberFormat, 'roundingValue'):
                    scalebar_cim.numberFormat.roundingValue = rounding_value
            scaleBar.setDefinition(scalebar_cim)
            try:
                applied_cim = scaleBar.getDefinition('V3')
                print(
                    "  Scale bar readback after initial apply:",
                    "fit=", getattr(applied_cim, 'fittingStrategy', 'n/a'),
                    "divisions=", getattr(applied_cim, 'divisions', 'n/a'),
                    "division=", getattr(applied_cim, 'division', 'n/a'),
                    "subdivisions=", getattr(applied_cim, 'subdivisions', 'n/a'),
                    "units=", getattr(applied_cim, 'units', 'n/a')
                )
            except Exception as readback_e:
                print(f"  [WARNING] Scale bar readback after initial apply skipped: {readback_e}")
        except Exception as e:
            print(f"  [WARNING] Could not apply adaptive scale bar CIM settings: {e}")

        scaleBar.elementWidth = desired_width
        scaleBar.elementPositionX = mf.elementWidth - scaleBar.elementWidth - 0.05

        # Re-apply division after final width set so ArcGIS does not auto-adjust to non-candidate values.
        try:
            final_cim = scaleBar.getDefinition('V3')
            if hasattr(final_cim, 'fittingStrategy'):
                try:
                    final_cim.fittingStrategy = 'AdjustFrame'
                except Exception:
                    try:
                        final_cim.fittingStrategy = 'AdjustDivision'
                    except Exception:
                        pass
            if hasattr(final_cim, 'divisions'):
                final_cim.divisions = 4
            if hasattr(final_cim, 'division'):
                final_cim.division = division_value
            if hasattr(final_cim, 'subdivisions'):
                final_cim.subdivisions = 0
            if hasattr(final_cim, 'units'):
                try:
                    final_cim.units = {'uwkid': unit_wkid}
                except Exception:
                    try:
                        final_cim.units = {'wkid': unit_wkid}
                    except Exception:
                        try:
                            final_cim.units = unit_name
                        except Exception:
                            pass
            if hasattr(final_cim, 'unitLabel'):
                final_cim.unitLabel = unit_label
            if hasattr(final_cim, 'numberFormat') and final_cim.numberFormat:
                if hasattr(final_cim.numberFormat, 'roundingValue'):
                    final_cim.numberFormat.roundingValue = rounding_value
            scaleBar.setDefinition(final_cim)
            print(f"  Scale bar final division lock applied: {round(division_value, 3)} {unit_label}")
            try:
                final_readback_cim = scaleBar.getDefinition('V3')
                print(
                    "  Scale bar final readback:",
                    "fit=", getattr(final_readback_cim, 'fittingStrategy', 'n/a'),
                    "divisions=", getattr(final_readback_cim, 'divisions', 'n/a'),
                    "division=", getattr(final_readback_cim, 'division', 'n/a'),
                    "subdivisions=", getattr(final_readback_cim, 'subdivisions', 'n/a'),
                    "units=", getattr(final_readback_cim, 'units', 'n/a')
                )
            except Exception as readback_e:
                print(f"  [WARNING] Scale bar final readback skipped: {readback_e}")
        except Exception as e:
            print(f"  [WARNING] Scale bar final division lock skipped: {e}")

        print(f"  Scale bar adaptive units: {unit_label}, division={round(division_value, 3)}, target_total_km={round(target_total_km, 3)}, width={round(desired_width, 3)}")
        print(f"  Scale bar adjusted")

        try:
            mfrm.camera.scale = int(final_scale)
            print(f"  Map frame scale re-applied before export: {int(mfrm.camera.scale)}")
        except Exception as e:
            print(f"  [WARNING] Map frame scale re-apply skipped: {e}")
    except Exception as e:
        print(f"  [WARNING] Could not adjust scale bar: {e}")
    
    # Generate output filename with today's date
    today = datetime.datetime.today().strftime('%Y%m%d')
    map_filename = f"{watershed_name} WHPOR Results Map {today}.pdf"
    map_path = os.path.join(maps_folder, map_filename)
    
    # Export PDF
    print(f"  Exporting: {map_filename}")
    try:
        lyout.exportToPDF(map_path)
        print(f"  [OK] Map exported successfully")
    except Exception as e:
        print(f"  [ERROR] Export failed: {e}")
        return False
    
    # Save aprx
    try:
        aprx.save()
        print(f"  [OK] Project saved")
    except Exception as e:
        print(f"  [WARNING] Could not save project: {e}")
        # Continue anyway - PDF was exported
    
    return True


def main():
    print("\n" + "=" * 70)
    print("WHPOR Map Regeneration Script")
    print(f"Zoom out factor: {int((ZOOM_OUT_FACTOR-1)*100)}%")
    print("=" * 70)
    print(f"\nBase path: {BASE_PATH}")
    print(f"Watersheds: {len(WATERSHEDS)}")
    print("\nIMPORTANT: Make sure ArcGIS Pro is CLOSED!\n")
    
    arcpy.env.overwriteOutput = True
    
    results = []
    for folder_name, watershed_name in WATERSHEDS:
        success = regenerate_map(folder_name, watershed_name)
        results.append((watershed_name, success))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, success in results:
        status = "[OK]" if success else "[FAILED]"
        print(f"  {status} {name}")
    
    success_count = sum(1 for _, s in results if s)
    print(f"\nCompleted: {success_count}/{len(WATERSHEDS)} maps regenerated")
    print("=" * 70)


if __name__ == "__main__":
    main()
