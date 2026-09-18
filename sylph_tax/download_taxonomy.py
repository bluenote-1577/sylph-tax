import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List
from sylph_tax.version import __version__
from sylph_tax.metadata_files import __metadata_file_urls__


def format_size(num_bytes: float) -> str:
    """Format a byte count as a human-readable string (e.g. '12.3 MB')."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} GB"


class SylphTaxDownloader:
    def __init__(self, db_location):
        if db_location == "NONE":
            self.taxonomy_location = None
        else:
            self.taxonomy_location = db_location

    def download_file(self, url: str) -> Path:
        """Download a file from Zenodo."""
        filename = url.split("/")[-1]
        output_path = Path(self.taxonomy_location) / filename
        reported_size = {}

        def report_size(count, block_size, total_size):
            # Fires on every chunk; only print once we know the total size.
            if total_size > 0 and "printed" not in reported_size:
                reported_size["printed"] = True
                print(f"Downloading {filename} ({format_size(total_size)})...")

        try:
            urllib.request.urlretrieve(url, output_path, report_size)
            final_size = output_path.stat().st_size
            print(f"Finished downloading {filename} ({format_size(final_size)}).")
            return output_path

        except Exception as e:
            print(f"Error downloading {filename}: {e}", file=sys.stderr)
            if output_path.exists():
                output_path.unlink()
            raise

    def download_taxonomy(self, urls: List[str], threads: int = 5) -> List[Path]:
        """Download multiple files from a list of URLs in parallel."""
        print(f"Downloading {len(urls)} file(s) using {threads} thread(s)...")
        with ThreadPoolExecutor(max_workers=threads) as executor:
            downloaded_paths = list(executor.map(self.download_file, urls))
        print("All downloads complete.")
        return downloaded_paths


def main(args, config):
    # Determine download destination with precedence: --download-to > --taxonomy-dir
    download_dest = None
    if args.download_to is not None:
        download_dest = args.download_to
    elif hasattr(args, "taxonomy_dir") and args.taxonomy_dir is not None:
        download_dest = args.taxonomy_dir

    # When --no-config is set, we need a download destination
    if config is None:
        if download_dest is None:
            print(
                "ERROR: --taxonomy-dir is required when --no-config is set. Please specify a directory using --taxonomy-dir or --download-to."
            )
            exit(1)
        # download without config
        os.makedirs(download_dest, exist_ok=True)
        downloader = SylphTaxDownloader(download_dest)
        downloader.download_taxonomy(__metadata_file_urls__, threads=args.threads)
        print(
            f"DOWNLOAD: Taxonomy metadata files have been downloaded to {download_dest}."
        )
        return

    # Standard mode with config
    if config.json["taxonomy_dir"] == "NONE":
        print("DOWNLOAD: Taxonomy metadata file directory has not been set.")
    else:
        print(
            f"DOWNLOAD: Current taxonomy location is set to {config.json['taxonomy_dir']}."
        )

    if download_dest is not None:
        os.makedirs(download_dest, exist_ok=True)
        config.set_taxonomy_dir(download_dest)
        downloader = SylphTaxDownloader(download_dest)
        downloader.download_taxonomy(__metadata_file_urls__, threads=args.threads)
        print(
            f"DOWNLOAD: Taxonomy metadata files have been downloaded to {download_dest}."
        )
        print(
            f"DOWNLOAD: {config.config_location} has been updated with the new taxonomy directory."
        )
    else:
        print(
            "DOWNLOAD: No download directory specified. Please specify a directory using the --download-to option."
        )
