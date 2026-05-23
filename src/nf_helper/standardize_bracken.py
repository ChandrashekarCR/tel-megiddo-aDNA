# Import libraries
import shutil
import argparse
import pandas as pd


def standardize_bracken(
    input_file: str, sample: str, rank: str, output_file: str, min_abd: float = 0.001
):
    df = pd.read_csv(input_file, sep="\t")
    df["classifier"] = "kraken_bracken"

    # Set abundance to zero if below the threshold
    df[sample] = df.apply(
        lambda row: (
            row["fraction_total_reads"] if row["fraction_total_reads"] >= min_abd else 0
        ),
        axis=1,
    )

    standardized_df = df[["classifier", "name", "taxonomy_id", sample]]
    standardized_df.columns = ["classifier", "clade", "tax_id", sample]

    standardized_df.to_csv(output_file, header=True, index=False)


def concat_tables(sample_list, fo):
    if len(sample_list) == 1:
        shutil.copy(sample_list[0], fo)
        return

    merged = None
    sample_cols = []

    for path in sample_list:
        df = pd.read_csv(path, header=0)

        # The last column contains the sample names
        sample = df.columns[-1]
        sample_cols.append(sample)

        # Normalize key fields to avoid mismaticsa due to extra spaces
        df["classifier"] = df["classifier"].astype(str).str.strip()
        df["clade"] = df["clade"].astype(str).str.strip()
        df["tax_id"] = df["tax_id"].astype(str).str.strip()

        # Keep only the relevant columns
        df = df[["classifier", "clade", "tax_id", sample]]

        # If there are duplicate taxa within the same file then sum their values
        df = df.groupby(["classifier", "clade", "tax_id"], as_index=False).sum(
            numeric_only=True
        )

        # For the first file, initialize the merged table; for the next files perfrom an outer merge on taxonomic keys
        if merged is None:
            merged = df
        else:
            merged = pd.merge(
                merged, df, on=["classifier", "clade", "tax_id"], how="outer"
            )

        # Replace any missising abundance values with - for each sample column
        for col in sample_cols:
            if col in merged.columns:
                merged[col] = merged[col].fillna(0)

        # Save the merged table
        merged.to_csv(fo, header=True, index=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["standardize", "merge"], required=True)
    # standardize args
    p.add_argument(
        "-i", "--input_file", nargs="+", required=True
    )  # nargs=+ handles both modes
    p.add_argument("-s", "--sample", required=False)
    p.add_argument("-r", "--rank", required=False)
    p.add_argument("-o", "--output_file", required=True)
    p.add_argument("--min_abd", type=float, default=0.001)
    args = p.parse_args()

    if args.mode == "standardize":
        standardize_bracken(
            args.input_file[0], args.sample, args.rank, args.output_file, args.min_abd
        )
    elif args.mode == "merge":
        concat_tables(args.input_file, args.output_file)
