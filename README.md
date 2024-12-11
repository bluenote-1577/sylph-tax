# sylph-tax - incorporating taxonomy into [sylph](https://github.com/bluenote-1577/sylph)

> [!NOTE]
> This repo replaces the [sylph-utils](https://github.com/bluenote-1577/sylph-utils) repository with a cleaner commandline interface and easy taxonomy downloading.

The [sylph](https://github.com/bluenote-1577/sylph) metagenome profiler outputs a TSV format that does not have taxonomic information. `sylph-tax` is a program for turning `sylph`'s output into a **taxonomic profile** like Kraken or MetaPhlAn.
## Taxonomy integration - available databases 

The following databases are currently supported (with pre-built sylph databases [available here](https://github.com/bluenote-1577/sylph/wiki/Pre%E2%80%90built-databases))

| sylph-tax identifier   | Database description                                                                                             | Clades     |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------- |
| GTDB_r220              | [GTDB-r220 (April 2024)](https://gtdb.ecogenomic.org/stats/r220)                                                 | Prokaryote |
| GTDB_r214              | [GTDB-r214 (April 2023)](https://gtdb.ecogenomic.org/stats/r214)                                                 | Prokaryote |
| OceanDNA               | [OceanDNA - ocean MAGs from Nishimura & Yoshizawa](https://doi.org/10.1038/s41597-022-01392-5)                   | Prokaryote |
| SoilSMAG               | [Soil MAGs (SMAG) from Ma et al.](https://www.nature.com/articles/s41467-023-43000-z)                            | Prokaryote |
| FungiRefSeq-2024-07-25 | Refseq fungi representative genomes collected on 2024-07-25                                                      | Eukaryote  |
| TaraEukaryoticSMAG     | [TARA eukaryotic SMAGs from Delmont et al.](https://www.sciencedirect.com/science/article/pii/S2666979X22000477) | Eukaryote  |
| IMGVR_4.1              | [IMG/VR 4.1 high-confidence viral OTU genomes](https://genome.jgi.doe.gov/portal/IMG_VR/IMG_VR.home.html)        | Virus      |
## Install

#### Conda (NOT READY YET)

> [!TIP] 
> If you installed the latest version of `sylph` via conda, `sylph-tax` is also installed. (NOT READY YET)

```sh
conda install -c bioconda sylph-tax
```
#### Python package manager

```sh
git clone https://github.com/bluenote-1577/sylph-tax/
cd sylph-tax
pip install .

sylph-tax --help
```
## Quick start

```sh
# download all taxonomy files (~50 MB)
sylph-tax download --download-to /any/location

# incorporate GTDB-r220 and IMGVR-4.1 taxonomies into sylph's results
sylph-tax taxprof sylph_results/*.tsv -t GTDB_r220 IMGVR_4.1 -o output_prefix-

ls output_prefix-sample1.sylphmpa
ls output_prefix-sample2.sylphmpa
...

# merge multiple results
sylph-tax merge *.sylphmpa --columns relative_abundance -o merged_abundance_file.tsv
```

## `sylph-tax` subcommands

### `download` - download taxonomy metadata 

```
sylph-tax download --download-to /my/folder/sylph_taxonomy_files/
```

* Downloads taxonomic annotation files (~50 MB; [see here](https://zenodo.org/records/14320496)) to `--download-to`.
* This folder can be wherever you want. Its location is written to `~/.config/sylph-tax/config.json`.
* If you don't have access to `$HOME`, then you must specify input the downloaded files for `sylph-tax taxprof`. 
### `taxprof` - taxonomic profiles from sylph's output

```sh
sylph-tax taxprof sylph_results/*.tsv  -o prefix_or_folder/ -t {sylph-tax identifier}
```
* `sylph_results/*.tsv`: outputs from sylph. **The databases used for sylph must be the same as the `-t` option.**
* `-t/--taxonomy-metadata`:  A list of `sylph-tax identifier`s in the above table (e.g. `GTDB_r220` or `IMGVR_4.1`).  Multiple taxonomy metadata files can be input. Custom taxonomy files are also possible; see below.
* `-o`: prepends this prefix to all of the output files. One file is output per sample in `sylph_output.tsv`
* `-a/--annotate-virus-hosts`: annotates found viral genomes with host information metadata (only available for `IMGVR_4.1` right now) 
* Output suffix is `.sylphmpa`.  

> [!NOTE]
> Please [see this manual](https://github.com/bluenote-1577/sylph/wiki/Integrating-taxonomic-information-with-sylph#custom-taxonomies-and-how-it-works) for more information on
> 1. output format information 
> 2. how to create taxonomy metadata for customized genome databases

> [!TIP]
> In python/pandas, `pd.read_csv('output.sylphmpa',sep='\t', comment='#')` works.

### `merge` - merge multiple taxonomic profiles

Merge multiple taxonomic profiles from `sylph_to_taxprof.py` into a TSV table 

```sh
sylph-tax merge *.sylphmpa --column {ANI, relative_abundance, sequence_abundance} -o output_table.tsv
```

* `*.sylphmpa` files are outputs from `sylph-tax taxprof`. 
* `--column` can be ANI, relative abundance, or sequence abundance (see paper for difference between abundances)
* `-o` output file in TSV format.
#### Output format for `merge` (TSV)
```sh
clade_name  sample1.fastq.gz  sample2.fastq.gz
d__Archaea  0.0  1.1
d__Archaea|p__Methanobacteriota 0.0     0.0965
...
```
