"""Fetch Berlin daily weather from Open-Meteo into landing/weather/."""

import json
import os
from pathlib import Path

import requests
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=52.52&longitude=13.41"
    "&start_date=2024-07-01&end_date=2026-06-30"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
)

resp = requests.get(URL, timeout=60)
resp.raise_for_status()
data = resp.json()
print(f"days returned: {len(data['daily']['time'])}")

conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container = BlobServiceClient.from_connection_string(conn).get_container_client("landing")
container.upload_blob(
    name="weather/weather_berlin.json",
    data=json.dumps(data).encode(),
    overwrite=True,
)
print("uploaded to landing/weather/weather_berlin.json")