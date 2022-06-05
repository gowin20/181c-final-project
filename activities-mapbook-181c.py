## Geog 181C 181 Project
## May 2022
## authors: Peter Flanders, George Owen, Seamus Sehres, Grant Linford, Wesley Motlow

import time
import arcpy
import os
from csv import reader
import argparse
import requests
import json

'''
Folder Structure
/181finalproj
├─── README.txt
├─── activities-mapbook-181c.py
├─── /ProjectData
     ├─── activities-mapbook-181c.aprx (project file)
     ├─── activity-data.csv(source data)
├─── /output
|     (location of table to be created)
'''


# Set up Geocoding Services
try:
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="activities-mapbook-181c")
    geopy_installed = True
except ImportError:
    print("Geopy not installed. Continuing..")
    geopy_installed = False

try:    
    with open('config.json') as file:
        ARCGIS_DEVELOPER_API_KEY = json.load(file)["KEY"]
    print(f'Arcgis Developer Key={ARCGIS_DEVELOPER_API_KEY}')
except FileNotFoundError:
    ARCGIS_DEVELOPER_API_KEY = None
    if not geopy_installed:
        print("The config file `config.json` was not created, and geopy was not installed. All Geocoding services are disabled.")


# Set Folder Paths and Environment Variables
folder_path = r''

arcpy.env.workspace = folder_path

arcpy.env.overwriteOutput = True

data_folder = os.path.join(folder_path, "ProjectData")

activity_csv = os.path.join(data_folder, "activity-data.csv")

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
theLakeMapFrame = thisLayout.listElements("MAPFRAME_ELEMENT")[0]
first_extent = arcpy.Extent(-118.6696481, 34.2278393, -118.1968878, 33.9179820)
theLakeMapFrame.camera.setExtent(first_extent)
theLakeMapFrame.camera.scale = theLakeMapFrame.camera.scale * 1.3

parser = argparse.ArgumentParser(description='Create a mapbook from a location.')
parser.add_argument('--lat',  type=float,
                    help='One float, a latitude value.')
parser.add_argument('--long', type=float,
                    help='One float, a longitude value.')
parser.add_argument('--address', type=str, 
                    help='An address description to be geocoded into a coordinate pair. MUST HAVE QUOTES (i.e. "125 East Lincoln Lane:)')
parser.add_argument('-t', action='store_true',
                    help='An boolean to describe if the script it running as a test or full output. Type -t to run as test')
args = parser.parse_args()

if args.t:
    print("Running as Test. Using activies-data-TESTING.csv")
    activity_csv = os.path.join(data_folder, "activity-data-TESTING.csv")

# Orgin of our mapbook! 
# Priority is (1) specified coords, (2) specified address, (3) default coords
# The logic flow is untraditional below, but it is because I wish to try and fill the coordinates 
# with multiple different sources before resorting to the default start location.
coordinates_assigned = False

if args.lat and args.long:
    coordinates_assigned = True
    start = (args.long, args.lat)

if args.address and geopy_installed and not coordinates_assigned:
    # use geopy I like it more
    try:
        location = geolocator.geocode(args.address)
        if location:
            start = (location.longitude, location.latitude)
            print(f'Geopy geolocated the address at {start}')
            coordinates_assigned = True
    except Exception as e:
        print(f"Geopy geocoding raised Exception {e}.")

if args.address and ARCGIS_DEVELOPER_API_KEY and not coordinates_assigned:
    # try to use esri's server
    try:
        # using some code from https://community.esri.com/t5/arcgis-api-for-python-blog/single-address-geocode-with-python/ba-p/902908 to geocode from arc servers
        geoCodeUrl = f"https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?token={ARCGIS_DEVELOPER_API_KEY}&f=json"
        
        #clean up the address for url encoding
        address = args.address.replace(" ", "+")
        address = address.replace(",", "%3B")
        url = geoCodeUrl + "&address=" + address
        print(f'url={url}')

        #send address to geocode service
        lookup = requests.get(url)
        data = lookup.json()
        print(f'data from esri server is: {data}')
    except Exception as e:
        print(f"ESRI geocoding service raised Exception {e}. ")

    try:    
        if data["candidates"]:
            #woo hoo results
            coords = data["candidates"][0]["location"]
            start = coords["x"], coords["y"]
            print(f'ESRI geolocated the address at {start}')
            coordinates_assigned = True
    except Exception as e:
        print(f"ESRI geocoding service raised Exception {e}. It may be that the address provided is not accurate enough.")

if not coordinates_assigned:
    if args.address:
        print('Default Coordinate being used. Potentially invalid address provided.')
    start = (-118.44497818287402, 34.06877178584797) # Center of UCLA!



def add_route_to_map(stop_coords): 
    """
    PARAM: stop_coords (tuple): a pair of coodinates (longitutde, latitude) 
    RETURN: directions: list of strings containing English directions for a navigation system.
    1. Creates a new Feature Class (this_route_points) in memory to store the route points
    2. Adds beginning and end coordinates to this_route_points
    3. Computes the route using `FindRoutes_agolservices`
    4. Converts the result of `FindRoutes_agolservices` to a layer object and adds this to the current map 
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

    #sleep while geoprocessing server runs commands
    while result.status < 4:
        time.sleep(2)
        print(f"Processing Status: {result.status}")
    #print(result.getMessages(0))

    #variable containing the route
    route = result[1]
    
    #used to get the directions
    textfile = result[3]

    #python list containing the step-by-step directions
    directions = ""
    for i, step in enumerate(arcpy.da.SearchCursor(textfile, ["Text"])):
        directions += str(i) + ": " + step[0] + "\n"

    
    # Step 4
    #remove the previous route if there is one
    layer = m.listLayers('route_layer')
    if layer:
        print(f"Removing old layer named: {layer[0].name}")        
        m.removeLayer(layer[0])
    
    #make temporary route_layer file to add to map
    route.save(route_save_path)
    route_layer = arcpy.MakeFeatureLayer_management(route, 'route_layer')
    layer_file = arcpy.SaveToLayerFile_management(route_layer, os.path.join(output_folder, 'route_layer'))

    #add current generated route_layer file
    print(f"add data from path: {m.addDataFromPath(layer_file[0])}")

    #set extent for current route
    desc = arcpy.Describe('route_layer')
    new_extent = arcpy.Extent(desc.extent.XMin, desc.extent.YMin, desc.extent.XMax, desc.extent.YMax)
    theLakeMapFrame.camera.setExtent(new_extent)
    theLakeMapFrame.camera.scale = theLakeMapFrame.camera.scale * 1.3

    return directions


## ===== Main Loop =====    
with open(activity_csv, 'r') as read_obj:
    csv_reader = reader(read_obj)
    header = next(csv_reader)
    # Check file as empty
    if header is not None:
        # Iterate over each row after the header in the csv
        for entry_row in csv_reader:
            # row variable is a list that represents a row in csv
            print(f"  Location Name is {entry_row[0]}, its type is {entry_row[3]}, and its coords are ({entry_row[1]}, {entry_row[2]})")
            tmp_coord = (float(entry_row[2]), float(entry_row[1]))
            
            #generate directions to this entry, and add the route to the map
            directions = add_route_to_map(stop_coords=tmp_coord)

            # add directions into the layout
            thisLayout.listElements("TEXT_ELEMENT")[0].text = directions
            thisLayout.listElements("TEXT_ELEMENT")[1].text = "Route To: " + entry_row[0]
            
            # export layout to pdf
            thisLayout.exportToPDF(tmp_PDF_path)
            
            # append pdf to final_PDF
            final_PDF.appendPages(tmp_PDF_path)
            print(f"Added {entry_row[0]} to mapbook.")
            
            



# Remove the tmpPDF at the end of the session
# if os.path.exists(tmp_PDF_path):
#     os.remove(tmp_PDF_path)

final_PDF.saveAndClose()


aprx.save() 
