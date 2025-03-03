import os
import requests


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


# Get all labels from Homebox instance and return as list with names as keys
def get_labels(auth_key: str) -> dict:
    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/labels"
    headers = {"Authorization": f"{auth_key}", "Accept": "application/json"}
    res = requests.get(url, headers=headers)

    res_dict = res.json()
    return_dict = {}

    for label in res_dict:
        return_dict[label["name"]] = label

    return return_dict


# Get all items in Homebox storage into a dict with ID as key
def get_all_items(auth_key: str) -> dict:
    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/items"
    headers = {"Authorization": f"{auth_key}", "Accept": "application/json"}
    res = requests.get(url, headers=headers)

    res_dict = res.json()
    return_dict = {}

    for item in res_dict["items"]:
        return_dict[item["id"]] = item

    return return_dict


# Add an item to Homebox using the Homebox API
def add_item(item: dict, auth_key: str) -> bool:
    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/items"
    headers = {"Authorization": f"{auth_key}", "Accept": "application/json", "Content-Type": "application/json"}
    data = {key: value for key, value in item.items()}

    res = requests.post(url, headers=headers, json=data)

    if res.status_code == 201:
        return True
    return False


# This replaces the item! Remember to submit with gotten data, not just the patched data.
def update_item(auth_key: str, item_id: str, item_data: dict) -> bool:
    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/items/{item_id}"
    headers = {"Authorization": f"{auth_key}", "Accept": "application/json", "Content-Type": "application/json"}

    item_data["locationId"] = item_data["location"]["id"]
    item_data["labelIds"] = []
    for label in item_data.get("labels", []):
        item_data["labelIds"].append(label["id"])

    if "parent" in item_data:
        item_data["parentId"] = item_data["parent"]["id"]
    else:
        item_data["parentId"] = None

    res = requests.put(url, headers=headers, json=item_data)

    if res.status_code == 200:
        return True
    return False
