import pandas as pd
from pathlib import Path
from collections import defaultdict
import sys
import csv
import gzip

from sylph_tax.metadata_files import __name_to_metadata_file__


def trim_file_path(file_name):
    return file_name.split("/")[-1]


def trim_contig_name(contig_name):
    return contig_name.split()[0]


def genome_file_to_gcf_acc(file_name):
    if "ASM" in file_name:
        return file_name.split("/")[-1].split("_ASM")[0]
    return file_name.split("/")[-1].split("_genomic")[0]


def contig_to_imgvr_acc(contig_name):
    return contig_name.split(" ")[0].split("|")[0]


def main(args, config):
    # Determine taxonomy directory with precedence: --taxonomy-dir > config
    taxonomy_dir = None
    if hasattr(args, "taxonomy_dir") and args.taxonomy_dir is not None:
        taxonomy_dir = args.taxonomy_dir
    elif config is not None and config.json["taxonomy_dir"] != "NONE":
        taxonomy_dir = config.json["taxonomy_dir"]

    # Check if we'll need the taxonomy directory (i.e., if any pre-built taxonomies are requested)
    needs_taxonomy_dir = any(
        f in __name_to_metadata_file__ for f in args.taxonomy_metadata
    )

    if needs_taxonomy_dir and taxonomy_dir is None:
        # Distinguish between --no-config mode and config with unset taxonomy_dir
        if config is None:
            print(
                "ERROR: --taxonomy-dir is required when --no-config is set and using pre-built taxonomies. Please specify a directory using --taxonomy-dir, or provide custom taxonomy file paths directly."
            )
        else:
            print(
                "ERROR: No taxonomy directory has been configured. Please run 'sylph-tax download --download-to <directory>' first, or specify --taxonomy-dir."
            )
        sys.exit(1)

    if taxonomy_dir is None and not needs_taxonomy_dir:
        pass  # Custom files only, no taxonomy dir needed
    elif taxonomy_dir is None:
        print(
            "WARNING: No downloaded taxonomy files could be found. Ensure that you have downloaded the taxonomy metadata files using the 'download' command."
        )

    annotate_virus = args.annotate_virus_hosts
    pavian = args.pavian

    ### This is a dictionary that contains the genome_file
    ### to taxonomy string mapping. It should be like
    ### {'my_genome.fna.gz' : b__Bacteria;...}
    genome_to_taxonomy = dict()
    genome_to_additional_data = dict()
    metadata_files_full = []

    print(f"Reading metadata: {args.taxonomy_metadata} ...")

    for file_name in args.taxonomy_metadata:
        prebuilt = False
        if file_name in __name_to_metadata_file__:
            if "UHGV" in file_name:
                print(
                    "WARNING: the UHGV taxonomy output format differs slightly from prokaryotic taxonomies. Taxonomic ranks may be skipped (e.g., Family -> Species rather than Family -> Genus -> Species)"
                )
            base_file = __name_to_metadata_file__[file_name]
            file = Path(taxonomy_dir) / base_file
            prebuilt = True
        else:
            file = Path(file_name)
        if not file.exists():
            print(f"ERROR: Metadata file {file} not found. Exiting.")
            sys.exit(1)
        ### Process gzip file instead if extension detected
        if ".gz" in file_name or ".gzip" in file_name or prebuilt:
            f = gzip.open(file, "rt")
        else:
            f = open(file, "r")

        metadata_files_full.append(str(file))

        ### Tag each taxonomy string with a t__ strain level identifier
        for row in f:
            spl = row.rstrip().split("\t")
            accession = spl[0]
            taxonomy = spl[1].rstrip() + ";t__" + accession
            if len(spl) > 2:
                genome_to_additional_data[accession] = spl[2].rstrip()
            genome_to_taxonomy[accession] = taxonomy

    for sylph_result in args.sylph_results:
        print("Processing sylph output file: ", sylph_result)

        with open(sylph_result, "r") as file:
            # Read the first line of the file
            first_line = file.readline()
            num_cols = len(first_line.split("\t"))
            second_line = file.readline()
            num_cols2 = len(second_line.split("\t"))
            if num_cols != num_cols2:
                print(
                    f"WARNING: there is an extra tab, probably in the contig fasta id used for sylph's database. Removing all columns after the first {num_cols}."
                )
        # Read sylph's output TSV file into a Pandas DataFrame
        try:
            df = pd.read_csv(sylph_result, sep="\t", usecols=range(num_cols))
            df["Sample_file"] = df["Sample_file"].astype(str)
        except:
            print("ERROR: Could not read sylph results file. Exiting.")
            sys.exit(1)

        ### Group by sample file. Output one file fo reach sample file.
        grouped = df.groupby("Sample_file")
        outs = set()

        for sample_file, group_df in grouped:
            first_warn = False
            if args.add_folder_information:
                out = "_".join(sample_file.split("/"))
            else:
                out = sample_file.split("/")[-1]
            out_file = args.output_prefix + out + ".sylphmpa"
            print(f"Writing output to: {out_file} ...")
            if out_file in outs and not args.overwrite:
                print(
                    f"ERROR! Multiple .sylphmpa files would have the same sample name ({out}), which will cause a file to be overwritten. Consider --add-folder-information to disambiguate sample files"
                )
                sys.exit(1)
            outs.add(out_file)
            out_file_path = Path(out_file)
            if out_file_path.exists() and not args.overwrite:
                print(
                    f"ERROR! A .sylphmpa file exists with the sample name ({out}), which will cause a file to be overwritten. Consider --add-folder-information to disambiguate sample files"
                )
                sys.exit(1)
            of = open(out_file, "w")

            tax_abundance = defaultdict(float)
            seq_abundance = defaultdict(float)
            ani_dict = defaultdict(float)
            cov_dict = defaultdict(float)

            # Iterate over each row in the DataFrame
            for idx, row in group_df.iterrows():
                if (
                    "Genome_file" not in row
                    or "Contig_name" not in row
                    or "Adjusted_ANI" not in row
                    or "Sequence_abundance" not in row
                ):
                    print(
                        "ERROR: Missing required columns in sylph output file. Exiting."
                    )
                    sys.exit(1)

                # Parse the genome file... assume the file is in gtdb format.
                # This can be changed.
                tax_str = None
                ani = float(row["Adjusted_ANI"])
                for i in range(2):
                    if i == 0:
                        genome_file = genome_file_to_gcf_acc(row["Genome_file"])
                        contig_id = contig_to_imgvr_acc(row["Contig_name"])
                    else:
                        genome_file = trim_file_path(row["Genome_file"])
                        contig_id = trim_contig_name(row["Contig_name"])

                    if "Eff_cov" in row:
                        cov = float(row["Eff_cov"])
                    else:
                        cov = float(row["True_cov"])

                    if genome_file in genome_to_taxonomy:
                        tax_str = genome_to_taxonomy[genome_file]
                    elif genome_file + ".gz" in genome_to_taxonomy:
                        tax_str = genome_to_taxonomy[genome_file + ".gz"]
                    elif contig_id in genome_to_taxonomy:
                        tax_str = genome_to_taxonomy[contig_id]
                    else:
                        split_fasta1 = genome_file.split(".fa")[0]
                        split_fasta2 = genome_file.split(".fasta")[0]
                        split_fasta3 = genome_file.split(".fna")[0]
                        if split_fasta1 in genome_to_taxonomy:
                            tax_str = genome_to_taxonomy[split_fasta1]
                        elif split_fasta2 in genome_to_taxonomy:
                            tax_str = genome_to_taxonomy[split_fasta2]
                        elif split_fasta3 in genome_to_taxonomy:
                            tax_str = genome_to_taxonomy[split_fasta3]

                if tax_str is None:
                    tax_str = "NO_TAXONOMY;t__" + genome_file + ":" + contig_id
                    if not first_warn:
                        print(
                            f"WARNING: No taxonomy information found for entry {genome_file} and contig {contig_id} in metadata files ({metadata_files_full}). Did you use the correct database and taxonomies? Assigning default taxonomy"
                        )

                abundance = float(row["Sequence_abundance"])
                rel_abundance = float(row["Taxonomic_abundance"])

                # Split taxonomy string into levels and update abundance
                tax_levels = tax_str.split(";")
                cur_tax = ""
                for level in tax_levels:
                    if level == "":
                        level = "UNKNOWN"
                    if cur_tax:
                        cur_tax += "|"
                    cur_tax += level
                    tax_abundance[cur_tax] += rel_abundance
                    seq_abundance[cur_tax] += abundance
                    if "t__" in cur_tax:
                        ani_dict[cur_tax] = ani
                    if "t__" in cur_tax:
                        cov_dict[cur_tax] = cov

            # Print the CAMI BioBoxes profiling format
            if pavian:
                of.write("#mpa_v3_sylphmock")

            of.write(
                f"#SampleID\t{sample_file}\tTaxonomies_used:{args.taxonomy_metadata}\n"
            )

            if pavian:
                of.write("#clade_name\tplaceholder\trelative_abundance\tplaceholder2\n")
            elif annotate_virus:
                of.write(
                    "clade_name\trelative_abundance\tsequence_abundance\tANI (if strain-level)\tCoverage (if strain-level)\tVirus_host (if viral)\n"
                )
            else:
                of.write(
                    "clade_name\trelative_abundance\tsequence_abundance\tANI (if strain-level)\tCoverage (if strain-level)\n"
                )

            level_to_key = dict()
            for key in tax_abundance.keys():
                level = len(key.split("|"))
                if level not in level_to_key:
                    level_to_key[level] = [key]
                else:
                    level_to_key[level].append(key)

            sorted_keys = sorted(level_to_key.keys())

            for level in sorted_keys:
                keys_for_level = sorted(
                    level_to_key[level], key=lambda x: tax_abundance[x], reverse=True
                )
                for tax in keys_for_level:
                    taxid = None
                    if pavian:
                        tax_len = len(tax.split("|")) - 1
                        taxid = "0"
                        for i in range(tax_len):
                            taxid += "|0"

                    if tax in ani_dict:
                        if pavian:
                            of.write(f"{tax}\t{taxid}\t{tax_abundance[tax]}\t\n")
                        elif annotate_virus:
                            accession = tax.split("t__")[-1]
                            if accession in genome_to_additional_data:
                                val = genome_to_additional_data[accession]
                                splitted = val.split(";")
                                splitted_unknown = [
                                    x if x != "" else "UNKNOWN" for x in splitted
                                ]
                                new_val = ";".join(splitted_unknown)
                                val = new_val
                            else:
                                val = "NA"
                            of.write(
                                f"{tax}\t{tax_abundance[tax]}\t{seq_abundance[tax]}\t{ani_dict[tax]}\t{cov_dict[tax]}\t{val}\n"
                            )
                        else:
                            of.write(
                                f"{tax}\t{tax_abundance[tax]}\t{seq_abundance[tax]}\t{ani_dict[tax]}\t{cov_dict[tax]}\n"
                            )
                    else:
                        if pavian:
                            of.write(f"{tax}\t{taxid}\t{tax_abundance[tax]}\t\n")
                        elif annotate_virus:
                            of.write(
                                f"{tax}\t{tax_abundance[tax]}\t{seq_abundance[tax]}\tNA\tNA\tNA\n"
                            )
                        else:
                            of.write(
                                f"{tax}\t{tax_abundance[tax]}\t{seq_abundance[tax]}\tNA\tNA\n"
                            )
