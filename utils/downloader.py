import shutil
import sys
from pathlib import Path

import aiohttp
import rarfile

# =========================
# CONSTANTS
# =========================

REPO = "SteamAutoCracks/DepotDownloaderMod"
GITHUB_API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"

RAR_ASSET_NAME = "Release.rar"
EXE_NAME = "DepotDownloaderMod.exe"

INSTALL_DIR_NAME = "DepotDownloaderMod"

CHUNK_SIZE = 64 * 1024


def _get_app_root() -> Path:
    if getattr(sys, "frozen", False):  # PyInstaller or similar
        return Path(sys.executable).resolve().parent

    # __file__ -> .../utils/downloader.py -> project root is parent of parent
    return Path(__file__).resolve().parent.parent


def get_install_dir() -> Path:
    return _get_app_root() / INSTALL_DIR_NAME


def _get_cache_dir() -> Path:
    return _get_app_root() / "cache"


# =========================
# DOWNLOAD
# =========================

async def fetch_latest_release(session: aiohttp.ClientSession) -> dict:
    async with session.get(GITHUB_API_LATEST) as response:
        response.raise_for_status()
        return await response.json()


def find_rar_asset(release: dict) -> dict:
    for asset in release.get("assets", []):
        if asset.get("name") == RAR_ASSET_NAME:
            return asset
    raise RuntimeError("Release.rar not found in latest GitHub release")


async def download_file(
    session: aiohttp.ClientSession,
    url: str,
    output_path: Path,
) -> None:
    async with session.get(url) as response:
        response.raise_for_status()
        with output_path.open("wb") as file:
            async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                file.write(chunk)

async def download_release_rar(cache_dir: Path | None = None) -> tuple[Path, str]:
    cache_dir = cache_dir or _get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        release = await fetch_latest_release(session)
        asset = find_rar_asset(release)

        tag_name = release.get("tag_name", "")
        version = parse_version_from_tag(tag_name)

        rar_path = cache_dir / RAR_ASSET_NAME
        await download_file(session, asset["browser_download_url"], rar_path)

    return rar_path, version

def write_version_file(install_dir: Path, version: str) -> None:
    version_file = install_dir / "version.txt"
    version_file.write_text(version, encoding="utf-8")


def read_installed_version(install_dir: Path) -> str | None:
    """Return installed version from version.txt if present, else None."""

    version_file = install_dir / "version.txt"
    if not version_file.is_file():
        return None

    try:
        content = version_file.read_text(encoding="utf-8").strip()
        return content or None
    except OSError:
        return None


def parse_version_from_tag(tag_name: str) -> str:
    try:
        return tag_name.split("_")[1]
    except IndexError:
        raise ValueError(f"Invalid tag format: {tag_name}")


def prepare_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def extract_rar(rar_path: Path, extract_dir: Path) -> None:
    prepare_directory(extract_dir)

    with rarfile.RarFile(rar_path) as rar:
        rar.extractall(extract_dir)


def find_executable(root: Path, exe_name: str) -> Path:
    for path in root.rglob(exe_name):
        return path
    raise RuntimeError(f"{exe_name} tidak ditemukan di dalam Release.rar")


def copy_install_files(source_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.iterdir():
        destination = target_dir / item.name
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(item, destination)


def install_from_rar(
    rar_path: Path,
    version: str,
) -> Path:
    if not rar_path.is_file():
        raise FileNotFoundError(f"RAR file not found: {rar_path}")

    install_dir = get_install_dir()
    extract_dir = _get_cache_dir() / "_extracted"

    extract_rar(rar_path, extract_dir)

    exe_path = find_executable(extract_dir, EXE_NAME)

    copy_install_files(exe_path.parent, install_dir)

    write_version_file(install_dir, version)

    shutil.rmtree(extract_dir, ignore_errors=True)
    final_exe = install_dir / EXE_NAME
    return final_exe


async def download_and_install() -> Path:
    install_dir = get_install_dir()
    exe_path = install_dir / EXE_NAME

    installed_version = read_installed_version(install_dir)

    cache_dir = _get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        release = await fetch_latest_release(session)

        tag_name = release.get("tag_name", "")
        latest_version = parse_version_from_tag(tag_name)

        # If already installed and up to date, skip re-downloading
        if installed_version == latest_version and exe_path.is_file():
            return exe_path

        asset = find_rar_asset(release)

        rar_path = cache_dir / RAR_ASSET_NAME

        await download_file(session, asset["browser_download_url"], rar_path)
    return install_from_rar(rar_path, latest_version)

# if __name__ == "__main__":
#     asyncio.run(download_and_install())
