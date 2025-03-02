import os
import sys
import configparser


# Function to end program safely
def end_safely(status: int):
    input("Press enter to exit program...")
    sys.exit(status)


# Replace location paths with their ID's
def translate_locations(data: list[dict], locations: list[str], loc_ids: list[str]) -> list[dict]:
    for dictionary in data:
        location = dictionary["location"]
        if location in locations:
            loc_ind = locations.index(location)
            dictionary["location"] = loc_ids[loc_ind]
        else:
            print(f"Location {location} not found. These items will be unaffected:")
            print(dictionary["items"])
            dictionary["items"] = []

    return data


project_root = os.path.abspath(os.path.dirname(__file__))

config_path = os.path.join(project_root, '../config.ini')

config = configparser.ConfigParser()
config.read(config_path)