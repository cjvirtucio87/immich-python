#!/usr/bin/env python3

from lib.immich import Immich

from pathlib import Path

import argparse
import yaml

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
