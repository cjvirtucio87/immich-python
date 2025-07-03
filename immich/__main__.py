#!/usr/bin/env python3

from immich.lib.immich import Immich
from immich.lib.export import Export
from immich.lib.config import create_config
from immich.lib.http import create_session
from immich.lib.logging import configure_logging, get_logger

import argparse
import re
import yaml
import traceback

LOGGER = get_logger()

def main():
    configure_logging()
    p = argparse.ArgumentParser(description="Download and flatten an Immich album.")
    p.add_argument("--album", "-a", required=True, help="Album name")
    args = p.parse_args()

    config = create_config()
    session = create_session(config.api_key)
    immich = Immich(session, config.instance_url.rstrip("/"))
    errors = []
    album_pattern = re.compile(args.album)
    for album in immich.albums():
        try:
            album_status_code = album.get('statusCode')
            if album_status_code is not None:
                LOGGER.debug("album is: %s", album)
                raise RuntimeError(f"encountered unexpected album album status code {album_status_code}")

            if not album_pattern.match(album.get('albumName', '')):
                continue

            info = immich.download_info(album['id'])
            export = Export(f"downloads/{album['albumName']}")
            album_info = immich.get_album_info(album['id'])

            # dump YAMLs
            with open(export.dir / 'album-info.yaml', 'w') as f:
                yaml.safe_dump(album_info, f)
            with open(export.dir / 'album-archive.yaml', 'w') as f:
                yaml.safe_dump(info, f)

            info_status_code = info.get('statusCode')
            if info_status_code is not None:
                LOGGER.debug("info is: %s", info)
                raise RuntimeError(f"encountered unexpected album info status code {info_status_code}")

            total_mb = info['totalSize'] / 1024 / 1024
            LOGGER.debug("total size: %d MB", total_mb)

            count = 0
            for archive in info.get('archives', []):
                for asset_id in archive.get('assetIds', []):
                    count += 1
                    LOGGER.debug("%d / %d", count, album_info.get('assetCount'))
                    immich.download_archive(
                        asset_id,
                        export.zipped,
                        album_info,
                        export.flatten
                    )
        except Exception as e:
            traceback.print_exc()
            errors.append(e)

    if len(errors) > 0:
        error_messages = [str(error) for error in errors]
        combined_message = "Multiple errors occurred:\n" + "\n".join(f"- {msg}" for msg in error_messages)
        raise RuntimeError(combined_message)


if __name__ == "__main__":
    main()
