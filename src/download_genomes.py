import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml
from omegaconf import OmegaConf


def resolve_config_path(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path).expanduser().resolve()
    env_path = os.environ.get("TEL_MEGIDDO_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (Path(__file__).resolve().parent.parent / "config" / "config.yaml")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download genomes for Kraken2 DB")
    parser.add_argument("--config", help="Path to config.yaml")
    args = parser.parse_args()

    cfg_path = resolve_config_path(args.config)
    config = OmegaConf.load(str(cfg_path))

    config_path = config.genome_config
    db_dir = config.database
    log_dir = config.log_dir

    os.makedirs(log_dir, exist_ok=True)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)


    for name, genome in cfg["genomes"].items():
        acc = genome["accession"]
        method = genome["method"]
        outdir = os.path.join(db_dir, "downloads", name)
        logf = os.path.join(log_dir, f"download_{name}.log")
        os.makedirs(outdir, exist_ok=True)

        # Skip if already downloaded
        if os.listdir(outdir):
            print(f"Skip. {name} already downloaded in {outdir}")
            continue

        print(f"Download {name} ({acc} via {method})")

        if method == "datasets":
            cmd = [
                "datasets",
                "download",
                "genome",
                "accession",
                acc,
                "--include",
                "genome",
                "--filename",
                os.path.join(outdir, f"{name}.zip"),
            ]
            with open(logf, "w") as lf:
                subprocess.run(cmd, check=True, stdout=lf, stderr=subprocess.STDOUT)
            subprocess.run(["unzip", "-q", os.path.join(outdir, f"{name}.zip"), "-d", outdir], check=True)

        elif method == "efetch":
            # Single nucleotide record (Phasianus chromosome)
            cmd = ["efetch", "-db", "nuccore", "-id", acc, "-format", "fasta"]
            with open(os.path.join(outdir, f"{name}.fna"), "w") as outf, open(logf, "w") as lf:
                subprocess.run(cmd, check=True, stdout=outf, stderr=lf)

        elif method == "bioproject":
            print(f"{name}: download assembly from BioProject {acc} manually")
            print("Run: datasets download genome accession <ASSEMBLY_ACC> \\")
            print(f" --include genome --filename {outdir}/{name}.zip")

        else:
            print(f"Unknown method '{method}' for {name}, skipping.")

    print("\nAll downloads attempted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())