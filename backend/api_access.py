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


# Add an item to Homebox using the Homebox API
def add_item(item: dict, auth_key: str) -> bool:
    url = f"{os.getenv('HOMEBOX_URL')}/api/v1/items"
    headers = {"Authorization": f"{auth_key}", "Accept": "application/json", "Content-Type": "application/json"}
    data = {key: value for key, value in item.items()}

    res = requests.post(url, headers=headers, json=data)

    if res.status_code == 201:
        return True
    return False
