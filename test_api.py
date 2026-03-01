import requests
import json

url = "http://127.0.0.1:8000/analyze"

# Only the corners are needed in the text payload now
payload = {
    'corners_json': json.dumps([[906, 1577], [1267, 1572], [2112, 2374], [85, 2406]])
}

# Open your test video (make sure this file exists in your folder!)
try:
    with open('IMG_6192.mov', 'rb') as f:
        files = {'video': f}

        print("Sending request to API...")
        response = requests.post(url, data=payload, files=files)

    # Print the result
    if response.status_code == 200:
        print("--- SUCCESS ---")
        print(json.dumps(response.json(), indent=4))
    else:
        print(f"--- ERROR {response.status_code} ---")
        print(response.text)

except FileNotFoundError:
    print("Error: Could not find 'test_ball.mov' in this folder.")