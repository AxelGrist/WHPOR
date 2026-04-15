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
        xpos = mf.elementWidth - scaleBar.elementWidth - 0.05
        scaleBar.elementPositionX = xpos
        scaleBar.elementPositionY = 2.45
        print(f"  Scale bar adjusted")
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
