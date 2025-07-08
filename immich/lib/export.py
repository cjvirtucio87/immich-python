from pathlib import Path


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
