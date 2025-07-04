from pathlib import Path

import re
import yaml
import traceback

import zipfile
from immich.lib.clients.immich import ImmichClient
from immich.lib.export import Export
from immich.lib.fs import StagingArea
import immich.lib.logging as immich_logging

LOGGER = immich_logging.get_logger()


class Immich:
    def __init__(self, staging_area: StagingArea, immich_client: ImmichClient):
        self._staging_area = staging_area
        self._immich_client = immich_client

    def download_albums(self, album_pattern: str) -> list:
        errors = []
        compiled_album_pattern = re.compile(album_pattern)
        for album in self._immich_client.get_albums():
            try:
                album_status_code = album.get("statusCode")
                if album_status_code is not None:
                    LOGGER.debug("album is: %s", album)
                    raise RuntimeError(
                        f"encountered unexpected album album status code {album_status_code}"
                    )

                if not compiled_album_pattern.match(album.get("albumName", "")):
                    continue

                info = self._immich_client.get_download_info(album["id"])
                album_info = self._immich_client.get_album_info(album["id"])

                album_dir_path = f"downloads/{album['albumName']}"
                Path(self._staging_area.get_path(album_dir_path)).mkdir(parents=True, exist_ok=True)

                # dump YAMLs
                album_info_dest_path = self._staging_area.get_path(f"{album_dir_path}/album-info.yaml")
                with open(album_info_dest_path, "w") as f:
                    yaml.safe_dump(album_info, f)

                album_archive_dest_path = self._staging_area.get_path(f"{album_dir_path}/album-archive.yaml")
                with open(album_archive_dest_path, "w") as f:
                    yaml.safe_dump(info, f)

                info_status_code = info.get("statusCode")
                if info_status_code is not None:
                    LOGGER.debug("info is: %s", info)
                    raise RuntimeError(
                        f"encountered unexpected album info status code {info_status_code}"
                    )

                total_mb = info["totalSize"] / 1024 / 1024
                LOGGER.debug("total size: %d MB", total_mb)


                staging_area_album_dir_path = self._staging_area.get_path(album_dir_path)
                export = Export(staging_area_album_dir_path)
                count = 0
                for archive in info.get("archives", []):
                    for asset_id in archive.get("assetIds", []):
                        count += 1
                        LOGGER.debug("%d / %d", count, album_info.get("assetCount"))
                        self._download_archive(
                            asset_id, export.zipped, album_info, export.flatten
                        )

                self._staging_area.sync(album_dir_path, album_dir_path)
            except Exception as e:
                traceback.print_exc()
                errors.append(e)

        return errors

    def _download_archive(
        self, asset_id, zipped_dir: Path, album_info: dict, flatten_dir: Path
    ):
        zipped_dir.mkdir(parents=True, exist_ok=True)
        unzipped_dir = zipped_dir.parent / "unzipped" / asset_id
        unzipped_dir.mkdir(parents=True, exist_ok=True)

        out_zip = zipped_dir / f"{asset_id}.zip"
        if not out_zip.exists():
            LOGGER.info("Downloading %s", asset_id)
            with open(out_zip, "wb") as fd:
                self._immich_client.get_asset_file_object(asset_id, fd)

        # extract
        with zipfile.ZipFile(out_zip, "r") as z:
            z.extractall(unzipped_dir)

        files = list(unzipped_dir.iterdir())
        LOGGER.info("children %s %s", len(files), asset_id)

        # build lookup tables
        date_time = {
            a["id"]: a["exifInfo"]["dateTimeOriginal"]
            for a in album_info.get("assets", [])
            if "exifInfo" in a and "dateTimeOriginal" in a["exifInfo"]
        }
        exif = {a["id"]: a for a in album_info.get("assets", [])}

        # move/flatten files
        flatten_dir.mkdir(parents=True, exist_ok=True)
        for entry in files:
            dt = date_time.get(asset_id)
            if dt:
                dest = flatten_dir / (dt + entry.suffix.lower())
                entry.replace(dest)
            else:
                # no exif date for this asset
                LOGGER.info(exif.get(asset_id))
