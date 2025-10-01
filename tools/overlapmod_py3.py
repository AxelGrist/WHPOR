'''
Purpose: The purpose is to check any input feature class for polygon overlap then output a new file or overwrite the existing and clean up overlaps.

Date: October, 2013

Created by: Graham MacGregor Thompson Okanagan Region (FLNRO)

Arguments:

Version: created in arcgis 10.0 arcpy format

Classes
-----------
featureClass(The feature class to check, the name of the ouput feature class, the boundary area extent that will be checked(if no boundary)
        -     this class will provide easy access to the properties of a featureClass. 
            if no gp is provided the full path of the featureClass/layer/shapefile
            must be provided.
        
        -    Properties such as name, type, geomField, shapeType,
            and a list of field names are availiable

'''

#Run the regular stuff
import os, sys, arcpy, time




#user Variables


arcpy.env.overwriteOutput = True

class featureClass:
    #delete Duplicate is = 1 then the first
    start = 0
    def __init__(self, inputLayer, BAfold, sExtractLoc=None):        #, boundarySource):
        start = time.time()
        self.inputLayer = inputLayer
        self.BAfold=BAfold
        #self.boundarySource = boundarySource
        tmpdrive = os.path.join( self.BAfold,r'1_SpatialData\3_VRI_Update')
        tmpFGDB = r"temp_data"
        self.sExtractLoc = os.path.join(tmpdrive, tmpFGDB) + ".gdb"
        if not arcpy.Exists(self.sExtractLoc):
            arcpy.CreateFileGDB_management(tmpdrive, tmpFGDB)
            print ('Temporary file geodatabase created')
    
    #example of sort fields string
    #sortFields = "STATE_NAME A; POP2000 D"
    def findoverlap(self, boundarySource, outputName, sortFields = None, delVar = None):#, boundarySource, deleteDuplicate):
        inLayer = arcpy.MakeFeatureLayer_management(self.inputLayer,'inputLyr')
        boundLayer = arcpy.MakeFeatureLayer_management(boundarySource,'bndLyr')
        
        
        #clip the in featureclass this creates a clipped copy - THIS SHOULD ALREADY BE CLIPPED.  Identity also used below.
        #print 'clipping data to boundary'
        #opening_extract = arcpy.Clip_analysis(inLayer, boundLayer, self.sExtractLoc + "/Temp_clip")
        opening_extract = inLayer
        
        #calc Opening Area
        descObj = arcpy.Describe(opening_extract)
        ftype = descObj.ShapeType
        if ftype == 'Polygon':
            areaItem = descObj.AreaFieldName #Get the shape field name
        shapeName = descObj.ShapeFieldName
        
        fieldNameslist = [f.name for f in arcpy.ListFields(opening_extract)]
        if "AREA_HA" not in fieldNameslist:
            arcpy.AddField_management(opening_extract, "AREA_HA", "DOUBLE")

        #arcpy.CalculateField_management(opening_extract, "AREA_HA", '[' + areaItem + '] / 10000') # calculate hectares
        # Python 64
        arcpy.CalculateField_management(opening_extract, 'AREA_HA', "!" + areaItem + "!/10000","PYTHON_9.3") # calculate hectares
                
        
        #identity with org bdy
        opening_ident = arcpy.Identity_analysis(opening_extract, boundarySource, self.sExtractLoc + "/tempident") # identitiy between org boundaries and openings
        
        #Calculate Centroid and duplicate indicator
        descObj = arcpy.Describe(opening_ident)
        shapeName = descObj.ShapeFieldName #Get the shape field name
        #get list
        fieldNameslist = [f.name for f in arcpy.ListFields(opening_ident)]
        if "CENT_XY" not in fieldNameslist:
            arcpy.AddField_management(opening_ident, "CENT_XY", "TEXT", 50) #Add field for centroid string
        calcExp = "str(!" + shapeName + ".CENTROID!)" # expression for calculation of centroid
        arcpy.CalculateField_management(opening_ident, "CENT_XY", calcExp, "PYTHON")# run the calculation
        if "DUPLICATE_IND" not in fieldNameslist:
            arcpy.AddField_management(opening_ident, "DUPLICATE_IND", "TEXT", 1) # add a text field to mark the duplicates
        
        #Delete non-openings
        
        # Start Cursor to find duplicates. creates
        rows = arcpy.UpdateCursor(opening_ident, "", "", "", sortFields)
        print ('checking for duplicates... Please wait')
        centroidList = []
        overlapList = []
        foundalready = []
        for row in rows:
            centroid = row.getValue("CENT_XY")
            if centroid in centroidList:
                # print 'found duplicate' + centroid
                row.setValue("DUPLICATE_IND", "Y")
                overlapList.append(centroid)
            else:
                centroidList.append(centroid)
                row.setValue("DUPLICATE_IND", "N")
            # update the row
            rows.updateRow(row)

        try:
            del row, rows
        except:
            del rows
        
        #Calculate duplicate area
        descObj = arcpy.Describe(opening_ident)
        shapeName = descObj.ShapeFieldName #Get the shape field name
        ftype = descObj.ShapeType
        if ftype == 'Polygon':
            areaItem = descObj.AreaFieldName
        if "DUP_HA" not in fieldNameslist:
            arcpy.AddField_management(opening_ident, "DUP_HA", "DOUBLE")
        #arcpy.CalculateField_management(opening_ident, "DUP_HA", '[' + areaItem + '] / 10000')
        # Python 64
        arcpy.CalculateField_management(opening_ident, 'DUP_HA', "!" + areaItem + "!/10000","PYTHON_9.3") # calculate hectares

        if "DUP_HA" not in fieldNameslist:
            arcpy.AddField_management(opening_ident, "PCT_DUP", "DOUBLE")
            #openingIdentLyr = gp.makeFeatureLayer_Management(opening_ident, "openingIdentLyr")
        #arcpy.CalculateField_management(opening_ident, "PCT_DUP", '([DUP_HA] / [AREA_HA])*100')
        # python 64
        arcpy.CalculateField_management(opening_ident, "PCT_DUP", "(!DUP_HA! / !AREA_HA!) *100", "PYTHON_9.3", "")
        print ('Done checking for duplicates')
        finalLayer = arcpy.MakeFeatureLayer_management(self.sExtractLoc + "/tempident",'finalLyr')
        arcpy.SelectLayerByAttribute_management(finalLayer,"NEW_SELECTION", "\"DUPLICATE_IND\" = 'Y' ")
        arcpy.CopyFeatures_management(finalLayer, outputName+"duplicates")
        arcpy.SelectLayerByAttribute_management(finalLayer,"NEW_SELECTION", "\"DUPLICATE_IND\" <> 'Y' ")
        arcpy.CopyFeatures_management(finalLayer, outputName+"fixed")
        print (' The feature with duplicates identified has been copied as ' + outputName+"fixed")
        #delete variables in fixed feature class
        if delVar == '1':
            print ('deleting overlap fields for' + outputName+"fixed")
            fieldList = ['PCT_DUP','DUP_HA','DUPLICATE_IND','CENT_XY','AREA_HA']
            for field in fieldList:
                arcpy.DeleteField_management(outputName+"fixed",field)
        #if deleteduplicate == 1:
        '''
        #Start Cursor to mark overlaps to create a just found layer
        opening_ident = arcpy.Identity_analysis(boundarySource, opening_extract, sExtractLoc + "/tempident")
        opening_copy = arcpy.CopyFeatures_management(opening_ident , sExtractLoc + "/delcopy")
        rows = arcpy.UpdateCursor(opening_copy)
        
        for row in rows:
                centroid = row.getValue("CENT_XY")
                if centroid in overlapList:
                    row.setValue("DUPLICATE_IND", "Y")
                    #update the row
                    rows.updateRow(row)
                    itemcount = overlapList.count(centroid)
                    count = 1
                    while (count <= itemcount):
                        overlapList.remove(centroid)
                        count = count + 1
                    foundalready.append(centroid)
                #if
                elif centroid in foundalready:
                    #not overlap so delete
                    row.setValue("DUPLICATE_IND", "F")
                    rows.updateRow(row)
                    rows.deleteRow(row)
                #go to next row
                else:
                    #not overlap so delete
                    row.setValue("DUPLICATE_IND", "S")
                    rows.updateRow(row)
                    rows.deleteRow(row)
                #go to next row
                row = rows.next()
        del row, rows
    
        '''
    stop = time.time()
    print (str(round((stop - start)/3600,4)) + ' hrs')
    

