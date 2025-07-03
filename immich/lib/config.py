from pathlib import Path
from dataclasses import dataclass
import yaml

CFG_PATH = Path.home() / ".config" / "immich" / "auth.yml"


@dataclass
class Config:
    api_key: str
    instance_url: str


def create_config(cfg_path: Path = CFG_PATH) -> Config:
    """Create a Config instance from a YAML configuration file."""
    with open(cfg_path, "r") as f:
        config_data = yaml.safe_load(f)

    return Config(
        api_key=config_data["apiKey"], instance_url=config_data["instanceUrl"]
    )
