from __future__ import annotations

import argparse
import base64
import os
import sys
import zipfile
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError


DEFAULT_DATASET = "wanmugui/childrens-dental-panoramic-x-ray-dataset"
DEFAULT_OUTPUT_DIR = Path("datasets")
CHUNK_SIZE = 1024 * 1024


def get_env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value

    if sys.platform != "win32":
        return None

    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            registry_value, _ = winreg.QueryValueEx(key, name)
            return str(registry_value) if registry_value else None
    except OSError:
        return None


def build_kaggle_url(slug: str) -> str:
    return f"https://www.kaggle.com/api/v1/datasets/download/{slug.strip('/')}"


def build_request(url: str, *, kaggle: bool) -> request.Request:
    headers = {"User-Agent": "Wisdom-Tooth-AI-Dataset-Downloader/1.0"}
    if kaggle:
        username = get_env_value("KAGGLE_USERNAME")
        key = get_env_value("KAGGLE_KEY")
        if not username or not key:
            raise SystemExit(
                "Kaggle credentials missing. Set KAGGLE_USERNAME and KAGGLE_KEY, "
                "or pass --url with a public direct zip URL."
            )
        token = base64.b64encode(f"{username}:{key}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    return request.Request(url, headers=headers)


def download(url: str, target: Path, *, kaggle: bool, overwrite: bool) -> Path:
    if target.exists() and not overwrite:
        print(f"Already exists: {target}")
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    temp_target = target.with_suffix(target.suffix + ".part")
    req = build_request(url, kaggle=kaggle)

    try:
        with request.urlopen(req, timeout=120) as response:
            total_header = response.headers.get("Content-Length")
            total = int(total_header) if total_header and total_header.isdigit() else None
            downloaded = 0
            with temp_target.open("wb") as file:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    file.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        percent = downloaded * 100 / total
                        print(f"\rDownloading: {downloaded / 1024 / 1024:.1f} MB / {total / 1024 / 1024:.1f} MB ({percent:.1f}%)", end="")
                    else:
                        print(f"\rDownloading: {downloaded / 1024 / 1024:.1f} MB", end="")
            print()
    except HTTPError as exc:
        if temp_target.exists():
            temp_target.unlink()
        raise SystemExit(f"Download failed: HTTP {exc.code} {exc.reason}") from exc
    except URLError as exc:
        if temp_target.exists():
            temp_target.unlink()
        raise SystemExit(f"Download failed: {exc.reason}") from exc

    temp_target.replace(target)
    print(f"Saved: {target}")
    return target


def extract_zip(zip_path: Path, extract_dir: Path, *, overwrite: bool) -> None:
    if extract_dir.exists() and any(extract_dir.iterdir()) and not overwrite:
        print(f"Extract directory already has files: {extract_dir}")
        return
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)
    print(f"Extracted: {extract_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download dental datasets into the local datasets/ folder.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--kaggle", default=DEFAULT_DATASET, help=f"Kaggle dataset slug. Default: {DEFAULT_DATASET}")
    source.add_argument("--url", help="Public direct zip URL.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--filename", default="childrens-dental-panoramic-x-ray-dataset.zip")
    parser.add_argument("--extract", action="store_true", help="Extract the downloaded zip after download.")
    parser.add_argument("--extract-dir", type=Path, help="Directory to extract into. Use a short path on Windows.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing zip/extracted folder.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.url:
        url = args.url
        kaggle = False
    else:
        url = build_kaggle_url(args.kaggle)
        kaggle = True

    zip_path = args.output_dir / "raw" / args.filename
    downloaded = download(url, zip_path, kaggle=kaggle, overwrite=args.overwrite)

    if args.extract:
        extract_dir = args.extract_dir or args.output_dir / "extracted" / "children_xray"
        extract_zip(downloaded, extract_dir, overwrite=args.overwrite)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
