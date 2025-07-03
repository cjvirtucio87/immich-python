#!/usr/bin/env python3

from immich.lib.immich import Immich
from immich.lib.config import create_config
from immich.lib.http import create_session
from immich.lib.logging import configure_logging, get_logger

import argparse

LOGGER = get_logger()


def main():
    configure_logging()
    p = argparse.ArgumentParser(description="Download and flatten an Immich album.")
    p.add_argument("--album", "-a", required=True, help="Album name")
    args = p.parse_args()

    config = create_config()
    session = create_session(config.api_key)
    immich = Immich(session, config.instance_url.rstrip("/"))
    errors = immich.download_albums(args.album)

    if len(errors) > 0:
        error_messages = [str(error) for error in errors]
        combined_message = "Multiple errors occurred:\n" + "\n".join(
            f"- {msg}" for msg in error_messages
        )
        raise RuntimeError(combined_message)


if __name__ == "__main__":
    main()
