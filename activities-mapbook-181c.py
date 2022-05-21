## Geog 181C 181 Project
## May 2022
## authors:


from typing import Tuple
import arcpy
import os
import json
import time
from csv import reader

'''
Folder Structure
/181finalproj
├─── activities-mapbook-181c.py
├─── /ProjectData
     ├─── activities-mapbook-181c.aprx (project file)
     ├─── activity-data.csv(source data)
├─── /output
|     (location of table to be created)
'''



# Set Folder Paths and Environment Variables
folder_path = r''

arcpy.env.workspace = folder_path

arcpy.env.overwriteOutput = True

data_folder = os.path.join(folder_path, "ProjectData")

activity_csv = os.path.join(data_folder, "activity-data-TESTING.csv")

route_save_path = os.path.join(data_folder, r"activities-mapbook-181c.gdb\temp_route2")
route_layer_save_path = os.path.join(data_folder, r"activities-mapbook-181c.gdb\temp_route_layer")

output_folder = os.path.join(folder_path, "output")

#Create output PDFs

tmp_PDF_path = os.path.join(output_folder,"tmp.pdf")

final_PDF_path = os.path.join(output_folder,"mapbook.pdf")

if os.path.exists(final_PDF_path):
    os.remove(final_PDF_path)

final_PDF = arcpy.mp.PDFDocumentCreate(final_PDF_path)

aprx = arcpy.mp.ArcGISProject(os.path.join(data_folder, "activities-mapbook-181c.aprx"))

m = aprx.listMaps()[0]
thisLayout = aprx.listLayouts()[0]

# the bruin bear!
start = (-118.44503670675103, 34.07098667225605)


def add_route_to_map(stop_coords: Tuple): 
    """
    PARAM: stop_coords (tuple): a pair of coodinates (longitutde, latitude) 
    
    RETURN: directions: list of strings containing English directions for a navigation system.

    1. Creates a new Feature Class (this_route_points) in memory to store the route points
    2. Adds beginning and end coordinates to this_route_points
    3. Computes the route using `FindRoutes_agolservices`
    4. Converts the result of `FindRoutes_agolservices` to a layer object and adds this to the current map 
        ----THIS ROUTE OBJECT NEEDS TO BE REMOVED AT A LATER POINT IN THE SCRIPT-----
    5. returns the directions list for potential usage in the layout.
    """   
    # Step 1. create feature class (hopefully overwriting exisiting FC in memory)
    this_route_points = arcpy.CreateFeatureclass_management("in_memory", "tempfc", "POINT")[0]

    # Step 2. add start and stop points to this route
    with arcpy.da.InsertCursor(this_route_points, ["SHAPE@XY"]) as cursor:
        cursor.insertRow([start])
        cursor.insertRow([stop_coords])

    # Step 3. run find route command
    result = arcpy.FindRoutes_agolservices(this_route_points,"Seconds")
    
    print(f"Finding Route, PID: {result.resultID}")
    print(f"Processing Status: {result.status}")

    #sleep while geoprocessing server runs commands
    while result.status < 4:
        time.sleep(1)
        print(f"Processing Status: {result.status}")
    print(result.getMessages(0))

    #variable containing the route
    route = result[1]
    
    #used to get the directions
    textfile = result[3]

    #python list containing the step-by-step directions
    directions = []

    for step in arcpy.da.SearchCursor(textfile, ["Text"]):
        directions.append(step[0])

    
    # Step 4
    print(f"route saving : {route.save(route_save_path)}")

    #remove the previous route if there is one
    layer = m.listLayers('route_layer')
    if layer:
        print(f"Removing old layer named: {layer[0].name}")        
        m.removeLayer(layer[0])
    route_layer = arcpy.MakeFeatureLayer_management(route, 'route_layer')
    print(f"type of route_layer is {type(route_layer)}")
    print(f"type of route_layer[0] is {type(route_layer[0])}")
    print(f"type of route_layer.dataSource is {type(route_layer[0].dataSource)}")
    print(f'route_layer data source is {route_layer[0].dataSource}')
    layer_file = arcpy.SaveToLayerFile_management(route_layer)
    
    #add current generated route
    print(f"current layers in map before add : {[l.name for l in m.listLayers()]}")
    print(f"using func addLayer: {m.addLayer(route_layer[0])}")
    #print(f"add data from path: {m.addDataFromPath(layer_file)}")
    print(f"current layers in map after add : {[l.name for l in m.listLayers()]}")
    print(f"layer 0 data source: {m.listLayers()[0].dataSource}")
    

    return directions


## ===== Main Loop =====    
with open(activity_csv, 'r') as read_obj:
    csv_reader = reader(read_obj)
    header = next(csv_reader)
    # Check file as empty
    if header != None:
        # Iterate over each row after the header in the csv
        for entry_row in csv_reader:
            # row variable is a list that represents a row in csv
            print(f"  Location Name is {entry_row[0]}, its type is {entry_row[3]}, and its coords are ({entry_row[1]}, {entry_row[2]})")
            tmp_coord = (float(entry_row[2]), float(entry_row[1]))
            
            #generate directions to this entry, and add the route to the map
            directions = add_route_to_map(stop_coords=tmp_coord)

            thisLayout.exportToPDF(tmp_PDF_path)

            final_PDF.appendPages(tmp_PDF_path)
            print(f"Added {entry_row[0]} to mapbook.")
            
            """
            TODO: use lab 7 code to print a new layout for each
             
            theTitleLayout.listElements("TEXT_ELEMENT")[0].text = "directions somehow currently directions is a list so it wont work without conversion"

            """



# Remove the tmpPDF at the end of the session
# if os.path.exists(tmp_PDF_path):
#     os.remove(tmp_PDF_path)

final_PDF.saveAndClose()


# aprx.save() no need tbh
