"""
upload_to_landing.py  --  PriceScope

Uploads the locally generated dataset into the ADLS Gen2 `landing` container,
mirroring the folder structure the "source systems" would drop files in.

    data/master/*.csv         ->  landing/master/*.csv
    data/sales/*.csv          ->  landing/sales/*.csv
    data/competitor/*.json    ->  landing/competitor/*.json

Landing is deliberately flat and untouched: no partitioning, no format change,
no renaming. Whatever the source produced is what lands. All structure is
introduced later, in raw/, by the ADF pipelines.

Requires in .env:
    AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

Install:
    pip install azure-storage-blob python-dotenv
"""

import os
import sys
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

CONTAINER = "landing"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# local subfolder -> glob pattern
SOURCES = {
    "master": "*.csv",
    "sales": "*.csv",
    "competitor": "*.json",
}


def human(nbytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def main(overwrite: bool = False) -> None:
    conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn:
        sys.exit("AZURE_STORAGE_CONNECTION_STRING missing from .env")

    if not DATA_DIR.exists():
        sys.exit(f"data directory not found: {DATA_DIR}")

    service = BlobServiceClient.from_connection_string(conn)
    container = service.get_container_client(CONTAINER)

    existing = {b.name for b in container.list_blobs()}
    uploaded = skipped = 0
    total_bytes = 0

    for folder, pattern in SOURCES.items():
        local_dir = DATA_DIR / folder
        if not local_dir.exists():
            print(f"[warn] {local_dir} does not exist, skipping")
            continue

        for path in sorted(local_dir.glob(pattern)):
            blob_name = f"{folder}/{path.name}"

            if blob_name in existing and not overwrite:
                print(f"[skip] {blob_name}")
                skipped += 1
                continue

            size = path.stat().st_size
            print(f"[up  ] {blob_name}  ({human(size)})", flush=True)
            with path.open("rb") as fh:
                container.upload_blob(name=blob_name, data=fh, overwrite=True)
            uploaded += 1
            total_bytes += size

    print(
        f"\ndone: {uploaded} uploaded ({human(total_bytes)}), "
        f"{skipped} skipped, container={CONTAINER}"
    )


if __name__ == "__main__":
    main(overwrite="--overwrite" in sys.argv)
