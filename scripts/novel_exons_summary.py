#!/usr/bin/env python3

# -*- coding: utf-8 -*-


# Importing modules
import os
import pathlib
import sys
import pybedtools as pb
import numpy as np
import pandas as pd
import tqdm
import gc
import csv
import argparse


# This function generates the list of files in BedGraph format to use for bedtools unionbedg
# Input:
#   - dir_path: Path to the directory with BedGraph files (files can be in the subdirectories and it will be perfectly fine)
#   - file_distinct: string to distinguish files of interest (BedGraph) from other files in possible subdirectories
#   - left_split: string to split the path from the left-hand side, to obtain a sample name
#   - right_split: string to split the path from the right-had side, to obtain a sample name
# Output: List of files and sample names (in the same order, i.e. first element in a file name list corresponds to the first element in the sample names list)
def FileList(dir_path, file_distinct, left_split, right_split):
    # Create empty list
    path_to_return = []
    # Append all the files found in a specific directory (and its' subdirectories) to the list
    for dir_path, subdirs, files in os.walk(dir_path):
        for name in files:
            path_to_return.append(str(pathlib.PurePath(dir_path, name)))
    # Filter out specific filenames and sort them
    path_to_return = [x for x in path_to_return if file_distinct in x]
    path_to_return.sort()
    # Create a list of sample names by parsing the filenames
    samples_to_return = [x.split(left_split)[-1].split(right_split)[0] for x in path_to_return]
    # Return both file paths and sample names
    return path_to_return, samples_to_return

# This function writes the output file to the specified location
# Because of some errors in pybedtools module I couldn't convert the output BedGraph file
# I created a workaround: I move the resulting BED file into temporary location
# Then I open the file as a DataFrame
# I add the sum of reads from columns 4..end to the last column
# And I write the file to the hard disk
# Input:
#   - filenames: list of filenames for bedtools unionbedg
#   - samples: list of sample names used as a header in bedtools unionbedg
#   - temp_file_path: path to the temporary file created by bedtools unionbedg
#   - output_file_path: path to the output file
# Output: None
def WritingOutputFile(filenames, samples, temp_file_path, output_file_path):
    # Create a file with all BedGraph position per library using bedtools unionbedg
    output_file = pb.BedTool.union_bedgraphs(pb.BedTool('', from_string=True), i=filenames, names=samples, header=True)
    # Move the resulting file to a temporary location
    output_file.moveto(temp_file_path)
    # Read the temporary file to the DataFrame
    output_file = pd.read_csv(temp_file_path, sep="\t", header=0)
    # Create a column with sum of all reads mapped to a particular location
    output_file['SUM'] = output_file.iloc[:,3:].sum(axis=1)
    # Write the file
    output_file.to_csv(output_file_path, sep="\t", header=True, index=False, quoting=csv.QUOTE_NONE, na_rep='NA')

# Test paths
"""
in_dir = '/tgac/workarea/group-eg/project_Capture/data/CACNA1C/July_17/CACNA1C_novel_exons'
temp_file = '/tgac/workarea/group-eg/project_Capture/data/CACNA1C/July_17/CACNA1C_novel_exons/temp_file'
out_path = '/tgac/workarea/group-eg/project_Capture/data/CACNA1C/July_17/CACNA1C_novel_exons/out_file'
"""

if __name__ == '__main__':
    # Import the input files using argparse module
    parser = argparse.ArgumentParser(description='This script generates the summary file for positions of novel exons covered by at least one read in one library. Number of reads covering particular position is put in a particular column. The last column is a sum of all reads covering a particular novel exon position. The coordinates are 0-based.')
    parser.add_argument("in_dir", type=str, help="Directory where the BedGraph files are stored.")
    parser.add_argument("temp_file", type=str, help="Path to the temporary file generated by bedtools unionbedg")
    parser.add_argument("out_path", type=str, help="Path to the output summary file")
    args = parser.parse_args()
    # Generating lists with paths to BedGraph files and sample names
    path_list, sample_names = FileList(args.in_dir, 'BedGraph', '/', '.BedGraph')
    # Generating the output summary file
    WritingOutputFile(path_list, sample_names, args.temp_file, args.out_path)
