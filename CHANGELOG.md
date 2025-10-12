## v1.6.0 - 10-11-2025 

- Added new fungal refseq database because the previous one didn't have Saccharomyces cerevisiae...
- Fixed `sylph-tax download` so that `--download-to` can point to anywhere and it will create a folder. 

## v1.5.1 - 7-22-2025 (should've added this before pushing v1.5.0. oh well)

- Add exactly Pavian compatible format option `--pavian` by replicating exactly MetaPhlan4 columns.

## v1.5.0 - 7-22-2025

- Added GlobDB_r226 as a supported database by default. 

## v1.4.0 - 7-18-2025

**NEW**

- Allowed parsing of taxonomy metadata files without ".fa", ".fna" or ".fasta". So GCF_00120 is now a valid column entry instead of requiring GCF_00120.fa for the metadata tsv files. 

## v1.3.0 - 6-29-2025

**BREAKING**: 
- Replaced empty taxonomic ranks with "UNKNOWN" by default. 

**NEW ADDITIONS**:

- Added UHGV taxonomies and GTDB-R226. 
- Added some help messages
