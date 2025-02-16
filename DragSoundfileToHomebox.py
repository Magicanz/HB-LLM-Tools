import sys
import os

from adder import add_from_sound_file


def process_file(file_path):
    if not os.path.exists(file_path):
        print("Error: File does not exist.")
        return

    print(f"Processing file: {file_path}")

    add_from_sound_file(file_path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            process_file(arg)
    else:
        print("No file provided. Drag and drop a file onto this script.")