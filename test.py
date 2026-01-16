from pathlib import Path
import subprocess

exe_dir = Path("DepotDownloaderMod").resolve()
exe_path = exe_dir / "DepotDownloaderMod.exe"

cmd = [
    str(exe_path),
    "-app", "294100",
    "-pubfile", "2222935097",
]

subprocess.Popen(
    cmd,
    cwd=exe_dir
)
