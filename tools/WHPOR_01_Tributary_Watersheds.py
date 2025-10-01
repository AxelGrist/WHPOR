
import arcpy
import pandas as pd
import os
import arcgis
from getpass import getpass

class Tribs:
    def __init__(self, wtrshdname, wtrshdkey, Bfold, username, password):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold
        self.username=username
        self.password=password
        self.wtrshdkey=wtrshdkey


        # user parameters
        named_watershed = self.wtrshdname
        BaseFolder= self.Bfold
        watershed_key = self.wtrshdkey
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

            #loop throuh intersection points and trace streams
            for x in range(1,max_num):
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




        theFirst(named_watershed)
        theSecond(network_name)
        theThird('trace_lines')