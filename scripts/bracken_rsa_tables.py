#!/usr/bin/env python3

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class Note:
    timestamp: str
    rank: str
    sample: str
    input_file: str
    status: str
    message: str


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_notes(notes: list[Note], notes_path: Path) -> None:
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([n.__dict__ for n in notes])
    if df.empty:
        # still create the file with headers
        df = pd.DataFrame(columns=["timestamp", "rank", "sample", "input_file", "status", "message"])
    df.to_csv(notes_path, sep="\t", index=False)


def iter_rank_files(bracken_dir: Path, rank: str) -> Iterable[Path]:
    # Expect layout: bracken_dir/<sample>/<rank>.tsv
    yield from sorted(bracken_dir.glob(f"*/{rank}.tsv"))


def make_rsa_table(
    bracken_dir: Path,
    rank: str,
    min_abd: float,
    notes: list[Note],
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []

    # Sample directories produced by our pipeline contain bracken logs like:
    #   bracken_phylum.log, bracken_species.log, etc.
    # This avoids accidentally treating output folders (e.g., rsa_tables/) as samples.
    sample_dirs = sorted([p for p in bracken_dir.iterdir() if p.is_dir() and any(p.glob("bracken_*.log"))])
    all_samples = [p.name for p in sample_dirs]

    if not all_samples:
        notes.append(
            Note(
                timestamp=iso_now(),
                rank=rank,
                sample="-",
                input_file=str(bracken_dir),
                status="WARN",
                message="no sample subdirectories found under bracken-dir",
            )
        )
        return pd.DataFrame(columns=["classifier", "clade", "tax_id"])

    for sample in all_samples:
        file_path = bracken_dir / sample / f"{rank}.tsv"
        if not file_path.exists():
            notes.append(
                Note(
                    timestamp=iso_now(),
                    rank=rank,
                    sample=sample,
                    input_file=str(file_path),
                    status="SKIP",
                    message="missing rank TSV",
                )
            )
            continue
        try:
            df = pd.read_csv(file_path, sep="\t")
        except Exception as exc:  # noqa: BLE001
            notes.append(
                Note(
                    timestamp=iso_now(),
                    rank=rank,
                    sample=sample,
                    input_file=str(file_path),
                    status="FAIL",
                    message=f"failed to read TSV: {exc}",
                )
            )
            continue

        if df.empty:
            notes.append(
                Note(
                    timestamp=iso_now(),
                    rank=rank,
                    sample=sample,
                    input_file=str(file_path),
                    status="SKIP",
                    message="empty TSV (no rows)",
                )
            )
            continue

        required_cols = {"name", "taxonomy_id", "fraction_total_reads"}
        missing = required_cols - set(df.columns)
        if missing:
            notes.append(
                Note(
                    timestamp=iso_now(),
                    rank=rank,
                    sample=sample,
                    input_file=str(file_path),
                    status="FAIL",
                    message=f"missing columns: {', '.join(sorted(missing))}",
                )
            )
            continue

        rsa = pd.to_numeric(df["fraction_total_reads"], errors="coerce").fillna(0.0)
        rsa = rsa.where(rsa >= min_abd, 0.0)

        out = pd.DataFrame(
            {
                "classifier": "kraken_bracken",
                "clade": df["name"].astype(str).str.strip(),
                "tax_id": df["taxonomy_id"].astype(str).str.strip(),
                "sample": sample,
                "rsa": rsa,
            }
        )

        # If there are duplicate taxa entries within the same sample, sum.
        out = out.groupby(["classifier", "clade", "tax_id", "sample"], as_index=False)["rsa"].sum()
        rows.append(out)

    if not rows:
        notes.append(
            Note(
                timestamp=iso_now(),
                rank=rank,
                sample="-",
                input_file=str(bracken_dir),
                status="WARN",
                message=f"no input files found for rank '{rank}'",
            )
        )
        return pd.DataFrame(columns=["classifier", "clade", "tax_id"])

    long_df = pd.concat(rows, ignore_index=True)

    wide = (
        long_df.pivot_table(
            index=["classifier", "clade", "tax_id"],
            columns="sample",
            values="rsa",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )

    # Ensure columns exist for all samples (even if missing rank TSV).
    for sample in all_samples:
        if sample not in wide.columns:
            wide[sample] = 0.0

    # Make sure sample columns are consistently ordered.
    fixed_cols = ["classifier", "clade", "tax_id"]
    sample_cols = all_samples
    wide = wide[fixed_cols + sample_cols]

    return wide


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Create merged RSA tables (fraction_total_reads) from Bracken results.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--bracken-dir",
        required=True,
        type=Path,
        help="Bracken results directory (expects <sample>/<rank>.tsv under it)",
    )
    p.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Output directory to write merged CSV tables",
    )
    p.add_argument(
        "--ranks",
        nargs="+",
        default=["phylum", "species"],
        help="Ranks to merge (files must be named <rank>.tsv)",
    )
    p.add_argument(
        "--min-abd",
        type=float,
        default=0.001,
        help="Minimum RSA to keep; smaller values are set to 0",
    )
    p.add_argument(
        "--notes",
        type=Path,
        default=None,
        help="Optional notes TSV path (default: <out-dir>/rsa_merge_notes.tsv)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    bracken_dir: Path = args.bracken_dir
    out_dir: Path = args.out_dir
    ranks: list[str] = args.ranks
    min_abd: float = args.min_abd

    if not bracken_dir.exists():
        raise FileNotFoundError(f"Bracken dir not found: {bracken_dir}")
    if not bracken_dir.is_dir():
        raise NotADirectoryError(f"Bracken dir is not a directory: {bracken_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    notes_path = args.notes or (out_dir / "rsa_merge_notes.tsv")

    notes: list[Note] = []

    for rank in ranks:
        table = make_rsa_table(bracken_dir=bracken_dir, rank=rank, min_abd=min_abd, notes=notes)
        out_csv = out_dir / f"bracken_{rank}_rsa.csv"
        table.to_csv(out_csv, index=False)
        notes.append(
            Note(
                timestamp=iso_now(),
                rank=rank,
                sample="-",
                input_file="-",
                status="OK",
                message=f"wrote {out_csv}",
            )
        )

    write_notes(notes, notes_path)


if __name__ == "__main__":
    main()
