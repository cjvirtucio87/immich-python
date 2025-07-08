
import requests


class ImmichClient:

    def __init__(self, base_url: str, session: requests.Session):
        self._base_url = base_url
        self._session = session

    @property
    def session(self):
        return self._session

    @property
    def base_url(self):
        return self._base_url

    def get_albums(self):
        url = f"{self.base_url}/api/albums"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_album_info(self, album_id):
        url = f"{self.base_url}/api/albums/{album_id}"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_download_info(self, album_id):
        url = f"{self.base_url}/api/download/info"
        resp = self.session.post(url, json={"albumId": album_id})
        resp.raise_for_status()
        return resp.json()

    def get_asset_file_object(self, asset_id: str, dst_file_object):
        url = f"{self.base_url}/api/download/archive"
        # override Accept for binary
        headers = {"Accept": "application/octet-stream"}
        resp = self.session.post(
            url,
            json={"assetIds": [asset_id]},
            headers=headers,
            stream=True,
            timeout=(5, 20),
        )
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                dst_file_object.write(chunk)
