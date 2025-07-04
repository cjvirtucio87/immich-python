import tempfile
import shutil
import os
from pathlib import Path
from typing import Optional


class StagingArea:

    def __init__(self, tmp_dir: Optional[str] = None) -> None:
        self._tmp_dir = tmp_dir
        self._should_cleanup = False
        self._path: Optional[Path] = None

    def __enter__(self) -> 'StagingArea':
        if self._tmp_dir is None:
            # Create a temporary directory and mark it for cleanup
            self._tmp_dir = tempfile.mkdtemp()
            self._should_cleanup = True

        self._path = Path(self._tmp_dir)

        # Create the directory if it doesn't exist
        if not self._path.exists():
            self._path.mkdir(parents=True, exist_ok=True)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._should_cleanup and self._path and self._path.exists():
            shutil.rmtree(str(self._path))

    @property
    def path(self) -> Path:
        """Get the path of the staging area."""
        if self._path is None:
            raise RuntimeError("StagingArea must be used as a context manager")
        return self._path

    def add(self, source: str, destination: Optional[str] = None) -> Path:
        """Add a file or directory to the staging area."""
        if self._path is None:
            raise RuntimeError("StagingArea must be used as a context manager")

        source_path = Path(source)
        if destination is None:
            dest_path = self._path / source_path.name
        else:
            dest_path = self._path / destination

        # Create parent directories if they don't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.is_file():
            shutil.copy2(source, dest_path)
        elif source_path.is_dir():
            shutil.copytree(source, dest_path, dirs_exist_ok=True)
        else:
            raise ValueError(f"Source '{source}' is not a file or directory")

        return dest_path

    def get_path(self, filepath: str) -> Path:
        """Get the absolute path to a file or directory within the staging area.

        Args:
            filepath: Relative path to the file or directory within the staging area

        Returns:
            Absolute path to the file or directory within the staging area
        """
        if self._path is None:
            raise RuntimeError("StagingArea must be used as a context manager")

        return self._path / filepath

    def sync(self, src: str, dst: str) -> None:
        """Sync a directory from the staging area to a destination directory.

        Args:
            src: Relative path within the staging area to the source directory
            dst: Destination path (absolute or relative to current working directory)
        """
        if self._path is None:
            raise RuntimeError("StagingArea must be used as a context manager")

        source_path = self._path / src

        # Convert dst to absolute path if it's relative
        dst_path = Path(dst)
        if not dst_path.is_absolute():
            dst_path = Path.cwd() / dst_path

        # Check if source exists
        if not source_path.exists():
            raise ValueError(f"Source directory '{src}' does not exist in staging area")

        if not source_path.is_dir():
            raise ValueError(f"Source '{src}' is not a directory")

        # Create destination directory if it doesn't exist
        dst_path.mkdir(parents=True, exist_ok=True)

        # Copy the contents of the source directory to the destination
        shutil.copytree(source_path, dst_path, dirs_exist_ok=True)

