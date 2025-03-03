from backend.general import config, end_safely
from backend.api_access import get_homebox_auth_key, get_labels, get_all_items, update_item
from backend.llm import get_parsed_list
from backend.error_check import check_for_errors

from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional


class Item(BaseModel):
    id: str
    labels: Optional[list[str]]


def remove_items_with_labels(items: dict) -> dict:
    new_items = {}
    for item in items:
        if not items[item]["labels"]:
            new_items[item] = items[item]
    return new_items


def process_with_llm(items: dict, labels: dict) -> list[dict]:
    items_string = [f"ID: <{key}> Name: {item['name']}: {item['description']}" for key, item in items.items()]
    labels_string = [f"<{labels[label]['name']}> with description {labels[label]['description']}" for label in labels]
    # AI prompt to structure labeling correctly
    prompt = f"""
                The following is a list of items:
                {items_string}
                END OF LIST                
                
                Use the labels in the list below to label the items. 
                Return the ID of the item together with the labels you have assigned to it.
                Only assign the names of the labels, do not include any of the descriptions
                If several labels fit the item, assign several labels to the item.
                If no labels fit the item, assign no labels to the item.
                Make sure to return the ID and label names exactly as they are written. 
                Dont include the < and > for both ID and label name
                Here is the list of labels:
                {labels_string}
                END OF LIST
                """

    llm_config = {
            "response_mime_type": "application/json",
            "response_schema": list[Item]
        }

    return get_parsed_list(prompt, llm_config)


def update_labels(data: list[dict], items: dict, labels: dict, auth: str):
    for labeled in data:
        if "labels" not in labeled:
            continue
        item = items[labeled["id"]]

        if not isinstance(labeled["labels"], list):
            labeled["labels"] = [labeled["labels"]]
        for label in labeled["labels"]:
            if label.startswith("<"):
                label = label[1:-1]
            label_dict = labels[label]
            if label_dict not in item["labels"]:
                item["labels"].append(label_dict)

        if not update_item(auth, item["id"], item):
            print(f"{item['name']} could not have labels added, skipping.")


def label_items():
    load_dotenv()

    auth = get_homebox_auth_key()
    items = get_all_items(auth)
    labels = get_labels(auth)

    if not config.getboolean("LABELER", "label_already_labeled"):
        items = remove_items_with_labels(items)
    print("Got items and labels from Homebox!")

    data = process_with_llm(items, labels)
    for item in data:
        if item["id"].startswith("<"):
            item["id"] = item["id"][1:-1]
        item["name"] = items[item["id"]]["name"]
    print("Processed with LLM!")

    data = check_for_errors(data)
    print("Checked for Errors!")

    update_labels(data, items, labels, auth)
    print("Labeled!")


if __name__ == "__main__":
    label_items()
