#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yaml
import zipfile
import shutil
from pathlib import Path
import time

class Immich:
    def __init__(self):
        # Load config from ~/.config/immich/auth.yml
        cfg_path = Path.home() / ".config" / "immich" / "auth.yml"
        with open(cfg_path, 'r') as f:
            config = yaml.safe_load(f)
        self.key = config['apiKey']
        self.host = config['instanceUrl'].rstrip('/')
        # persistent session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.key,
            "Accept": "application/json",
        })
        retry_cfg = Retry(
          total=5,
          connect=5,
          read=5,
          backoff_factor=2,
          status_forcelist=[500, 502, 503, 504],
          allowed_methods={"POST"},   # Immich’s endpoint is POST but idempotent
        )
        self.session.mount(
            "https://",
            HTTPAdapter(
              max_retries=retry_cfg,
            ),
        )
        self.session.mount(
            "http://",
            HTTPAdapter(
              max_retries=retry_cfg,
            ),
        )

    def download_info(self, album_id):
        url = f"{self.host}/api/download/info"
        resp = self.session.post(url, json={"albumId": album_id})
        resp.raise_for_status()
        return resp.json()

    def download_archive(self, asset_id, zipped_dir: Path, album_info: dict, flatten_dir: Path):
        zipped_dir.mkdir(parents=True, exist_ok=True)
        unzipped_dir = zipped_dir.parent / "unzipped" / asset_id
        unzipped_dir.mkdir(parents=True, exist_ok=True)

        out_zip = zipped_dir / f"{asset_id}.zip"
        if not out_zip.exists():
            print(f"Downloading {asset_id}")
            url = f"{self.host}/api/download/archive"
            # override Accept for binary
            headers = {"Accept": "application/octet-stream"}
            resp = self.session.post(url, json={"assetIds": [asset_id]}, headers=headers, stream=True, timeout=(5, 20))
            resp.raise_for_status()
            with open(out_zip, "wb") as fd:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fd.write(chunk)

        # extract
        with zipfile.ZipFile(out_zip, 'r') as z:
            z.extractall(unzipped_dir)

        files = list(unzipped_dir.iterdir())
        print(f"children {len(files)} {asset_id}")

        # build lookup tables
        date_time = {
            a['id']: a['exifInfo']['dateTimeOriginal']
            for a in album_info.get('assets', [])
            if 'exifInfo' in a and 'dateTimeOriginal' in a['exifInfo']
        }
        exif = {a['id']: a for a in album_info.get('assets', [])}

        # move/flatten files
        flatten_dir.mkdir(parents=True, exist_ok=True)
        for entry in files:
            dt = date_time.get(asset_id)
            if dt:
                dest = flatten_dir / (dt + entry.suffix.lower())
                entry.replace(dest)
            else:
                # no exif date for this asset
                print(exif.get(asset_id))

    def get_album_info(self, album_id):
        url = f"{self.host}/api/albums/{album_id}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def albums(self):
        url = f"{self.host}/api/albums"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

class Export:
    def __init__(self, base_dir):
        self.base = Path(base_dir)
        # zipped, unzipped, flatten subdirs
        (self.base / "zipped").mkdir(parents=True, exist_ok=True)
        (self.base / "unzipped").mkdir(parents=True, exist_ok=True)
        (self.base / "flatten").mkdir(parents=True, exist_ok=True)

    @property
    def dir(self):
        return self.base

    @property
    def zipped(self):
        return self.base / "zipped"

    @property
    def unzipped(self):
        return self.base / "unzipped"

    @property
    def flatten(self):
        return self.base / "flatten"

def main():
    p = argparse.ArgumentParser(description="Download and flatten an Immich album.")
    p.add_argument("--album", "-a", required=True, help="Album name")
    args = p.parse_args()

    immich = Immich()
    for album in immich.albums():
        # skip errored albums
        if album.get('statusCode') is not None:
            continue
        if album.get('albumName') != args.album:
            continue

        info = immich.download_info(album['id'])
        export = Export(f"downloads/{album['albumName']}")
        album_info = immich.get_album_info(album['id'])

        # dump YAMLs
        with open(export.dir / 'album-info.yaml', 'w') as f:
            yaml.safe_dump(album_info, f)
        with open(export.dir / 'album-archive.yaml', 'w') as f:
            yaml.safe_dump(info, f)

        if info.get('statusCode') is None:
            total_mb = info['totalSize'] / 1024 / 1024
            print(f"{total_mb:.2f} MB")

            count = 0
            for archive in info.get('archives', []):
                for asset_id in archive.get('assetIds', []):
                    count += 1
                    print(f"{count} / {album_info.get('assetCount')}")
                    immich.download_archive(
                        asset_id,
                        export.zipped,
                        album_info,
                        export.flatten
                    )
        else:
            print(info)

if __name__ == "__main__":
    main()
