import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session(api_key: str):
    session = requests.Session()
    session.headers.update(
        {
            "x-api-key": api_key,
            "Accept": "application/json",
        }
    )
    retry_cfg = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={"POST"},  # Immich’s endpoint is POST but idempotent
    )
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=retry_cfg,
        ),
    )

    return session
