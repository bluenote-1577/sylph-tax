import unittest
import tempfile
import os
import shutil
import pandas as pd
import gzip
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import sys

from download_taxonomy import SylphTaxDownloader
from json_config import JsonConfig
from metadata_files import __metadata_file_urls__, __name_to_metadata_file__
from merge_sylph_taxprof import merge_data

class TestSylphTaxIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.base_dir = Path(tempfile.mkdtemp())
        cls.taxonomy_dir = cls.base_dir / "taxonomy"
        cls.output_dir = cls.base_dir / "output"
        cls.test_files_dir = Path("test_files")
        
        # Create directories
        cls.taxonomy_dir.mkdir(parents=True)
        cls.output_dir.mkdir(parents=True)
        
        # Configure environment
        os.environ['HOME'] = str(cls.base_dir)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.base_dir)

    def setUp(self):
        """Set up each test."""
        # Create new config for each test
        self.config = JsonConfig()
        self.config.set_taxonomy_dir(str(self.taxonomy_dir))

    def verify_tsv_file(self, file_path):
        """Helper method to verify TSV file validity."""
        try:
            df = pd.read_csv(file_path, sep='\t')
            self.assertGreater(len(df), 0, f"Empty TSV file: {file_path}")
            return True
        except Exception as e:
            self.fail(f"Invalid TSV file {file_path}: {str(e)}")
            return False

    @patch('download_taxonomy.urllib.request.urlretrieve')
    def test_full_workflow(self, mock_urlretrieve):
        """Test the full workflow from download to merge."""
        # Mock the download to create fake taxonomy files
        def fake_download(url, path, callback):
            filename = Path(path).name
            # Create a minimal gzipped TSV file
            with gzip.open(path, 'wt') as f:
                f.write("accession\ttaxonomy\n")
                f.write("TEST123\td__Bacteria;p__Proteobacteria\n")
            return path, None
        
        mock_urlretrieve.side_effect = fake_download

        try:
            # Run sylph-tax taxonomy command
            cmd = [
                sys.executable,"sylph-tax", "download",
                "--download-to", str(self.taxonomy_dir),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")

            # 2. Run taxonomy classification
            sylph_result_path = self.test_files_dir / "result.tsv"
            output_prefix = str(self.output_dir / "test_output_")
            
            # Run sylph-tax taxonomy command
            cmd = [
                sys.executable, "sylph-tax", "taxonomy",
                "-s", str(sylph_result_path),
                "-t", "IMGVR_4.1", "GTDB_r220",
                "-o", output_prefix
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")

            # 3. Verify outputs
            output_files = list(self.output_dir.glob("*.sylphmpa"))
            self.assertGreater(len(output_files), 0, "No output files generated")
            
            # Verify each output file
            for output_file in output_files:
                self.verify_tsv_file(output_file)

            # 4. Test merging
            merged_output = self.output_dir / "merged_output.tsv"
            merge_result = merge_data(
                [str(f) for f in output_files],
                "relative_abundance"
            )
            merge_result.to_csv(merged_output, sep='\t')
            
            # Verify merged output
            self.verify_tsv_file(merged_output)

        except Exception as e:
            self.fail(f"Integration test failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
