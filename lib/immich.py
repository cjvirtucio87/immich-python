import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pathlib import Path

import yaml

import zipfile

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
