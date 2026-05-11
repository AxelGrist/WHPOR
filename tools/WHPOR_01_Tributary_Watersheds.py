
import arcpy
import pandas as pd
import os
import arcgis
from getpass import getpass

class Tribs:
    def __init__(self, wtrshdname, wtrshdkey, Bfold, username, password, custom_aoi=None):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold
        self.username=username
        self.password=password
        self.wtrshdkey=wtrshdkey
        self.custom_aoi=custom_aoi


        # user parameters
        named_watershed = self.wtrshdname
        BaseFolder= self.Bfold
        watershed_key = self.wtrshdkey
        custom_aoi_path = self.custom_aoi
        NamedWatershed=str(named_watershed.replace(' ','_'))+'.gdb'
        inputdataPath=os.path.join(BaseFolder,r'1_SpatialData\1_InputData') 
        initial_gdb_path = os.path.join(inputdataPath,NamedWatershed)
        
        wrkspc=initial_gdb_path
        outputfolder=inputdataPath
        sdeloc=os.path.join(outputfolder,'bcgw.bcgov.sde')

        # static variables 
        arcpy.env.overwriteOutput = True

        bcgw_username = self.username
        bcgw_password = self.password

        network_name = 'network_' + str(watershed_key)
        watersheds_file = named_watershed.replace(' ', '_') + '_Watersheds'
        tributaries_watershed_file = named_watershed.replace(' ', '_') + '_Tributaries'
        current_workspace = wrkspc

        #create empty feature data set to export layers
        if arcpy.Exists(os.path.join(current_workspace,'network')):
            print('network exists')

        else:
            arcpy.management.CreateFeatureDataset(current_workspace,'network',3005)

        #set new workspace to feature data set
        current_workspace=os.path.join(current_workspace,'network')
        arcpy.env.workspace = current_workspace
        arcpy.env.overwriteOutput = True
        print(current_workspace)


                    
        try:
            arcpy.CreateDatabaseConnection_management(out_folder_path=outputfolder, out_name='bcgw.bcgov.sde',database_platform='ORACLE', instance='bcgw.bcgov/idwprod1.bcgov',
            account_authentication='DATABASE_AUTH', username=bcgw_username, password=bcgw_password, save_user_pass='DO_NOT_SAVE_USERNAME')
            print(' new SDE connection')
        except:
            print('Database connection already exists')

        def add_field_if_missing(in_table, field_name, field_type, field_length=None):
            existing = [f.name.upper() for f in arcpy.ListFields(in_table)]
            if field_name.upper() in existing:
                return
            if field_type.upper() == 'TEXT' and field_length is not None:
                arcpy.management.AddField(in_table=in_table, field_name=field_name, field_type=field_type, field_length=field_length)
            else:
                arcpy.management.AddField(in_table=in_table, field_name=field_name, field_type=field_type)

        def custom_aoi_mode(aoi_fc):
            named_watershed_file = named_watershed.replace(' ', '_') + '_Named_Watershed'
            named_watershed_stream_file = named_watershed.replace(' ', '_') + '_Stream_Network'
            tributary_stream_file = 'Tributary_Stream_Network'
            aoi_streams_file = named_watershed.replace(' ', '_') + '_AOI_Stream_Network'

            if arcpy.Exists(named_watershed_file):
                arcpy.management.Delete(named_watershed_file)

            source_aoi = aoi_fc
            try:
                aoi_sr = arcpy.Describe(aoi_fc).spatialReference
                if aoi_sr and aoi_sr.factoryCode != 3005:
                    projected_aoi = named_watershed.replace(' ', '_') + '_AOI_3005'
                    if arcpy.Exists(projected_aoi):
                        arcpy.management.Delete(projected_aoi)
                    arcpy.management.Project(aoi_fc, projected_aoi, arcpy.SpatialReference(3005))
                    source_aoi = projected_aoi
                    print('Custom AOI projected to BC Albers (EPSG:3005)')
            except Exception as e:
                print('Custom AOI projection check skipped:', e)

            named_source_layer = os.path.join(sdeloc, 'WHSE_BASEMAPPING.FWA_NAMED_WATERSHEDS_POLY')
            named_sel = arcpy.management.SelectLayerByLocation(
                in_layer=named_source_layer,
                overlap_type='INTERSECT',
                select_features=source_aoi
            )
            named_count = int(arcpy.management.GetCount(named_sel)[0])

            if named_count > 0:
                named_sel_file = named_watershed_file + '_SEL'
                if arcpy.Exists(named_sel_file):
                    arcpy.management.Delete(named_sel_file)
                arcpy.conversion.FeatureClassToFeatureClass(
                    in_features=named_sel,
                    out_path=current_workspace,
                    out_name=named_sel_file
                )
                arcpy.analysis.Clip(named_sel_file, source_aoi, named_watershed_file)
                arcpy.management.Delete(named_sel_file)
                print('Custom AOI named watersheds selected and clipped:', named_count)
            else:
                arcpy.management.Dissolve(in_features=source_aoi, out_feature_class=named_watershed_file, multi_part='SINGLE_PART')
                print('No intersecting named watersheds found. Using dissolved AOI boundary fallback.')

            add_field_if_missing(named_watershed_file, 'GNIS_NAME', 'TEXT', 120)
            add_field_if_missing(named_watershed_file, 'FWA_WATERSHED_CODE', 'TEXT', 50)
            add_field_if_missing(named_watershed_file, 'Stream_Order', 'LONG')

            with arcpy.da.UpdateCursor(named_watershed_file, ['GNIS_NAME', 'FWA_WATERSHED_CODE', 'Stream_Order']) as cursor:
                for row in cursor:
                    if row[0] in [None, '']:
                        row[0] = named_watershed
                    if row[1] in [None, '']:
                        row[1] = 'CUSTOM_AOI'
                    if row[2] in [None, '']:
                        row[2] = 0
                    cursor.updateRow(row)
            print('Custom AOI named watershed fields prepared for downstream modules')

            # Build true tributary polygons for custom AOI using stream tracing workflow.
            for nm in [aoi_streams_file, named_watershed_stream_file, tributary_stream_file,
                       'del_intersection_points', 'intersection_points', watersheds_file,
                       tributaries_watershed_file, 'trace_lines']:
                if arcpy.Exists(nm):
                    arcpy.management.Delete(nm)

            stream_layer = os.path.join(sdeloc, 'WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP')
            stream_sel = arcpy.management.SelectLayerByLocation(
                in_layer=stream_layer,
                overlap_type='INTERSECT',
                select_features=named_watershed_file
            )
            arcpy.conversion.FeatureClassToFeatureClass(
                in_features=stream_sel,
                out_path=current_workspace,
                out_name=aoi_streams_file
            )

            stream_count = int(arcpy.management.GetCount(aoi_streams_file)[0])
            if stream_count == 0:
                raise RuntimeError('No streams found intersecting custom AOI. Cannot build tributary trace products.')

            order_field = None
            for fld in arcpy.ListFields(aoi_streams_file):
                upper_name = fld.name.upper()
                if upper_name == 'STREAM_ORDER' or ('STREAM' in upper_name and 'ORDER' in upper_name):
                    order_field = fld.name
                    break

            max_order = None
            if order_field:
                with arcpy.da.SearchCursor(aoi_streams_file, [order_field]) as cursor:
                    order_values = [row[0] for row in cursor if row[0] is not None]
                if len(order_values) > 0:
                    max_order = max(order_values)

            if order_field and max_order is not None:
                fld_delim = arcpy.AddFieldDelimiters(current_workspace, order_field)
                if isinstance(max_order, str):
                    main_query = f"{fld_delim} = '{max_order}'"
                else:
                    main_query = f"{fld_delim} = {max_order}"

                arcpy.conversion.FeatureClassToFeatureClass(
                    in_features=aoi_streams_file,
                    out_path=current_workspace,
                    out_name=named_watershed_stream_file,
                    where_clause=main_query
                )
                print('Custom AOI mainstem selected from highest stream order:', max_order)
            else:
                oid_field = arcpy.Describe(aoi_streams_file).OIDFieldName
                longest_oid = None
                longest_len = -1
                with arcpy.da.SearchCursor(aoi_streams_file, [oid_field, 'SHAPE@LENGTH']) as cursor:
                    for row in cursor:
                        if row[1] is not None and row[1] > longest_len:
                            longest_len = row[1]
                            longest_oid = row[0]

                if longest_oid is not None:
                    oid_delim = arcpy.AddFieldDelimiters(current_workspace, oid_field)
                    main_query = f"{oid_delim} = {longest_oid}"
                    arcpy.conversion.FeatureClassToFeatureClass(
                        in_features=aoi_streams_file,
                        out_path=current_workspace,
                        out_name=named_watershed_stream_file,
                        where_clause=main_query
                    )
                    print('STREAM_ORDER not found. Using longest stream segment as mainstem proxy.')
                else:
                    arcpy.management.CopyFeatures(aoi_streams_file, named_watershed_stream_file)
                    print('STREAM_ORDER not found and no stream lengths available. Using all AOI streams as named stream network.')

            main_count = int(arcpy.management.GetCount(named_watershed_stream_file)[0])
            if main_count == 0:
                raise RuntimeError('No mainstem streams identified in custom AOI. Cannot build tributary trace products.')

            arcpy.analysis.Erase(
                in_features=aoi_streams_file,
                erase_features=named_watershed_stream_file,
                out_feature_class=tributary_stream_file
            )
            trib_stream_count = int(arcpy.management.GetCount(tributary_stream_file)[0])
            if trib_stream_count == 0:
                print('No tributary streams remain after removing mainstem streams in custom AOI')

            if trib_stream_count > 0:
                arcpy.analysis.Intersect(
                    in_features=[named_watershed_stream_file, tributary_stream_file],
                    out_feature_class='del_intersection_points',
                    join_attributes='ONLY_FID',
                    output_type='POINT'
                )
                arcpy.management.Dissolve(
                    in_features='del_intersection_points',
                    out_feature_class='intersection_points',
                    multi_part='SINGLE_PART'
                )
            else:
                arcpy.management.CreateFeatureclass(current_workspace, 'intersection_points', 'POINT', spatial_reference=arcpy.Describe(named_watershed_file).spatialReference)

            layerpath = os.path.join(sdeloc, 'WHSE_BASEMAPPING.FWA_WATERSHEDS_POLY')
            watersheds_sel = arcpy.management.SelectLayerByLocation(
                in_layer=layerpath,
                overlap_type='INTERSECT',
                select_features=named_watershed_file
            )
            arcpy.conversion.FeatureClassToFeatureClass(
                in_features=watersheds_sel,
                out_path=current_workspace,
                out_name=watersheds_file
            )

            print('Custom AOI stream/watershed inputs created for tributary tracing')

            if arcpy.Exists(network_name):
                arcpy.management.Delete(network_name)
            arcpy.tn.CreateTraceNetwork(
                in_feature_dataset=current_workspace,
                in_trace_network_name=network_name,
                input_edges=[[tributary_stream_file, 'SIMPLE_EDGE']]
            )
            print('Custom AOI trace network created')


        def theFirst(wtrshdnam):
            #create watershed layer
            # Query for watershed and stream features
            named_watershed_sql =  f"WATERSHED_KEY ={watershed_key}"    #"GNIS_NAME = " + "'" + wtrshdnam + "'" OLD LOGIC PULLS ALL WATERSEHDS NAMED THE SAME... NO GOOD 

            # 'Bowron River' becomes 'Bowron_River_Named_Watershed'
        
            named_watershed_file = named_watershed.replace(' ', '_') + '_Named_Watershed'
            layerpath=os.path.join(sdeloc,'WHSE_BASEMAPPING.FWA_NAMED_WATERSHEDS_POLY')
            arcpy.conversion.FeatureClassToFeatureClass(in_features = layerpath, out_path=current_workspace, out_name = named_watershed_file, where_clause= named_watershed_sql)
            print('Watershed layer created')

            # Create Named Watershed Stream Layer

            # 'Bowron River' becomes 'Bowron_River_Stream_Network'
            named_watershed_stream_file_del=named_watershed.replace(' ', '_') + '_Stream_Network_DEL'
            named_watershed_stream_file = named_watershed.replace(' ', '_') + '_Stream_Network'
            named_watershed_stream_sql = 'WATERSHED_KEY = ' + str(watershed_key)
            layerpath=os.path.join(sdeloc,'WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP')

            arcpy.conversion.FeatureClassToFeatureClass(in_features=layerpath, out_path=current_workspace, out_name = named_watershed_stream_file, where_clause= named_watershed_stream_sql)

            print('Streams layer created')

            # Create Non-Named Watershed Stream Layer
            tributary_stream_sql =  'WATERSHED_KEY <> ' + str(watershed_key)
            tributary_stream_file = 'Tributary_Stream_Network'
            aoi_layer = named_watershed.replace(' ', '_') + '_Named_Watershed'
            layerpath=os.path.join(sdeloc,'WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP')
            sel=arcpy.management.SelectLayerByLocation(in_layer = layerpath, overlap_type = 'COMPLETELY_WITHIN', select_features=aoi_layer)
            print('stream features selected by watershed, completely within')
            arcpy.conversion.FeatureClassToFeatureClass(in_features=sel, out_path=current_workspace, out_name = tributary_stream_file, where_clause=tributary_stream_sql)
            print('non-named streams created')


            # Create intersection points
            arcpy.analysis.Intersect(in_features = [named_watershed_stream_file, tributary_stream_file], out_feature_class = 'del_intersection_points',
                                    join_attributes = 'ONLY_FID',output_type = 'POINT')

            arcpy.management.Dissolve(in_features = 'del_intersection_points', out_feature_class = 'intersection_points', multi_part = 'SINGLE_PART')

            # Create Watersheds Layer

            aoi_layer = named_watershed.replace(' ', '_') + '_Named_Watershed'
            layerpath=os.path.join(sdeloc,'WHSE_BASEMAPPING.FWA_WATERSHEDS_POLY')

            sel=arcpy.management.SelectLayerByLocation(in_layer = layerpath, overlap_type = 'INTERSECT', select_features=aoi_layer)
            print('select features by aoi layer')
            arcpy.conversion.FeatureClassToFeatureClass(in_features=sel,out_path=current_workspace, out_name = watersheds_file)
            print('create watersheds')


            #create trace network
            print('start create Trace Network')
            arcpy.tn.CreateTraceNetwork(in_feature_dataset=current_workspace, in_trace_network_name=network_name,input_edges=[['Tributary_Stream_Network', 'SIMPLE_EDGE']])
            print('trace network created')

        def theSecond(ntwrknm):
            arcpy.tn.DisableNetworkTopology(ntwrknm)
            arcpy.env.overwriteOutput = True
            #enable trace network 
            enabletr=arcpy.tn.EnableNetworkTopology(in_trace_network= ntwrknm)
            print('network enabled')

            count = int(arcpy.GetCount_management('intersection_points')[0])
            max_num=count
            print(max_num)

            if count <= 0:
                print('No intersection points available for tracing. Creating empty trace_lines.')
                if arcpy.Exists('trace_lines'):
                    arcpy.management.Delete('trace_lines')
                arcpy.management.CreateFeatureclass(current_workspace, 'trace_lines', 'POLYLINE', spatial_reference=arcpy.Describe('Tributary_Stream_Network').spatialReference)
                return

            trace_ids = []
            with arcpy.da.SearchCursor('intersection_points', ['OBJECTID']) as cursor:
                for row in cursor:
                    trace_ids.append(row[0])

            #loop throuh intersection points and trace streams
            for x in trace_ids:
                trcout=('Trace_Results'+str(x))
                sql = 'OBJECTID = ' + str(x)
                try:
                    arcpy.conversion.ExportFeatures(in_features = 'intersection_points', out_features='trace_point', where_clause=sql)
                    print('trace points')
                    trace = arcpy.tn.Trace(in_trace_network=enabletr, starting_points='trace_point',barriers = '',
                                                        include_barriers="EXCLUDE_BARRIERS", validate_consistency="DO_NOT_VALIDATE_CONSISTENCY", 
                                                        result_types="AGGREGATED_GEOMETRY", aggregated_lines = trcout)
                except:
                    print('exception occured, unable to use file "trace_points, renaming" ')
                    new_out='trace_point'+str(x)
                    arcpy.conversion.ExportFeatures(in_features = 'intersection_points', out_features=new_out, where_clause=sql)
                    print('trace points')
                    trace = arcpy.tn.Trace(in_trace_network=enabletr, starting_points=new_out,barriers = '',
                                                        include_barriers="EXCLUDE_BARRIERS", validate_consistency="DO_NOT_VALIDATE_CONSISTENCY", 
                                                        result_types="AGGREGATED_GEOMETRY", aggregated_lines = trcout)

                print(int(arcpy.GetCount_management(trcout)[0]))
                print('point '+str(x)+' traced!')
                
            rs=arcpy.ListFeatureClasses('Trace_Results*')
            for r in rs:
                print(r)
            if 'Trace_Results_Aggregated_Points' in rs:
                rs.remove('Trace_Results_Aggregated_Points')
            if len(rs) == 0:
                print('No trace results generated. Creating empty trace_lines.')
                if arcpy.Exists('trace_lines'):
                    arcpy.management.Delete('trace_lines')
                arcpy.management.CreateFeatureclass(current_workspace, 'trace_lines', 'POLYLINE', spatial_reference=arcpy.Describe('Tributary_Stream_Network').spatialReference)
                return
            #merge all trace lines
            arcpy.management.Merge(rs,'trace_lines')
            print('Merged')

        def theThird(TL):


            print('======== Trib Count ========')
            print(int(arcpy.GetCount_management(TL)[0]))

            TL_out='trace_lines_out'
            #saptial join attributes from stream network, watershed key is needed for the trib
            arcpy.analysis.SpatialJoin(TL, 'Tributary_Stream_Network',TL_out)


            arcpy.management.AddField(TL_out, 'Tributary', 'DOUBLE')
            WK=arcpy.ListFields(TL_out, '*WATERSHED_KEY*')[0]
            print(WK.name)
            arcpy.management.CalculateField(TL_out, 'Tributary','!WATERSHED_KEY!', 'PYTHON3' )
            
        
            print('tributary calculated')
            
            arcpy.analysis.SpatialJoin(watersheds_file,TL_out,'watersheds_trib' )
            print('spatial join tribs')

            nmd_str=named_watershed.replace(' ', '_')+'_Stream_Network'

            sel=arcpy.management.SelectLayerByLocation(in_layer= 'watersheds_trib', overlap_type='CONTAINS', select_features=nmd_str)
            print('Selected Feature Counts======================')
            print(int(arcpy.management.GetCount(sel)[0]))
            
            triff=arcpy.ListFields('watersheds_trib','*Tributary*')[0]
            print(triff)
            #give all watersheds that contain the named stream the trib id of 1
            arcpy.management.CalculateField(in_table=sel,field='Tributary',expression=1,expression_type='PYTHON3')

            arcpy.management.SelectLayerByAttribute('watersheds_trib','CLEAR_SELECTION')
            
            # ========================================================================================
            

            arcpy.management.Dissolve(in_features = 'watersheds_trib' , out_feature_class = tributaries_watershed_file, dissolve_field = 'Tributary')
            
            print('print dissolved, tribs or whatever')
            
            Sel_c=arcpy.management.SelectLayerByAttribute(tributaries_watershed_file,'NEW_SELECTION','"Tributary" IS NULL Or "Tributary" = 1 Or "Shape_Area" < 10000000  ')
            Sel_count = int (arcpy.GetCount_management (Sel_c).getOutput (0))
            arcpy.management.SelectLayerByAttribute(tributaries_watershed_file,'CLEAR_SELECTION')
            F_count = int (arcpy.GetCount_management (tributaries_watershed_file)[0])
            print(Sel_count)
            print(F_count)
            if Sel_count == F_count:
                arcpy.management.Delete(tributaries_watershed_file)
                print('No Tribs greater than 1000 ha and or that meet the criteria')
            else:
                print(str(F_count-Sel_count)+' Tribs Remain')

                with arcpy.da.UpdateCursor(tributaries_watershed_file, ['Tributary', 'Shape_Area']) as cursor:
                    for row in cursor:
                        if row[0] is None:
                            cursor.deleteRow()
                        elif row[0] == 1:
                            cursor.deleteRow()
                        if row[1] < 10000000:
                            cursor.deleteRow()
                print('Tribs removed that do not meet the requirements')
                    
            print(' THE END ')

        if custom_aoi_path:
            if arcpy.Exists(custom_aoi_path):
                print('Custom AOI mode enabled:', custom_aoi_path)
                custom_aoi_mode(custom_aoi_path)
                theSecond(network_name)
                theThird('trace_lines')
            else:
                raise ValueError(f'Custom AOI path does not exist: {custom_aoi_path}')
        else:
            theFirst(named_watershed)
            theSecond(network_name)
            theThird('trace_lines')