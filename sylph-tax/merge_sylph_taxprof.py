#!/usr/bin/env python3

import argparse
import pandas as pd

def read_tsv(file_path, column_name):
    df = pd.read_csv(file_path, sep='\t', usecols=['clade_name', column_name], comment='#')
    df.set_index('clade_name', inplace=True)
    return df

def merge_data(files, column_name):
    merged_df = pd.DataFrame()
    if column_name == 'ANI':
        column_name = 'ANI (if strain-level)'
    for file in files:
        with open(file) as f:
            first_line = f.readline()
            sample_name = first_line.split('\t')[1].strip()
        df = read_tsv(file, column_name)
        df.rename(columns={column_name: sample_name}, inplace=True)
        if merged_df.empty:
            merged_df = df
        else:
            merged_df = merged_df.join(df, how='outer')
    merged_df.fillna(0, inplace=True)
    return merged_df

def main(args, config):

    merged_df = merge_data(args.files, args.column)
    output_file = args.output
    merged_df.to_csv(output_file, sep='\t')
    print(f"Merged data written to {output_file}")

if __name__ == "__main__":
    main()
