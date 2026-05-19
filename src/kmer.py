# Import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os

class Kmer:
    def __init__(self,in_file):
        self.in_file = in_file
    
    def read_file(self):
        df = pd.read_csv(self.in_file, sep = "\t", header=None, names=['read_id','length'])
        length_counts = df['length'].value_counts().sort_index()
        len_df = pd.DataFrame({'length':length_counts.index,'count':length_counts.values})

        return len_df
    
    def kmer_dist(self, len_df: pd.DataFrame, min_kmer: int = 20, step_size: int = 1) -> pd.DataFrame:
        kmer_df = len_df.copy()
        kvals = list(range(min_kmer, max(len_df['length'].max(), 201), 1))

        # Build all k-mer columns at once
        kmer_cols = {}
        for k in kvals:
            kmer_cols[f"k_{k}"] = (len_df['length'] - k + 1).clip(lower=0) * len_df['count']

        # Concatenate all at once
        kmer_df = pd.concat([kmer_df, pd.DataFrame(kmer_cols)], axis=1)
        return kmer_df
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate k-mer distribution from read lengths')
    parser.add_argument('-i','--input_file', dest='input_file', help='Input file with read_id and length')
    parser.add_argument('-m','--min-kmer', dest='min_kmer',type=int, default=20, help='Minimum k-mer size')
    parser.add_argument('-s','--step-size',dest='step_size', type=int, default=1, help='Step size for k-mer calculation')
    parser.add_argument('-o','--output',dest='output', help='Output file to save results')
            
    args = parser.parse_args()
            
    kmer = Kmer(args.input_file)
    len_df = kmer.read_file()
    result_df = kmer.kmer_dist(len_df, min_kmer=args.min_kmer, step_size=args.step_size)
    
    if args.output:
        result_df.to_csv(args.output, index=False)
    else:
        print(result_df)
        