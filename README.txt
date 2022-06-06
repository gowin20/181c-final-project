Repository containing all files for the GEOG 181C Final Project: Student Activity Locator

The authors of this project were Peter Flanders, George Owen, Wesley Motlow, Grant Linford, and Seamus Sehres.

The goal of this project was to create a student-oriented Activities Locator, curated with activities and destinations for students at UCLA. What makes UCLA a truly unique school to attend, besides the world class academics, are the near endless opportunities for students to eat, drink, and explore the greater Los Angeles area. Some colleges are in places with far fewer opportunities, so this group wanted to highlight what is available to UCLA students.

Getting Started:
1. First, clone/download this repository.
2. The required packages are 
  - The Python Standard Library
  - arcpy 
3. Optional Packages include:
  - geopy (this is a more consistent geocoding service, but a pain to install with ArcGIS Pro's conda envs)
3. If you want to use the --address argument to specify the location of the mapbook, you need to either have installed geopy or you need to add a file called `config.json` in the root directory with your ArcGIS Developer API Key.  
4. You can run the main script with `python activities-mapbook-181c.py`
4. This should produce logs in the terminal indicating progress and after ~10min the final mapbook pdf should be created and saved in the output folder.

Optional arguments for the script are as follows:
  -h, the help flag which explains these arguments to users in the command line.
  --lat, which takes in a single float value, the latitude (must be used with --long)
  --long, which takes in a single float value, the longitutde (must be used with --lat)
  --address, which takes a string and attempts to geocode it based on some conditions, 
  -t, which is a boolean flag which allows the user to run the script as a test. MUCH QUICKER

Sample usage:
`
python .\activities-mapbook-181c.py --address "337 Charles E Young Dr E, Los Angeles, CA 90095"
`
This line of code runs a full book of routes from the address of UCLA's Public Affairs Building at the address listed above. 
