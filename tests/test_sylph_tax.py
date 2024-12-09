from unittest import TestCase, main
import os
import tempfile
import json
from pathlib import Path
import requests

import sylph_tax

# Import the modules we want to test
from sylph_tax.download_taxonomy import SylphTaxDownloader
from sylph_tax.json_config import JsonConfig
from sylph_tax.metadata_files import __metadata_file_urls__, __name_to_metadata_file__
from sylph_tax.sylph_to_taxprof import genome_file_to_gcf_acc, contig_to_imgvr_acc

class TestSylphTaxDownloader(TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = SylphTaxDownloader(self.temp_dir)
    
    def tearDown(self):
        # Clean up temporary files
        for file in Path(self.temp_dir).glob('*'):
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
        self.temp_config_dir = Path(tempfile.mkdtemp()) / '.config' / 'sylph-tax'
        self.temp_config_dir.mkdir(parents=True)
        self.original_home = os.environ.get('HOME')
        os.environ['HOME'] = str(Path(self.temp_config_dir).parent.parent.parent)
    
    def tearDown(self):
        # Restore original HOME and clean up
        if self.original_home:
            os.environ['HOME'] = self.original_home
        if self.temp_config_dir.exists():
            for file in self.temp_config_dir.glob('*'):
                file.unlink()
            self.temp_config_dir.rmdir()
            self.temp_config_dir.parent.rmdir()
            self.temp_config_dir.parent.parent.rmdir()
    
class TestSylphToTaxprof(TestCase):
    def test_genome_file_to_gcf_acc(self):
        # Test ASM format
        self.assertEqual(
            genome_file_to_gcf_acc("path/to/GCF_000123_ASM456_genomic.fna"),
            "GCF_000123"
        )
        
        # Test regular format
        self.assertEqual(
            genome_file_to_gcf_acc("path/to/GCF_000789_genomic.fna"),
            "GCF_000789"
        )
    
    def test_contig_to_imgvr_acc(self):
        self.assertEqual(
            contig_to_imgvr_acc("IMGVR_UViG_123|other_info"),
            "IMGVR_UViG_123"
        )
        
        self.assertEqual(
            contig_to_imgvr_acc("Simple_contig_name"),
            "Simple_contig_name"
        )

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

if __name__ == '__main__':
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
                content_length = int(response.headers.get('content-length', 0))
                self.assertGreater(content_length, 1024, f"File seems too small: {url}")

    def test_metadata_file_mapping_consistency(self):
        """Test that all mapped files have valid corresponding URLs."""
        for name, filename in __name_to_metadata_file__.items():
            with self.subTest(name=name):
                # Check if file exists in URLs
                matching_urls = [url for url in __metadata_file_urls__ if url.endswith(filename)]
                self.assertEqual(
                    len(matching_urls), 1,
                    f"Expected exactly one matching URL for {filename}"
                )
