from unittest import TestCase, main
from unittest.mock import MagicMock
import os
import tempfile
import json
from pathlib import Path
import argparse
import requests

import sylph_tax

# Import the modules we want to test
from sylph_tax.download_taxonomy import SylphTaxDownloader, main as download_main
from sylph_tax.json_config import JsonConfig
from sylph_tax.metadata_files import __metadata_file_urls__, __name_to_metadata_file__
from sylph_tax.sylph_to_taxprof import (
    genome_file_to_gcf_acc,
    contig_to_imgvr_acc,
    main as taxprof_main,
)


class TestSylphTaxDownloader(TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = SylphTaxDownloader(self.temp_dir)

    def tearDown(self):
        # Clean up temporary files
        for file in Path(self.temp_dir).glob("*"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_init_none_location(self):
        downloader = SylphTaxDownloader("NONE")
        self.assertIsNone(downloader.taxonomy_location)

    def test_init_with_location(self):
        self.assertEqual(self.downloader.taxonomy_location, self.temp_dir)


class TestJsonConfig(TestCase):
    def setUp(self):
        # Create a temporary config directory
        self.temp_config_dir = Path(tempfile.mkdtemp()) / ".config" / "sylph-tax"
        self.temp_config_dir.mkdir(parents=True)
        self.original_home = os.environ.get("HOME")
        os.environ["HOME"] = str(Path(self.temp_config_dir).parent.parent.parent)

    def tearDown(self):
        # Restore original HOME and clean up
        if self.original_home:
            os.environ["HOME"] = self.original_home
        if self.temp_config_dir.exists():
            for file in self.temp_config_dir.glob("*"):
                file.unlink()
            self.temp_config_dir.rmdir()
            self.temp_config_dir.parent.rmdir()
            self.temp_config_dir.parent.parent.rmdir()


class TestSylphToTaxprof(TestCase):
    def test_genome_file_to_gcf_acc(self):
        # Test ASM format
        self.assertEqual(
            genome_file_to_gcf_acc("path/to/GCF_000123_ASM456_genomic.fna"),
            "GCF_000123",
        )

        # Test regular format
        self.assertEqual(genome_file_to_gcf_acc("path/to/GCF_000789_genomic.fna"), "GCF_000789")

    def test_contig_to_imgvr_acc(self):
        self.assertEqual(contig_to_imgvr_acc("IMGVR_UViG_123|other_info"), "IMGVR_UViG_123")

        self.assertEqual(contig_to_imgvr_acc("Simple_contig_name"), "Simple_contig_name")


class TestMetadataFiles(TestCase):
    def test_metadata_urls_not_empty(self):
        self.assertTrue(len(__metadata_file_urls__) > 0)

    def test_name_to_metadata_mapping(self):
        self.assertTrue(len(__name_to_metadata_file__) > 0)
        # Check that all mapped files have corresponding URLs
        for filename in __name_to_metadata_file__.values():
            found = False
            for url in __metadata_file_urls__:
                if url.endswith(filename):
                    found = True
                    break
            self.assertTrue(found, f"Metadata file {filename} not found in URLs")


class TestNoConfigFlag(TestCase):
    """Tests for the --no-config and --taxonomy-dir global flags."""

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.taxonomy_dir = Path(self.temp_dir) / "taxonomy"
        self.taxonomy_dir.mkdir()

    def tearDown(self):
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_download_no_config_requires_taxonomy_dir(self):
        """Test that download with --no-config fails without --taxonomy-dir."""
        args = argparse.Namespace(download_to=None, taxonomy_dir=None, no_config=True)
        with self.assertRaises(SystemExit) as cm:
            download_main(args, config=None)
        self.assertEqual(cm.exception.code, 1)

    def test_download_no_config_with_taxonomy_dir(self):
        """Test that download with --no-config succeeds with --taxonomy-dir."""
        args = argparse.Namespace(
            download_to=None, taxonomy_dir=str(self.taxonomy_dir), no_config=True
        )
        # Mock the actual download to avoid network calls
        import sylph_tax.download_taxonomy as dt

        original_download = dt.SylphTaxDownloader.download_taxonomy
        dt.SylphTaxDownloader.download_taxonomy = MagicMock(return_value=[])

        try:
            # Should not raise
            download_main(args, config=None)
        finally:
            dt.SylphTaxDownloader.download_taxonomy = original_download

    def test_download_no_config_with_download_to(self):
        """Test that download with --no-config succeeds with --download-to."""
        args = argparse.Namespace(
            download_to=str(self.taxonomy_dir), taxonomy_dir=None, no_config=True
        )
        # Mock the actual download to avoid network calls
        import sylph_tax.download_taxonomy as dt

        original_download = dt.SylphTaxDownloader.download_taxonomy
        dt.SylphTaxDownloader.download_taxonomy = MagicMock(return_value=[])

        try:
            # Should not raise
            download_main(args, config=None)
        finally:
            dt.SylphTaxDownloader.download_taxonomy = original_download

    def test_download_to_takes_precedence_over_taxonomy_dir(self):
        """Test that --download-to takes precedence over --taxonomy-dir for download."""
        download_dest = Path(self.temp_dir) / "download_dest"
        download_dest.mkdir()

        args = argparse.Namespace(
            download_to=str(download_dest),
            taxonomy_dir=str(self.taxonomy_dir),
            no_config=True,
        )

        # Track which directory was used
        used_dir = None
        import sylph_tax.download_taxonomy as dt

        original_init = dt.SylphTaxDownloader.__init__

        def tracking_init(self, db_location):
            nonlocal used_dir
            used_dir = db_location
            original_init(self, db_location)

        dt.SylphTaxDownloader.__init__ = tracking_init
        dt.SylphTaxDownloader.download_taxonomy = MagicMock(return_value=[])

        try:
            download_main(args, config=None)
            self.assertEqual(used_dir, str(download_dest))
        finally:
            dt.SylphTaxDownloader.__init__ = original_init

    def test_taxprof_no_config_requires_taxonomy_dir_for_prebuilt(self):
        """Test that taxprof with --no-config fails without --taxonomy-dir when using pre-built taxonomy."""
        args = argparse.Namespace(
            sylph_results=["test.tsv"],
            taxonomy_metadata=["GTDB_r226"],  # Pre-built taxonomy
            taxonomy_dir=None,
            no_config=True,
            annotate_virus_hosts=False,
            pavian=False,
            output_prefix="",
            add_folder_information=False,
            overwrite=False,
        )
        with self.assertRaises(SystemExit) as cm:
            taxprof_main(args, config=None)
        self.assertEqual(cm.exception.code, 1)

    def test_taxprof_no_config_allows_custom_taxonomy_without_taxonomy_dir(self):
        """Test that taxprof with --no-config works with custom taxonomy file (no --taxonomy-dir needed)."""
        # Create a minimal custom taxonomy file
        custom_tax = Path(self.temp_dir) / "custom_taxonomy.tsv"
        custom_tax.write_text("accession\ttaxonomy\nTEST123\td__Bacteria\n")

        # Create a minimal sylph result file
        sylph_result = Path(self.temp_dir) / "result.tsv"
        sylph_result.write_text(
            "Sample_file\tGenome_file\tContig_name\tAdjusted_ANI\tSequence_abundance\tTaxonomic_abundance\tEff_cov\n"
        )
        sylph_result.write_text(
            "Sample_file\tGenome_file\tContig_name\tAdjusted_ANI\tSequence_abundance\tTaxonomic_abundance\tEff_cov\nsample.fq\tTEST123.fna\tcontig1\t0.95\t0.5\t0.5\t10.0\n"
        )

        args = argparse.Namespace(
            sylph_results=[str(sylph_result)],
            taxonomy_metadata=[str(custom_tax)],  # Custom file, not pre-built
            taxonomy_dir=None,
            no_config=True,
            annotate_virus_hosts=False,
            pavian=False,
            output_prefix=str(self.temp_dir) + "/out_",
            add_folder_information=False,
            overwrite=True,
        )
        # Should not raise - custom taxonomy doesn't need taxonomy_dir
        taxprof_main(args, config=None)


if __name__ == "__main__":
    main()


class TestMetadataURLs(TestCase):
    def test_metadata_urls_accessible(self):
        """Test that all metadata URLs are accessible and return valid gzipped files."""
        for url in __metadata_file_urls__:
            with self.subTest(url=url):
                # Make HEAD request first to check accessibility
                response = requests.head(url, allow_redirects=True)
                self.assertEqual(response.status_code, 200, f"URL not accessible: {url}")

                # Check file size is reasonable (more than 1KB)
                content_length = int(response.headers.get("content-length", 0))
                self.assertGreater(content_length, 1024, f"File seems too small: {url}")

    def test_metadata_file_mapping_consistency(self):
        """Test that all mapped files have valid corresponding URLs."""
        for name, filename in __name_to_metadata_file__.items():
            with self.subTest(name=name):
                # Check if file exists in URLs
                matching_urls = [url for url in __metadata_file_urls__ if url.endswith(filename)]
                self.assertEqual(
                    len(matching_urls),
                    1,
                    f"Expected exactly one matching URL for {filename}",
                )
