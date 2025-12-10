import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import List
from sylph_tax.version import __version__
from sylph_tax.metadata_files import __metadata_file_urls__

class SylphTaxDownloader:
    def __init__(self, db_location):
        if db_location == "NONE":
            self.taxonomy_location = None
        else:
            self.taxonomy_location = db_location

    def download_file(self, url: str) -> Path:
        """Download a file from Zenodo with simple progress reporting."""
        filename = url.split('/')[-1]
        output_path = Path(self.taxonomy_location) / filename

        print(f"Downloading {filename}...")

        try:
            urllib.request.urlretrieve(
                url, 
                output_path,
                lambda count, block_size, total_size: print(
                    f"\rProgress: {count * block_size * 100 / total_size:.1f}%",
                    end=''
                )
            )
            print("\nDownload complete!")
            return output_path

        except Exception as e:
            print(f"\nError downloading {filename}: {e}", file=sys.stderr)
            if output_path.exists():
                output_path.unlink()
            raise

    def download_taxonomy(self, urls: List[str]) -> List[Path]:
        """Download multiple files from a list of URLs."""
        downloaded_paths = []
        for url in urls:
            path = self.download_file(url)
            downloaded_paths.append(path)
        return downloaded_paths

def main(args, config):

    if config == None and not args.no_config:
        env_var = os.getenv('SYLPH_TAXONOMY_CONFIG')
        print(f"ERROR: Could not load config file at {env_var} -- 'sylph-tax download' will not attempt to download taxonomy metadata files. Please manually download taxonomy metadata files yourself. Exiting")
        exit(1)

    if config.json['taxonomy_dir'] == "NONE":
        print("DOWNLOAD: Taxonomy metadata file directory has not been set.")
    else:
        print(f"DOWNLOAD: Current taxonomy location is set to {config.json['taxonomy_dir']}.")

    if args.download_to != None:
        os.makedirs(args.download_to, exist_ok=True)
        if config != None:
            config.set_taxonomy_dir(args.download_to)
        downloader = SylphTaxDownloader(args.download_to)
        downloader.download_taxonomy(__metadata_file_urls__)
        print(f"DOWNLOAD: Taxonomy metadata files have been downloaded to {args.download_to}.")
        print(f"DOWNLOAD: {config.config_location} has been updated with the new taxonomy directory.")
    else:
        print("DOWNLOAD: No download directory specified. Please specify a directory using the --download-to option.")
