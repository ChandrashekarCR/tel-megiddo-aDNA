import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import argparse
import warnings

warnings.filterwarnings("ignore")


class PlotKmer:
    def __init__(self, in_file):
        self.in_file = in_file

    def make_plot_kmer(self):
        kmer_df = pd.read_csv(self.in_file)
        k_cols = [c for c in kmer_df.columns if c.startswith("k_")]

        plot_df = kmer_df.melt(
            id_vars=["length"], value_vars=k_cols, var_name="k", value_name="kmer_count"
        )

        kmer_plot_df = (
            plot_df.groupby(by="k").sum().drop(columns=["length"]).reset_index()
        )
        kmer_plot_df["k"] = (
            kmer_plot_df["k"].apply(lambda x: x.split("_")[-1]).astype(int)
        )
        kmer_plot_df = kmer_plot_df.sort_values(by="k")

        # Numerical derivative dkmer_count/dk at each k
        kmer_plot_df["dkmer_dk"] = np.gradient(
            kmer_plot_df["kmer_count"].to_numpy(), kmer_plot_df["k"].to_numpy()
        )

        return kmer_plot_df

    def kmer_plot(self):
        kmer_plot_df = self.make_plot_kmer()

        fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharex=True)

        sns.lineplot(data=kmer_plot_df, x="k", y="kmer_count", ax=axes[0])
        axes[0].set_title("k-mer count")
        axes[0].set_xlabel("k")
        axes[0].set_ylabel("Count")

        sns.lineplot(data=kmer_plot_df, x="k", y="dkmer_dk", ax=axes[1])
        axes[1].set_title("Derivative of k-mer count")
        axes[1].set_xlabel("k")
        axes[1].set_ylabel("d(count)/dk")

        fig.tight_layout()
        return fig, axes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot k-mer distribution")
    parser.add_argument(
        "-i",
        "--input_file",
        dest="input_file",
        help="Input file with kmer distribution",
    )
    parser.add_argument(
        "-o", "--output", dest="output", help="Output file to save results"
    )
    parser.add_argument("-f", "--figure", dest="figure", help="Ouptu the figure")

    args = parser.parse_args()

    kmer_df = PlotKmer(args.input_file).make_plot_kmer()

    if args.output:
        kmer_df.to_csv(args.output, index=False)
    else:
        print(kmer_df)

    if args.figure:
        fig, axes = PlotKmer(args.input_file).kmer_plot()
        fig.savefig(args.figure, dpi=300, bbox_inches="tight")
    else:
        print("Figure not saved. Pass in the figure parameter.")
