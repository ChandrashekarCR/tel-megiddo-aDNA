import argparse
import os
import shutil
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
    parser = argparse.ArgumentParser(description="Build Kraken2 databases from tagged FASTA")
    parser.add_argument("--config", help="Path to config.yaml")
    args = parser.parse_args()

    cfg_path = resolve_config_path(args.config)
    config = OmegaConf.load(str(cfg_path))

    config_path = config.genome_config
    db_dir = config.database
    log_dir = config.log_dir
    threads = int(os.environ.get("KRAKEN_THREADS", "16"))

    os.makedirs(log_dir, exist_ok=True)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    for build_name, build_cfg in cfg["db_builds"].items():
        build_db = os.path.join(db_dir, build_name)

        # Copy taxonomy into build-specific DB dir
        os.makedirs(build_db, exist_ok=True)
        tax_src = os.path.join(db_dir, "taxonomy")
        tax_dst = os.path.join(build_db, "taxonomy")
        if not os.path.exists(tax_dst):
            shutil.copytree(tax_src, tax_dst)

        print(f"\n{build_name}")

        # Add each genome in this build group
        add_log = os.path.join(log_dir, f"addlib_{build_name}.log")
        for genome_name in build_cfg["includes"]:
            tagged = os.path.join(db_dir, "tagged", f"{genome_name}_tagged.fna")
            if not os.path.exists(tagged):
                print(f"Missing tagged FASTA for {genome_name}, skipping")
                continue
            print(f"Adding: {genome_name}")
            with open(add_log, "a") as lf:
                subprocess.run(
                    ["kraken2-build", "--add-to-library", tagged, "--db", build_db],
                    check=True,
                    stdout=lf,
                    stderr=subprocess.STDOUT,
                )

        # Build the database
        print("Building DB...")
        build_log = os.path.join(log_dir, f"build_{build_name}.log")
        with open(build_log, "w") as lf:
            subprocess.run(
                [
                    "kraken2-build",
                    "--build",
                    "--db",
                    build_db,
                    "--threads",
                    str(threads),
                    "--kmer-len",
                    "35",
                    "--minimizer-len",
                    "31",
                    "--minimizer-spaces",
                    "6",
                ],
                check=True,
                stdout=lf,
                stderr=subprocess.STDOUT,
            )

        print(f"{build_name} built.")

    return 0


if __name__ == "__main__":
    sys.exit(main())