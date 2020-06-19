#!/usr/bin/env python3

# -*- coding: utf-8 -*-


# Importing modules
import sys
import os
import pybedtools as pb
import numpy as np
import pandas as pd
import tqdm
import gc
import csv
import argparse

# This function is to preprocess input file, put it in the DataFrame, extract only BED4 file
# (i.e. chrom, start, end and name), sort it and return the DataFrame
# Input: Path to the input file
# Output: DataFrame with genomic positions of all reads covering novel exons
def PreProcessingInput(input_path):
    # Try to read the file, if unsuccessful, then return an empty DataFrame
    to_return = pd.read_csv(input_path, sep='\t', header=None)
    # Extract only chrom, start, end and read name
    to_return = to_return[[0,1,2,3]]
    # Change coordinates used to 0-based
    to_return[1] = to_return[1] - 1
    # Sort by chrom, start and end
    to_return = to_return.sort_values([0,1,2])
    return to_return

# This function is to obtain a table with amount of reads covering particular position
# Input: DataFrame with genomic positions of novel exons and read names covering these positions (one line per read)
# Output: BedGraph file with chrom, start, end and amount of reads covering a particular position
def BedGraphFile(input_df, path_to_genome_file):
    # Creating BedTool object
    to_return = pb.BedTool.from_dataframe(input_df)
    # Calculating the coverage of each position (for hg38 genome) using bedtools genomecov wrapper
    to_return = to_return.genome_coverage(bg=True, g=path_to_genome_file)
    # Converting the output to DataFrame and returning it
    to_return = to_return.to_dataframe()
    return to_return

# This function is to obtain a BedGraph file with sample name (given as an input file) and read names covering particular genomic interval
# Input:
#   - in_bedgraph: DataFrame with BedGraph file (generated using BedGraphFile function)
#   - in_df_file: DataFrame with input file (preprocessed using PreProcessingInput function)
#   - name_of_sample: string with sample name to put in the table
# Output: DataFrame with BedGraph file with two extra columns: sample name and read names
def BedGraphExtendedFile(in_bedgraph, in_df_file, name_of_sample):
    # Copy the BedGraph into new object
    to_return = in_bedgraph.copy()
    # Change names of the columns
    to_return.columns = ['#chrom', 'start', 'end', 'read_num']
    # Adding new columns
    to_return['sample'] = name_of_sample
    to_return['read_names'] = 'to_fill'
    # Converting input file to
    df_pb = pb.BedTool.from_dataframe(in_df_file)
    # Iterating through input DataFrame to obtain read names for reads covering each potential novel exonic location
    for i in tqdm.trange(to_return.shape[0]):
        # Converting a line to a BedTool object
        a_bed = pb.BedTool.from_dataframe(pd.DataFrame([to_return.iloc[i,[0,1,2]]]))
        # Extracting a read names of reads covering particular genomic location
        readnames = ",".join(list(a_bed.intersect(df_pb, wa=True, wb=True).to_dataframe()['thickStart']))
        # Putting the read name in the file
        to_return.iloc[i,5] = readnames
        del a_bed, readnames
    del df_pb
    return to_return

# Test paths
"""
in_exons = "/tgac/workarea/group-eg/project_Capture/data/CACNA1C/July_17/2017_06_15_CACNA1C/2017_06_15_CACNA1C_barcoded_All_seq_from_pass_files_barcode01/reads_missing_exons.bed"
sample_name = '2017_06_15.barcode01'
out_bedgraph = "temp/temp.bc01.bedgraph"
out_info = "temp/temp.bc01.info"
"""

if __name__ == '__main__':
    # Import the input files using argparse module
    parser = argparse.ArgumentParser(description='This script can be used to obtain BedGraph file with amount of reads covering particular genomic location. It generates BedGraph file with amount of reads a particular location is covered, as well as the same file with sample and read names. The coordinates are 0-based.')
    parser.add_argument("in_file", type=str, help="Path to the parsed LAST MAF output file - reads_missing_exons.bed - generated by parse_maf_annotations.pl script")
    parser.add_argument("path_genome_chrom_sizes", type=str, help="Path to the genome chromosome sizes")
    parser.add_argument("sample_name", type=str, help="String with name of a sample used in the extended BedGraph file")
    parser.add_argument("out_bedgraph", type=str, help="Path to the output BedGraph file")
    parser.add_argument("out_info", type=str, help="Path to the output BedGraph file with sample name and read names covering genomic locations")
    args = parser.parse_args()
    # If the BED file is empty
    if os.stat(args.in_file).st_size == 0:
        # Create empty DataFrames
        bedgraph_out = pd.DataFrame()
        bedgraph_info = pd.DataFrame(columns=['#chrom', 'start', 'end', 'read_num', 'sample', 'read_names'])
        # Writing empty BedGraph and extended BedGraph to output files
        bedgraph_out.to_csv(args.out_bedgraph, sep="\t", header=False, index=False, quoting=csv.QUOTE_NONE, na_rep='NA')
        bedgraph_info.to_csv(args.out_info, sep="\t", header=True, index=False, quoting=csv.QUOTE_NONE, na_rep='NA')
        del bedgraph_out, bedgraph_info
        gc.collect()
    # If the BED file is not empty:
    else:
        # Preprocessing input
        df_in = PreProcessingInput(args.in_file)
        gc.collect()
        # Generating BedGraph
        bedgraph_out = BedGraphFile(df_in, args.path_genome_chrom_sizes)
        gc.collect()
        # Extending the BedGraph file in sample and read name
        bedgraph_info = BedGraphExtendedFile(bedgraph_out, df_in, args.sample_name)
        del df_in
        gc.collect()
        # Writing BedGraph and extended BedGraph to output files
        bedgraph_out.to_csv(args.out_bedgraph, sep="\t", header=False, index=False, quoting=csv.QUOTE_NONE, na_rep='NA')
        bedgraph_info.to_csv(args.out_info, sep="\t", header=True, index=False, quoting=csv.QUOTE_NONE, na_rep='NA')
        del bedgraph_out, bedgraph_info
        gc.collect()
