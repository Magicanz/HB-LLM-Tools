import os
import re
import subprocess
from typing import TextIO

TEMP_FILE = "temp"
PROPERTY_ORDER = ["id", "quantity", "name", "description", "purchaseFrom", "purchasePrice", "labels"]
LOAD_PATTERN = r"::(\w+)::\s*(.*?)(?=\s+::|\s*$)"


def write_to_file_inner(file: TextIO, item: dict):
    for prop in PROPERTY_ORDER:
        if prop in item and item[prop]:
            if isinstance(item[prop], list) :
                for list_item in item[prop]:
                    file.write(f"::{prop}:: {list_item} ")
            else:
                file.write(f"::{prop}:: {item[prop]} ")
    file.write("\n")


def write_to_file(filename: str, data: list[dict]):
    with open(filename, 'w') as file:
        file.write("# Use this file to fix any errors made by the AI\n")

        for item in data:
            write_to_file_inner(file, item)


# Write data to file for error check, with header
def write_to_file_with_header(filename: str, data: list[dict],
                              header_name: str = "location", entry_name: str = "items"):

    with open(filename, 'w') as file:

        file.write("""# Use this file to fix any errors made by the AI
# If location is <error>, make sure to assign a correct location!
# eg 'Kitchen' or 'Storage Room/Shelf 1/Box 4'.
""")

        for entry in data:
            file.write(f"<{entry[header_name]}>\n")
            for item in entry[entry_name]:
                write_to_file_inner(file, item)


# Load after file editing is complete
def load_from_file(filename: str) -> list[dict]:
    updated_data = []

    with open(filename, 'r') as file:
        lines = file.readlines()

        for line in lines:
            line = line.strip()
            if "::" in line:
                matches = re.findall(LOAD_PATTERN, line)
                res_dict = {}
                for key, value in matches:
                    if key in res_dict:
                        if isinstance(res_dict[key], list):
                            res_dict[key].append(value)
                        else:
                            res_dict[key] = [res_dict[key], value]
                    else:
                        res_dict[key] = value
                updated_data.append(res_dict)

    return updated_data


# Load after file editing is complete, with header
def load_from_file_with_header(filename: str, header_name: str = "location", entry_name: str = "items") -> list[dict]:
    updated_data = []
    current_header = None
    current_entries = []

    with open(filename, 'r') as file:
        lines = file.readlines()

        for line in lines:
            line = line.strip()
            if "::" in line:
                matches = re.findall(LOAD_PATTERN, line)
                res_dict = {}
                for key, value in matches:
                    if key in res_dict:
                        if isinstance(res_dict[key], list):
                            res_dict[key].append(value)
                        else:
                            res_dict[key] = [res_dict[key], value]
                    else:
                        res_dict[key] = value
                current_entries.append(res_dict)
            elif line.startswith('<') and line.endswith('>'):
                if current_header:
                    updated_data.append({header_name: current_header, entry_name: current_entries})

                current_header = line[1:-1]  # Strip the < and >
                current_entries = []

        if current_header:
            updated_data.append({header_name: current_header, entry_name: current_entries})

    return updated_data


# Open in editor for error check
def open_in_editor(filename: str):
    if os.name == 'posix':  # For macOS/Linux
        subprocess.run(['open', filename])
    elif os.name == 'nt':  # For Windows
        subprocess.run(['notepad', filename])


def check_for_errors(data: list[dict]):
    write_to_file(TEMP_FILE, data)

    open_in_editor(TEMP_FILE)

    return load_from_file(TEMP_FILE)


def check_for_errors_with_header(data: list[dict], header_name, entry_name) -> list[dict]:
    write_to_file_with_header(TEMP_FILE, data, header_name, entry_name)

    open_in_editor(TEMP_FILE)

    return load_from_file_with_header(TEMP_FILE, header_name, entry_name)