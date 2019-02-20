import requests
from requests import exceptions
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import argparse
import cv2
import os
import re

ap = argparse.ArgumentParser();
ap.add_argument("-q", "--query", required=True, help="search query to search Bing Image API for")
ap.add_argument("-o", "--output", required=True, help="path to output directory")

args = ap.parse_args()

subscription_key = "9e0ec10bdc6541f993e35ffb0d2ecad6"
search_url = "https://api.cognitive.microsoft.com/bing/v7.0/images/search"
MAX_RESULTS = 1000
BATCH_SIZE = 50
BUFFER = 2

print("[INFO] MAX_RESULTS set to {}".format(MAX_RESULTS))
print("[INFO] BUFFER set to {}".format(BUFFER))
print("[INFO] BATCH_SIZE set to {}".format(BATCH_SIZE))
print("[INFO] Using query {}".format(args.query))
print("[INFO] Using output {}".format(args.output))

headers = {"Ocp-Apim-Subscription-Key": subscription_key}
params = {"q": args.query, "license": "public", "imageType": "photo"}

search = requests.get(search_url, headers=headers, params=params)
search.raise_for_status()
response_json = search.json()
check = set()

estNumResults = min(response_json["totalEstimatedMatches"], MAX_RESULTS)

ALLOWED_EXCEPTIONS = set([
    IOError,
    # FileNotFoundError,
    exceptions.RequestException,
    exceptions.HTTPError,
    exceptions.ConnectionError,
    exceptions.Timeout
])

ext_regex = re.compile(r"(\.[a-z]+)(\?.+)?")

def loop():
    total = 0
    for offset in range(0, estNumResults, BATCH_SIZE):
        print("[INFO] Iterating over results {} to {} of {}.".format(offset + 1, min(offset + BATCH_SIZE, estNumResults), estNumResults))
        params["offset"] = offset
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()

        for result in results["value"]:
            try:
                img = requests.get(result["contentUrl"], timeout=30)
                raw_ext = result["contentUrl"][result["contentUrl"].rfind("."):]
                matches = ext_regex.match(raw_ext)
                ext = matches.group(1) if matches is not None else ""
                p = os.path.sep.join([args.output, "{}{}".format(str(total).zfill(8), ext)])
                with open(p, "wb") as f:
                    f.write(img.content)
                image = cv2.imread(p)
                if image is None or img.content in check:
                    os.remove(p)
                    continue
                print("[INFO] Saved {}".format(p))
                total += 1
                check.add(img.content)
            except Exception as e:
                if type(e) in ALLOWED_EXCEPTIONS:
                    continue
                else:
                    raise e

loop()
