'''union1
Script to prep and calculate ECA Score
C.folkers
2023/04/17
'''


import arcpy
import os
import datetime
import sys
from getpass import getpass

class ECA:
    def __init__(self, wtrshdname, Bfold, username, password):
        self.wtrshdname=wtrshdname
        self.Bfold=Bfold
        self.username=username
        self.password=password

        arcpy.env.overwriteOutput = True

        #user Variables
        WatershedName= wtrshdname
        BaseFolder=Bfold

        namedwatershed=WatershedName.replace(' ','_')
        inputgdb=namedwatershed+'_Input_Data.gdb'
        today = datetime.date.today()
        year = today.year
        wrkspc=os.path.join (BaseFolder,'1_SpatialData','1_InputData',inputgdb)  #select input gdb
        output=os.path.join(BaseFolder,'1_SpatialData','1_InputData') 
        dlvr_fldr=os.path.join(BaseFolder,'1_SpatialData','1_InputData') 
        vri_str=('VRI2_AOI_'+str(year)+'.gdb')
        VRI2gdb=os.path.join(BaseFolder,'1_SpatialData','3_VRI_Update','data',vri_str)
       

        #static variables
        #variables in first function union_fc
        bcgw_username = username
        bcgw_password = password
        sdeloc=output+r'\\bcgw.bcgov.sde'
        unilist=[]
        union1=['IR_CLAB','BCCEF_Integrated_Roads_2021_Buffers','BC_CEF_Human_Disturb_BTM_2023','PMBC_PF_O']
        uni='Roads_HD_IR_PE_CR_Temp'
        uni1='HD_RD_IR_PR_CR'


        unilist2=[]
        union2=['BEC','H_FIRE_PLY','C_FIRE_PLY']
        uni2='VRI_BEC_FIRE'


        fields100=['BCCEF_Integrated_Roads_2021TEMPCLIP_INTEGRATED_ROADS_ID','CEF_DISTURB_GROUP','Flag']            
        qry100="BCCEF_Integrated_Roads_2021TEMPCLIP_INTEGRATED_ROADS_ID <> 0 OR CEF_DISTURB_GROUP <> ''"                        
        fields75= ['PID','CLAB_ID','Flag']
        qry75="PID <> '' OR CLAB_ID <> '' "

        eca='ECA'

        arcpy.env.overwriteOutput = True

        def bd_gbd (outputfolder):
            try:
                arcpy.CreateDatabaseConnection_management(out_folder_path=outputfolder, out_name='bcgw.bcgov.sde',database_platform='ORACLE', instance='bcgw.bcgov/idwprod1.bcgov',
                account_authentication='DATABASE_AUTH', username=bcgw_username, password=bcgw_password, save_user_pass='DO_NOT_SAVE_USERNAME')
                print(' new SDE connection')
            except:
                print('Database connection already exists')
            


        #|-----Function to union 'IR_CLAB','BCCEF_Integrated_Roads_2021_Buffers','BCCEF_Human_Disturbance_2021','PMBC_PF_O' and flag them for ECA factor  -----|
        def union_1 (wrk):
            arcpy.env.workspace = wrk
            #identify gdb and featureclasses
            # inputgdb = arcpy.ListWorkspaces('*Input*', 'FileGDB')[0]
            # arcpy.env.workspace= inputgdb
            print(wrk)
            fcs=arcpy.ListFeatureClasses()
            # print(union1)
            # print(fcs)
            #find layers for union
            for x in union1:
                if x in fcs:
                    unilist.append(x)
            print('Feature classes to union',unilist)
            out=(wrk+'/'+uni)
            arcpy.analysis.Union(in_features= unilist,out_feature_class= out)
            arcpy.management.AddField(uni,'Flag','TEXT')
            if int(arcpy.management.GetCount('PMBC_PF_O')[0]) <=0:
                arcpy.management.AddField(uni, 'PID', 'TEXT')
            

        #|-----Function to flag polygons-----|
        def flag100_75(uni_input):
            #look for fields that do not exist and create them and leave blank 
            lsftflds=arcpy.ListFields(uni_input)
            if 'CLAB_ID' not in lsftflds:
                arcpy.management.AddField(uni_input,'CLAB_ID','TEXT')
            else:
                print('CLAB ID exists ')


            with arcpy.da.UpdateCursor(uni_input, fields100, qry100) as cursor:
                for row in cursor:
                    row[2]='Human Disturbance'
                    cursor.updateRow(row)
            
            print('Human Disturbance')

            
            with arcpy.da.UpdateCursor(uni_input, fields75, qry75) as cursor:
                for row in cursor:
                    row[2]='Private, Crown Agency, & IR'
                    cursor.updateRow(row)
            
            print('Private, Crown Agency, & IR')
            arcpy.management.Dissolve(in_features=uni,out_feature_class=uni1,dissolve_field='Flag')
            print('Dissolve roads,HD, IR, PE, CR')


        # |-----find VRI2 FCs-----|
        def CopyMoveVRI2 (vri,wrk):
            arcpy.env.workspace=vri
            vri2= arcpy.ListFeatureClasses('VRI2*',)
            print(vri2)
            for x in vri2:
                outclass= wrk+'/'+x 
                arcpy.management.CopyFeatures(x,outclass)
                print(x + ' has been copied to Input GDB')
            
        def union_2_erase (wrk):
            arcpy.env.workspace=wrk
            #find VRI 2 layers
            vri2= arcpy.ListFeatureClasses('*resultant*')
            union2.append(vri2[0])
            print(union2)
            all_fc=arcpy.ListFeatureClasses()
            #find all matching FCs to union
            for x in union2:
                if x in all_fc:
                    unilist2.append(x)
            # print('Feature classes to union',unilist2)
            out1=(wrk+'/'+uni2)
            arcpy.analysis.Union(in_features=unilist2,out_feature_class=out1)
            print(unilist2,' Union')

            out2=(wrk+'/'+'VRI_Erase')
            arcpy.analysis.Erase(out1, uni1,out2)
            print('Erase union 1 from union 2')

            out3=(wrk+'/'+ eca)
            mergefc=[out2,uni1]
            arcpy.management.Merge(mergefc, out3)
            print('Data sets merged')
            
            # arcpy.management.Delete(uni)
            # arcpy.management.Delete(uni1)
            # arcpy.management.Delete(uni2)
        #|----- assign ECA type and factor -----|
        def ECA_Type_Factor_ROW_IR_Priv(wrk):
            arcpy.env.workspace=wrk
                #create fields for ECA Rank,Factor and Score
                #write if theese cols exist then nothing else create them
            eca=wrk+r'\ECA'
            arcpy.management.AddField(eca, 'ECA_Type', 'TEXT')
            arcpy.management.AddField(eca, 'ECA_Factor', 'DOUBLE')
            arcpy.management.AddField(eca, 'ECA_Score', 'DOUBLE')
            arcpy.management.AddField(eca, 'ECA_Rank', 'TEXT')
            uniqueList1=[]
            with arcpy.da.UpdateCursor(eca, ROW_IR_Fields) as cursor:
                for row in cursor:
                    uniqueList1.append(row[2])
                    if row[2]== 'Human Disturbance ' or row[2]== 'Human Disturbance' :
                        row[0]='Human Disturbance'
                        row[1]=100
                    elif row[2] == "Private, Crown Agency, & IR":
                        row[0]= 'Private, Crown Agency, & IR'
                        row[1]= 75
                    else:
                        continue
                    cursor.updateRow(row)
                    set_list= set(uniqueList1)
                    print(set_list)

        def ECA_Type_Factor_Non_Natural (wrk):
            arcpy.env.workspace=wrk
            eca=wrk+r'\ECA'

            uniqueList1=[]
            unqiueList2=[]
            
            with arcpy.da.UpdateCursor(eca, NNfields) as cursor:
                for row in cursor:
                    uniqueList1.append(row[2])
                    unqiueList2.append(row[3])
                    if row[2] in ['GP', 'MI', 'RZ', 'TZ', 'UR'] or row[3] in ['C', 'GR','U'] and row[1] is None:
                        row[0]='Non Natural '
                        row[1]=100
                    else:
                        continue
                    cursor.updateRow(row)
                set_list= set(uniqueList1)
                set_list2=set(unqiueList2)
                print(set_list)
                print(set_list2)

                print('Done')


        def ECA_Type_Factor_PLogged (wrk):
            arcpy.env.workspace=wrk
            eca=wrk+r'\ECA'
            uniqueList1=[]
            unqiueList2=[]

            with arcpy.da.UpdateCursor(eca, PloggedFields) as cursor:
                for row in cursor:
                    uniqueList1.append(row[1])
                    unqiueList2.append(row[2])
                    if row[1] is None and row[2] == 'Presumed Logged':
                        row[0]='Presumed Logged'
                        row[1]=100
                    else:
                        continue
                    cursor.updateRow(row)
                set_list= set(uniqueList1)
                set_list2=set(unqiueList2)
                print(set_list)
                print(set_list2)

        def ECA_Type_Factor_Fire (wrk):
            arcpy.env.workspace=wrk
            if arcpy.Exists('C_FIRE_PLY') or arcpy.Exists('H_FIRE_PLY'):
                eca=wrk+r'\ECA'
                uniqueList1=[]
                today = datetime.date.today()
                year = today.year

                #addtion to compensate for if there is no fire year but somehow a fire exists.... 20230929
                fy_field=arcpy.ListFields(eca)
                x=False
                y=False
                for f in fy_field:
                    if f.name =='FIRE_YEAR':
                        print('fire year field exists')
                        x=True
                    elif f.name =='FIRE_YEAR_1':
                        print('fire year 1 field exists')
                        y=True
                

                # if x == False:
                #     arcpy.management.AddField(eca,'FIRE_YEAR', 'DOUBLE')
                #     fire_yr='FIRE_YEAR'
                if x == False:
                    arcpy.management.AddField(eca,'FIRE_YEAR', 'DOUBLE')
                if y == False:
                    arcpy.management.AddField(eca,'FIRE_YEAR_1', 'DOUBLE')
                
                # FireFields=['ECA_Type', 'ECA_Factor', 'FIRE_YEAR', 'VRI2_DISTURB_YR','VRI2_DISTURB_CODE',fire_yr ]
                FireFields=['ECA_Type', 'ECA_Factor', 'FIRE_YEAR', 'VRI2_DISTURB_YR','VRI2_DISTURB_CODE','FIRE_YEAR_1' ]
                with arcpy.da.UpdateCursor(eca, FireFields) as cursor:
                    # for row in cursor:
                    #     uniqueList1.append(row[4])
                    #     if row[0] is Not None:
                    #         if row[2] is None:
                    #             row[2]=0
                    #         if row[0] is None and row[3] is not None and (row[2]>=row[3]) and row[2]>0:
                    #             row[0]='Fire'
                    #             row[1]=80
                    #         # elif row[0] is None and (row[2] is not None and row[3] is None):  #investigate this
                    #         #     row[0]='Fire'
                    #         #     row[1]=80
                    #         elif row[0] is None and row[2]>0  and row[4] not in ['L','Presumed Logged', 'Logged']:
                    #             row[0]='Fire'
                    #             row[1]=80
                    #         elif row[0] is None and row[4] in ['B%'] and row[3]>(year-25):
                    #             row[0]='Fire'
                    #             row[1]=80
                    #         cursor.updateRow(row)
                    #FireFields=['ECA_Type', 'ECA_Factor', 'FIRE_YEAR', 'VRI2_DISTURB_YR','VRI2_DISTURB_CODE','FIRE_YEAR_1' ]
                    for row in cursor:
                        uniqueList1.append(row[4])
                        if row[2] is None:
                            row[2]=0

                        if row[5] is None:
                            row[5]=0

                        if row[0] is None and row[3] is not None and (row[2]>=row[3]) and row[2]>0:
                            row[0]='Fire'
                            row[1]=80
                        elif row[0] is None and (row[2] > 0 and row[3] is None):  #investigate this
                            row[0]='Fire'
                            row[1]=80
                        elif row[0] is None and row[2]>0  and row[4] not in ['L','Presumed Logged', 'Logged']:
                            row[0]='Fire'
                            row[1]=80
                        if row[0] is None and row[3] is not None and (row[5]>=row[3]) and row[5]>0:
                            row[0]='Fire'
                            row[1]=80
                        elif row[0] is None and (row[5] > 0 and row[3] is None):  #investigate this
                            row[0]='Fire'
                            row[1]=80
                        elif row[0] is None and row[5]>0  and row[4] not in ['L','Presumed Logged', 'Logged']:
                            row[0]='Fire'
                            row[1]=80
                        elif row[0] is None and row[4] in ['B%'] and row[3]>(year-25):
                            row[0]='Fire'
                            row[1]=80

                        cursor.updateRow(row)
                    set_list= set(uniqueList1)
                    print(set_list)
            else:
                print('No Fires Perimeters')


        def MPBFactor(wrk):
            arcpy.env.workspace=wrk
            eca=wrk+r'\ECA'
            
            #calculate dead class
            expression='getDeadCls(!STAND_PERCENTAGE_DEAD!)'
            codeblock="""def getDeadCls(pcDead):
                if pcDead > 0 and pcDead <= 30:
                    return 1
                if pcDead > 30 and pcDead <= 50:
                    return 2
                if pcDead > 50 and pcDead <= 70:
                    return 3
                if pcDead > 70:
                    return 4
                else:
                    return 0"""
            arcpy.management.AddField(eca,'MPB_dead_cls', 'DOUBLE' )
            arcpy.management.CalculateField(eca, 'MPB_dead_cls', expression, "PYTHON3", codeblock)
            print('Dead Class')

            #calculate MPB year class
            expression='getYrsCls(!EARLIEST_NONLOGGING_DIST_DATE!)'
            codeblock="""def getYrsCls(dist_y):
            import datetime 
            dist=str(dist_y)
            dist.split('-')
            dist_y=int(dist[0])
            today = datetime.date.today()
            year = today.year
            ysa = year- dist_y
            if ysa > 0 and ysa <= 5:
                return 5
            if ysa > 5 and ysa <= 10:
                return 10
            if ysa > 10 and ysa <= 15:
                return 15
            if ysa > 15 and ysa <= 20:
                return 20
            if ysa > 20 and ysa <= 25:
                return 25
            if ysa > 25 and ysa <= 30:
                return 30
            if ysa > 30 and ysa <= 35:
                return 35
            if ysa > 35 and ysa <= 40:
                return 40
            if ysa > 40 and ysa <= 45:
                return 45
            if ysa > 45 and ysa <= 50:
                return 50
            if ysa > 50 and ysa <= 55:
                return 55
            if ysa > 55 and ysa <= 60:
                return 60
            if ysa > 60:
                return 100
            else:
                return 0"""
            arcpy.management.AddField(eca,'MPB_years_cls', 'DOUBLE' )
            arcpy.management.CalculateField(eca, 'MPB_years_cls', expression, "PYTHON3", codeblock)
            print('MPB year')

            #calculate MPB Factor
            expression='getMPBfactor(!BEC_MOIST_CLS!, !MPB_dead_cls!, !MPB_years_cls!)'
            codeblock= """def getMPBfactor(BECm, Dcls, Ycls):
                # print BECm,Dcls,Ycls
                if BECm == 'dry_bec':
                    if Dcls == 0:
                        return 0
                    if Dcls == 1:
                        return 0
                    else:
                        if Dcls == 2:
                            Dry_Dict = {5: 5, 10: 10, 15: 20, 20: 30, 25: 30, 30: 25, 35: 20, 40: 15, 45: 10, 50: 5, 55: 5, 60: 0,
                                        100: 0}
                        if Dcls == 3:
                            Dry_Dict = {5: 10, 10: 30, 15: 40, 20: 50, 25: 50, 30: 40, 35: 30, 40: 20, 45: 15, 50: 10, 55: 5, 60: 5,
                                        100: 0}
                        if Dcls == 4:
                            Dry_Dict = {5: 15, 10: 50, 15: 60, 20: 70, 25: 70, 30: 60, 35: 50, 40: 40, 45: 30, 50: 20, 55: 15,
                                        60: 10, 100: 0}

                        retVal = None
                        if Ycls in Dry_Dict:
                            retVal = Dry_Dict[Ycls]
                        return retVal

                if BECm == 'wet_bec' or 'moist_bec' :
                    if Dcls == 0:
                        return 0
                    if Dcls == 1:
                        return 0
                    else:
                        if Dcls == 2:
                            Wet_Dict = {5: 5, 10: 10, 15: 15, 20: 20, 25: 20, 30: 15, 35: 10, 40: 5, 45: 0, 50: 0, 55: 0, 60: 0,
                                        100: 0}
                        if Dcls == 3:
                            Wet_Dict = {5: 5, 10: 15, 15: 20, 20: 30, 25: 30, 30: 20, 35: 15, 40: 10, 45: 10, 50: 5, 55: 0, 60: 0,
                                        100: 0}
                        if Dcls == 4:
                            Wet_Dict = {5: 10, 10: 30, 15: 40, 20: 45, 25: 45, 30: 40, 35: 30, 40: 25, 45: 20, 50: 10, 55: 5, 60: 0,
                                        100: 0}

                        retVal = None
                        if Ycls in Wet_Dict:
                            retVal = Wet_Dict[Ycls]
                        return retVal
            """
            arcpy.management.AddField(eca,'MPB_Factor', 'DOUBLE' )
            arcpy.management.CalculateField(eca, 'MPB_Factor', expression, "PYTHON3", codeblock)
            #update MPB factor where harvest only, mpb factor 0 
            with arcpy.da.UpdateCursor(eca,['MPB_Factor', 'VRI2_HARVESTED']) as cursor:
                for row in cursor:
                    if row[1] =='YES':
                        row[0]=0
                    cursor.updateRow(row)
            
            print('MPB Factor')

        #calculate height factor
        def HeightFactor (wrk):
            arcpy.env.workspace=wrk
            eca=wrk+r'\ECA'
            expression='eca_func(!VRI2_HEIGHT!)'

            codeblock= """def eca_func(height_value):
                if height_value >= 19:
                    return 0.0
                elif height_value >= 18:
                    return 5.4
                elif height_value >= 17:
                    return 6.9
                elif height_value >= 16:
                    return 8.7
                elif height_value >= 15:
                    return 11.0
                elif height_value >= 14:
                    return 13.8
                elif height_value >= 13:
                    return 17.3
                elif height_value >= 12:
                    return 21.7
                elif height_value >= 11:
                    return 26.9
                elif height_value >= 10:
                    return 33.3
                elif height_value >= 9:
                    return 40.9
                elif height_value >= 8:
                    return 49.7
                elif height_value >= 7:
                    return 59.5
                elif height_value >= 6:
                    return 70.1
                elif height_value >= 5:
                    return 80.7
                elif height_value >= 4:
                    return 90.1
                elif height_value >= 3:
                    return 96.9
                elif height_value >= 2:
                    return 99.8
                elif height_value >= 0:
                    return 100.0
            """
            arcpy.management.AddField(eca,'Height_Factor', 'DOUBLE' )
            arcpy.management.CalculateField(eca, 'Height_Factor', expression, "PYTHON3", codeblock)
            
            #update height factor where IBM only, height factor 0
            with arcpy.da.UpdateCursor(eca,['VRI2_DISTURB_CODE', 'Height_Factor']) as cursor:
                for row in cursor:
                    if row[0]=='IBM' or row[0]=='I':
                        row[1]=0
                    cursor.updateRow(row)
            print('Height Factor')    

        def ECA_Type_Harvest (wrk):
            arcpy.env.workspace=wrk
            eca=wrk+r'\ECA'
            uniqueList1=[]
            uniqueList2=[]
            today = datetime.date.today()
            year = today.year

            with arcpy.da.UpdateCursor(eca, HarvFields, ) as cursor:
                for row in cursor:
                    if row[0] is None and row[2] == 'YES':
                        if row[3] is None or row[3]==0 and row[4]>=(year-25):
                            row[1]=100
                            row[0]= 'Harvest'
                        elif row[3] >0:
                            row[1]=row[3]
                            row[0]= 'Harvest'
                    cursor.updateRow(row)    
            print('Harvest')

        def Pine_Adjustment (wrk):
            arcpy.env.workspace = wrk
            arcpy.env.overwriteOutput = True
            eca=wrk+r'\ECA'
            expression="pinep(!SPECIES_CD_1!,!SPECIES_PCT_1!,!SPECIES_CD_2!,!SPECIES_PCT_2!,!SPECIES_CD_3!,!SPECIES_PCT_3!,!SPECIES_CD_4!,!SPECIES_PCT_4!,!SPECIES_CD_5!,!SPECIES_PCT_5!,!SPECIES_CD_6!,!SPECIES_PCT_6!)"
            codeblock="""def pinep (sp1,pc1,sp2,pc2,sp3,pc3,sp4,pc4,sp5,pc5,sp6,pc6):
                pp=0
                if sp1.startswith('P'):
                    pp=pp+pc1
                elif sp2.startswith('P'):
                    pp=pp+pc2
                elif sp3.startswith('P'):
                    pp=pp+pc3
                elif sp4.startswith('P'):
                    pp=pp+pc4
                elif sp5.startswith('P'):
                    pp=pp+pc5
                elif sp6.startswith('P'):
                    pp=pp+pc6
                return pp
            """
            fieldList=['EARLIEST_NONLOGGING_DIST_TYPE','EARLIEST_NONLOGGING_DIST_DATE','STAND_PERCENTAGE_DEAD','BASAL_AREA','SPECIES_CD_1','SPECIES_PCT_1','SPECIES_CD_2','SPECIES_PCT_2','SPECIES_CD_3','SPECIES_PCT_3','SPECIES_CD_4','SPECIES_PCT_4','SPECIES_CD_5','SPECIES_PCT_5','SPECIES_CD_6','SPECIES_PCT_6','PROJ_AGE_1','PROJ_HEIGHT_1','FEATURE_AREA_SQM']
            
            layerpath=os.path.join(sdeloc,'WHSE_FOREST_VEGETATION.VEG_COMP_LYR_D_POLY')

            
            arcpy.management.AddField(eca,'Pine_pct', 'DOUBLE')
            arcpy.management.CalculateField(eca, 'Pine_pct', expression, "PYTHON3", codeblock)
            
            #select records with pine percen, then clip dead layer
            aoi=arcpy.management.SelectLayerByAttribute(eca,'NEW_SELECTION','"Pine_pct" > 0')
            #used clip as we are not concerned with the area of the poly but the attributes within and clip is the fastest

            #sometimes if you have not opened the sde connection in arcpro it will fail the cliop
            dead=wrk+r'\Dead_Layer'
            arcpy.analysis.Clip(in_features=layerpath,clip_features=aoi,out_feature_class=dead)
            print('Clip the Dead')
            val_join=arcpy.management.ValidateJoin(in_layer_or_view=eca,in_field='FEATURE_ID',join_table=dead,join_field='FEATURE_ID')
            print('Dead Join Valid')
            joined=arcpy.management.JoinField(in_data=eca, in_field='FEATURE_ID',join_table=dead,join_field='FEATURE_ID',fields=fieldList, fm_option='NOT_USE_FM')
            arcpy.CopyFeatures_management(joined,'ECA_D')
            eca='ECA_D'
            print('Join the Dead')
            #spatial join dead to ECA then calculate pine adjustment
            # aoi=arcpy.management.SelectLayerByAttribute(eca,'NEW_SELECTION','"Pine_pct" > 0')
            
            #use arcpy listfields to get all fields, for BASAL_AREA* SPECIES_CD and SPECIES_PCT

            expression='tot_Pine(!BASAL_AREA!,!BASAL_AREA_1!,!SPECIES_CD_1!,!SPECIES_PCT_1!,!SPECIES_CD_2!,!SPECIES_PCT_2!,!SPECIES_CD_3!,!SPECIES_PCT_3!,!SPECIES_CD_4!,!SPECIES_PCT_4!,!SPECIES_CD_5!,!SPECIES_PCT_5!,!SPECIES_CD_6!,!SPECIES_PCT_6!,!SPECIES_CD_12!,!SPECIES_PCT_12!,!SPECIES_CD_23!,!SPECIES_PCT_23!,!SPECIES_CD_34!,!SPECIES_PCT_34!,!SPECIES_CD_45!,!SPECIES_PCT_45!,!SPECIES_CD_56!,!SPECIES_PCT_56!,!SPECIES_CD_67!,!SPECIES_PCT_67!)'
            codeblock="""def tot_Pine(og_basal,d_basal,sp1,pc1,sp2,pc2,sp3,pc3,sp4,pc4,sp5,pc5,sp6,pc6,  dsp1,dpc1,dsp2,dpc2,dsp3,dpc3,dsp4,dpc4,dsp5,dpc5,dsp6,dpc6):
                tot_basal=og_basal+d_basal
                og_pct=0
                d_pct=0
                toatz=0

                if sp1.startswith('P'):
                    pct=pc1*(og_basal/tot_basal)
                    og_pct=og_pct+pct

                elif sp2.startswith('P'):
                    pct=pc2*(og_basal/tot_basal)
                    og_pct=og_pct+pct

                elif sp3.startswith('P'):
                    pct=pc3*(og_basal/tot_basal)
                    og_pct=og_pct+pct

                elif sp4.startswith('P'):
                    pct=pc4*(og_basal/tot_basal)
                    og_pct=og_pct+pct

                elif sp5.startswith('P'):
                    pct=pc5*(og_basal/tot_basal)
                    og_pct=og_pct+pct

                elif sp6.startswith('P'):
                    pct=pc6*(og_basal/tot_basal)
                    og_pct=og_pct+pct

                elif dsp1.startswith('P'):
                    pct=dpc1*(d_basal/tot_basal)
                    d_pct=d_pct+pct

                elif dsp2.startswith('P'):
                    pct=dpc2*(d_basal/tot_basal)
                    d_pct=d_pct+pct

                elif dsp3.startswith('P'):
                    pct=dpc3*(d_basal/tot_basal)
                    d_pct=d_pct+pct

                elif dsp4.startswith('P'):
                    pct=dpc4*(d_basal/tot_basal)
                    d_pct=d_pct+pct

                elif dsp5.startswith('P'):
                    pct=dpc5*(d_basal/tot_basal)
                    d_pct=d_pct+pct

                elif dsp6.startswith('P'):
                    pct=dpc6*(d_basal/tot_basal)
                    d_pct=d_pct+pct

                toatz=og_pct+d_pct
                return toatz
            """
            arcpy.management.AddField(eca,'Total_Pine_Pct', 'DOUBLE')
            arcpy.management.CalculateField(eca, 'Total_Pine_Pct', expression, "PYTHON3", codeblock)
            with arcpy.da.UpdateCursor(eca, ['Total_Pine_Pct','STAND_PERCENTAGE_DEAD'] ) as cursor:
                for row in cursor:
                    if row[0] == None:
                        row[0]=0
                    elif row[1] == None:
                        row[1]=0
                    cursor.updateRow(row)
            print('pine updated')


        def ECA_Type_IBM (wrk):
            arcpy.env.workspace=wrk
            eca=wrk+r'\ECA_D'
            uniqueList1=[]
            uniqueList2=[]

            with arcpy.da.UpdateCursor(eca, IBMonlyFields ) as cursor:
                for row in cursor:
                    if row[0] is None and row[2]=='IBM' or row[2]=='I' and row[3] !='YES' and row[6]>30 and row[7]>30:
                        row[0]='MPB'
                        row[1]= row[5]
                        if row [1] >100:
                            row[1]=100
                    cursor.updateRow(row)

            with arcpy.da.UpdateCursor(eca, IBMharvFields, ) as cursor:
                for row in cursor:
                    if row[0] is None and row[2]=='IBM' or row[2]=='I' and row[3] =='YES' and row[6]>30 and row[7]>30:
                        row[0]='MPB and Harvest'
                        row[1]= row[4]+row[5]
                        if row [1] >100:
                            row[1]=100
                    cursor.updateRow(row)
            print('MPB')

        def clean_wrksp(wrk):
            arcpy.env.workspace=wrk
            ecaD=wrk+r'\ECA_D'
            eca=wrk+r'\ECA'
            arcpy.management.Delete(eca)
            arcpy.management.CopyFeatures(ecaD,eca)
            arcpy.management.Delete(ecaD)


        #|-----Define fields for cursors-----|
        ROW_IR_Fields=['ECA_Type', 'ECA_Factor','Flag']
        NNfields=['ECA_Type', 'ECA_Factor','BCLCS_LEVEL_5','NON_PRODUCTIVE_DESCRIPTOR_CD']
        PloggedFields=['ECA_Type', 'ECA_Factor', 'VRI2_DISTURB_CODE']
        
        IBMonlyFields=['ECA_Type', 'ECA_Factor', 'VRI2_DISTURB_CODE','VRI2_HARVESTED','Height_Factor','MPB_Factor','Total_Pine_Pct','STAND_PERCENTAGE_DEAD']
        IBMharvFields=['ECA_Type', 'ECA_Factor', 'VRI2_DISTURB_CODE','VRI2_HARVESTED','Height_Factor','MPB_Factor','Total_Pine_Pct','STAND_PERCENTAGE_DEAD']
        HarvFields=['ECA_Type', 'ECA_Factor', 'VRI2_HARVESTED','Height_Factor','VRI2_DISTURB_YR']
        PineFields=['ECA_Type', 'ECA_Factor','STAND_PERCENTAGE_DEAD','Pine_pct'] 

        #|------Call Functions-----|
        bd_gbd (output)
        union_1(wrkspc)
        flag100_75(uni)
        CopyMoveVRI2(VRI2gdb,wrkspc)
        union_2_erase(wrkspc)
        ECA_Type_Factor_ROW_IR_Priv(wrkspc)
        ECA_Type_Factor_Non_Natural (wrkspc)
        ECA_Type_Factor_PLogged(wrkspc)
        ECA_Type_Factor_Fire (wrkspc)
        MPBFactor(wrkspc)
        HeightFactor(wrkspc)
        ECA_Type_Harvest(wrkspc)
        Pine_Adjustment(wrkspc)
        ECA_Type_IBM (wrkspc)
        clean_wrksp(wrkspc)
        print('ECA Complete')


            
