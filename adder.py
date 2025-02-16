import os
import sys
import subprocess
import speech_recognition as sr
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
import requests
import csv
import configparser


# Data models for Gemini return
class Item(BaseModel):
    item: str
    number: int
    description: str


class Additions(BaseModel):
    location: str
    items: list[Item]


# Fetch authentication token for Homebox API
def get_homebox_auth_key() -> str:
    if not all([os.getenv("HOMEBOX_URL"), os.getenv("HOMEBOX_USERNAME"), os.getenv("HOMEBOX_PASSWORD")]):
        raise ValueError("Missing environment variables for Homebox authentication.")

    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/users/login"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    data = {
        "password": os.getenv("HOMEBOX_PASSWORD"),
        "stayLoggedIn": True,
        "username": os.getenv("HOMEBOX_USERNAME")
    }

    res = requests.post(url, headers=headers, json=data)

    if "application/json" not in res.headers.get("Content-Type", ""):
        print("Unexpected response format:", res.text)
        raise ValueError("Server did not return JSON.")

    res_data = res.json()

    return res_data["token"]


# Retrieve locations from Homebox and structure them in a list, with accompanying ID list
def get_locations(auth_key: str) -> (list[str], list[str]):
    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/locations/tree"
    headers = {"Authorization": f"{auth_key}", "Accept": "application/json"}
    res = requests.get(url, headers=headers)

    location_list = res.json()

    locations: list[str] = []
    ids: list[str] = []
    for location in location_list:
        locs, idss = helper_location_tree(location)
        locations.extend(locs)
        ids.extend(idss)

    return locations, ids


# Recursively process location tree
def helper_location_tree(node: dict) -> (list[str], list[str]):
    name = node["name"]
    locations = [name]
    ids = [node["id"]]
    for child in node["children"]:
        sub_locations, sub_ids = helper_location_tree(child)
        for s_loc in sub_locations:
            locations.append(f"{name}/{s_loc}")
        ids.extend(sub_ids)

    return locations, ids


# Convert audio file into text using speech recognition
def interpret_sound_file(filename: str) -> str:
    r = sr.Recognizer()

    with sr.AudioFile(filename) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
        return text


# Process AI response to structure recognized items and locations
def get_json_from_gemini(recognized_text: str, location_list: list[str], generate_description: bool=False) -> list[dict]:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # AI prompt to structure the recognized text properly
    prompt = f"""
            The following is a speech-recognition text with one or more parts which each start with a location and is followed by a list of items separated by the word "next".
            There may be several locations. All items coming after location A but before location B should end up in location A.
            Locations should be on the form "location" if they are alone, but if they are in or under something they should be separated with slashes, with the outermost container being furthest to the left and the innermost container being furthest to the right.
            For example, "Box 5 in Cabinet inside Pantry" should be on the form Pantry/Cabinet/Box 5.
            Do NOT change the location unless explicitly told, even if it sounds like it would fit somewhere else.
            Capitalize the text nicely. Number should be 1 unless otherwise specified.
            Please create a json object that has all of these locations connected to the items that are in them.
            If something is a speech recognition error, you would correct the item.
            {"Try to generate a short description for each item, if possible." if config["SETTINGS"]["generate_description"] else "Leave the description field blank."}
            
            Locations have to be in the following list, if none fits put "error":
            {location_list}
            
            The input string is:
            {recognized_text} 
            """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Additions]
        }
    )
    return [item.model_dump() for item in response.parsed]


# Write data to file for error check
def write_to_file(filename: str, data: list[dict]):
    with open(filename, 'w') as file:

        file.write("""# Use this file to fix any errors made by the AI
# If location is <error>, make sure to assign a correct location!
# eg 'Kitchen' or 'Storage Room/Shelf 1/Box 4'.
""")

        for entry in data:
            file.write(f"<{entry['location']}>\n")
            for item in entry['items']:
                file.write(f"{item['number']} ::-:: {item['item']} ::-:: {item['description']}\n")
            file.write("\n")


# Load after file editing is complete
def load_from_file(filename: str) -> list[dict]:
    updated_data = []
    current_location = None
    current_items = []

    with open(filename, 'r') as file:
        lines = file.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith('<') and line.endswith('>'):
                if current_location:
                    updated_data.append({"location": current_location, "items": current_items})

                current_location = line[1:-1]  # Strip the < and >
                current_items = []
            elif " ::-:: " in line:
                item = line.split(" ::-:: ", 2)
                current_items.append({"item": item[1], "number": int(item[0]), "description": item[2]})

        if current_location:
            updated_data.append({"location": current_location, "items": current_items})

    return updated_data


# Open in editor for error check
def open_in_editor(filename: str):
    if os.name == 'posix':  # For macOS/Linux
        subprocess.run(['open', filename])
    elif os.name == 'nt':  # For Windows
        subprocess.run(['notepad', filename])


# Check the results from the LLM for erroneous locations/items
def check_for_errors(data: list[dict]) -> list[dict]:
    temp_file = "temp"

    write_to_file(temp_file, data)

    open_in_editor(temp_file)

    return load_from_file(temp_file)


# Replace location paths with their ID's
def translate_locations(data: list[dict], locations: list[str], loc_ids: list[str]) -> list[dict]:
    for dictionary in data:
        location = dictionary["location"]
        if location in locations:
            loc_ind = locations.index(location)
            dictionary["location"] = loc_ids[loc_ind]
        else:
            print(f"Location {location} not found. Not adding these items:")
            print(dictionary["items"])
            dictionary["items"] = []

    return data


# Add an item to Homebox using the Homebox API
def add_item(item: dict, location: str, auth_key: str) -> bool:
    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/items"
    headers = {"Authorization": f"{auth_key}", "Accept": "application/json", "Content-Type": "application/json"}
    data = {
        "name": item["item"],
        "locationId": location,
        "description": item["description"],
        "quantity": item["number"]
    }

    res = requests.post(url, headers=headers, json=data)

    if res.status_code == 201:
        return True
    return False


# Add all items in a data dict to Homebox
def add_data_to_storage(data: list[dict], auth_key: str) -> dict:
    failed_adds = {}
    for container in data:
        location = container["location"]
        for item in container["items"]:
            res = add_item(item, location, auth_key)
            if not res:
                if location in failed_adds:
                    failed_adds[location].append(item)
                else:
                    failed_adds[location] = [item]

    return failed_adds


# Optional output: generate CSV file for importable data
def generate_importable_csv(filename: str, data: list[dict]):
    with open(filename, mode="w", newline="") as file:
        fieldnames = ["HB.name", "HB.quantity", "HB.location", "HB.description"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()  # Write column headers

        # Process each location and its items
        for entry in data:
            location = entry["location"]
            for item in entry["items"]:
                writer.writerow({
                    "HB.name": item["item"],
                    "HB.quantity": item["number"],
                    "HB.location": location,
                    "HB.description": item["description"]
                })

    print(f"Generated file {filename}")


def common_process(filename: str) -> (list[dict], list[str], list[str], str):
    load_dotenv()

    auth = get_homebox_auth_key()
    locations, loc_ids = get_locations(auth)

    print("Locations got!")

    text = interpret_sound_file(filename)

    print(f"Text interpreted as: {text}")

    data = get_json_from_gemini(text, locations, True)

    print("Formated by LLM!")

    data = check_for_errors(data)

    print("Data checked for errors!")

    return data, locations, loc_ids, auth


# Add directly to Homebox from sound file.
def add_from_sound_file(filename: str):
    data, locations, loc_ids, auth = common_process(filename)

    data = translate_locations(data, locations, loc_ids)

    print("Locations translated!")

    failed = add_data_to_storage(data, auth)

    if failed:
        print("Failed to add these items: ")
        print(failed)
    else:
        print("Successfully added all items!")


# Generate an importable CSV
def csv_from_sound_file(soundfile: str, outfile: str):
    data, _, _, _ = common_process(soundfile)

    generate_importable_csv(outfile, data)


# Code for processing file
def process_file(filename: str):
    if not os.path.exists(filename):
        print("Error: File does not exist.")
        return

    print(f"Processing file: {filename}")

    if config["SETTINGS"]["output_into_csv"]:
        out_name = input("Choose name of output file (without .csv): ")
        csv_from_sound_file(filename, out_name + ".csv")
    else:
        add_from_sound_file(filename)


# Main program function
def main():
    filename = input("Which file should be processed? ")

    process_file(filename)


config = configparser.ConfigParser()
config.read("config.ini")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            process_file(arg)
    else:
        main()
