from backend.general import config, end_safely, translate_locations
from backend.api_access import get_homebox_auth_key, get_locations, add_item
from backend.voice_recognition import interpret_sound_file
from backend.llm import get_parsed_list
from backend.error_check import check_for_errors_with_header


import os
import sys
from dotenv import load_dotenv
from pydantic import BaseModel
import csv


# Data models for Gemini return
class Item(BaseModel):
    name: str
    quantity: int
    description: str


class Additions(BaseModel):
    location: str
    items: list[Item]


def process_with_llm(recognised_text: str, location_list: list[str]) -> list[dict]:
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
                {"Try to generate a short description for each item, if possible." if config.getboolean("ADDER", "generate_description") else "Leave the description field blank."}

                Locations have to be in the following list, if none fits put "error":
                {location_list}

                The input string is:
                {recognised_text} 
                """

    llm_config = {
            "response_mime_type": "application/json",
            "response_schema": list[Additions]
        }

    return get_parsed_list(prompt, llm_config)


# Add all items in a data dict to Homebox
def add_data_to_storage(data: list[dict], auth_key: str) -> dict:
    failed_adds = {}
    for container in data:
        location = container["location"]
        for item in container["items"]:
            item["locationId"] = location
            res = add_item(item, auth_key)
            if not res:
                if location in failed_adds:
                    failed_adds[location].append(item)
                else:
                    failed_adds[location] = [item]

    return failed_adds


def generate_importable_csv(filename: str, data: list[dict]):
    with open(filename, mode="w", newline="") as file:
        fields = ["HB.name", "HB.quantity", "HB.location", "HB.description", "HB.purchase_from", "HB.purchase_price"]
        writer = csv.DictWriter(file, fieldnames=fields)

        writer.writeheader()  # Write column headers

        # Process each location and its items
        for entry in data:
            location = entry["location"]
            for item in entry["items"]:
                item["location"] = location
                writer.writerow({f"HB.{key}": value for key, value in item.items()})

    print(f"Generated file {filename}")


def common_process(filename: str) -> (list[dict], list[str], list[str], str):
    load_dotenv()

    auth = get_homebox_auth_key()
    locations, loc_ids = get_locations(auth)

    print("Locations got!")

    text = interpret_sound_file(filename)

    print(f"Text interpreted as: {text}")

    data = process_with_llm(text, locations)

    print("Formated by LLM!")

    data = check_for_errors_with_header(data, "location", "items")

    print("Data checked for errors!")

    return data, locations, loc_ids, auth


# Add directly to Homebox from sound file
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

    if config.getboolean("ADDER", "output_into_csv"):
        out_name = input("Choose name of output file (without .csv): ")
        csv_from_sound_file(filename, out_name + ".csv")
    else:
        add_from_sound_file(filename)


# Main program function
def main():
    filename = input("Which file should be processed? ")

    process_file(filename)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            process_file(arg)
    else:
        main()

    end_safely(0)
