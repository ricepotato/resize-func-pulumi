
import json

def resize_image(event: dict, context: dict):
    print("Received event: ")
    print(json.dumps(event, indent=2))