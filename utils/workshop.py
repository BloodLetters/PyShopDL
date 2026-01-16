from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import subprocess

from . import downloader as depot_downloader


@dataclass
class WorkshopJob:
    """Represents a single Workshop download request."""

    app_id: str
    pubfile_id: str


class WorkshopDownloader:
    """Run DepotDownloaderMod.exe to download Steam Workshop content.

    This class is UI-agnostic and only knows how to build and execute the
    DepotDownloaderMod command-line for a given Workshop job.
    """

    def __init__(self, exe_dir: Optional[Path] = None) -> None:
        if exe_dir is None:
            project_root = Path(__file__).resolve().parent.parent
            exe_dir = project_root / depot_downloader.INSTALL_DIR_NAME

        self.exe_dir = exe_dir
        self.exe_path = self.exe_dir / depot_downloader.EXE_NAME

    def build_command(self, job: WorkshopJob) -> list[str]:
        """Build the command-line for DepotDownloaderMod for a given job."""

        return [
            str(self.exe_path),
            "-app",
            job.app_id,
            "-pubfile",
            job.pubfile_id,
        ]

    def run_job(self, job: WorkshopJob) -> subprocess.Popen:
        """Start DepotDownloaderMod for the given job and return the process.

        The caller is responsible for reading stdout/stderr and waiting for
        completion.
        """

        cmd = self.build_command(job)

        proc = subprocess.Popen(
            cmd,
            cwd=self.exe_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        return proc
