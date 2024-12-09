# sylph-tax - incorporating taxonomy information into [sylph](https://github.com/bluenote-1577/sylph)

> [!NOTE]
> This repo replaces the [sylph-utils](https://github.com/bluenote-1577/sylph-utils) repository with a cleaner commandline interface and easy taxonomy downloading.

This repository contains scripts for incoporating taxonomic information into the output of [sylph](https://github.com/bluenote-1577/sylph). 

## Taxonomy integration - available databases 
The following databases are currently supported (with pre-built sylph databases [available here](https://github.com/bluenote-1577/sylph/wiki/Pre%E2%80%90built-databases))

| sylph-tax identifier | Database description | Clades|
| --- | --- | --- |
| GTDB_r220 | [GTDB-r220 (April 2024)](https://gtdb.ecogenomic.org/stats/r220) | Prokaryote |
| GTDB_r214 | [GTDB-r214 (April 2023)](https://gtdb.ecogenomic.org/stats/r214)  | Prokaryote |
| OceanDNA | [OceanDNA - ocean MAGs from Nishimura & Yoshizawa](https://doi.org/10.1038/s41597-022-01392-5) | Prokaryote |
| SoilSMAG | [Soil MAGs (SMAG) from Ma et al.](https://www.nature.com/articles/s41467-023-43000-z) | Prokaryote |
| FungiRefSeq-2024-07-25 | Refseq fungi representative genomes collected on 2024-07-25| Eukaryote |
| TaraEukaryoticSMAG | [TARA eukaryotic SMAGs from Delmont et al.](https://www.sciencedirect.com/science/article/pii/S2666979X22000477) | Eukaryote |
| IMGVR_4.1 | [IMG/VR 4.1 high-confidence viral OTU genomes](https://genome.jgi.doe.gov/portal/IMG_VR/IMG_VR.home.html) | Virus |

## Install

```sh
git clone https://github.com/bluenote-1577/sylph-tax/
cd sylph-tax
pip install .

sylph-tax --help
```

## Quick start

```sh
# download all taxonomy files
sylph-tax download --download-to /path/to/taxonomy_file_folder

# incorporate GTDB-R220 and IMGVR-4.1 taxonomies into sylph's results
sylph-tax taxonomy sylph_results/*.tsv -t GTDB_R220 IMGVR_4.1 -o output_prefix-

ls output_prefix-sample1.sylphmpa
ls output_prefix-sample2.sylphmpa
...

# merge multiple results
sylph-tax merge *.sylphmpa --columns relative_abundance -o merged_abundance_file.tsv
```

## `sylph-tax` subcommand information

### download - download taxonomy metadata 

```
sylph-tax download --download-to /my/folder/sylph_taxonomy_files
```

* Downloads taxonomic annotation files (~50 MB; [see here](https://zenodo.org/records/14320496)) to `--download-to`.
* This folder can be wherever you want. Its location is remembered and written to `~/.config/sylph-tax/config.json`.
* Ensure you have write-access to `$HOME`. 

### taxonomy - obtaining taxonomic profiles from sylph's output

```sh
sylph-tax taxonomy sylph_output.tsv sylph_output2.tsv ... -o prefix_or_folder/ -t {FungiRefSeq-2024-07-25, GTDB_r214, GTDB_r220, IMGVR_4.1, OceanDNA, SoilSMAG, TaraEukaryoticSMAG} 
```
* `-t/--taxonomy-metadata`: One of the sylph-tax identifiers in the above table (e.g. GTDB_r220).  Multiple taxonomy metadata files can be input (will be concatenated). This can also be a custom taxonomy file.
* `sylph_output.tsv sylph_output2.tsv` outputs from sylph. **The databases used for sylph must be the same as the `-t` option.**
* `-o`: prepends this prefix to all of the output files. One file is output per sample in `sylph_output.tsv`
* `--annotate-virus-hosts`: annotates found viral genomes with host information metadata (only available for `IMGVR_4.1` right now) 
* Output suffix is `.sylphmpa`.  

> [!NOTE]
> Please [see this manual](https://github.com/bluenote-1577/sylph/wiki/Integrating-taxonomic-information-with-sylph#custom-taxonomies-and-how-it-works) for more information on
> 1. output format information 
> 2. how to create taxonomy metadata for customized genome databases

> [!TIP]
> In python/pandas, `pd.read_csv('output.sylphmpa',sep='\t', comment='#')` works.

### merge - merge multiple taxonomic profiles

Merge multiple taxonomic profiles from `sylph_to_taxprof.py` into a TSV table 

```sh
sylph-tax merge *.sylphmpa --column {ANI, relative_abundance, sequence_abundance} -o output_table.tsv
```

* `*.sylphmpa` files from `sylph-tax taxonomy`. 
* `--column` can be ANI, relative abundance, or sequence abundance (see paper for difference between abundances)
* `-o` output file in TSV format.

#### Output format
```sh
clade_name  sample1.fastq.gz  sample2.fastq.gz
d__Archaea  0.0  1.1
d__Archaea|p__Methanobacteriota 0.0     0.0965
...
```
