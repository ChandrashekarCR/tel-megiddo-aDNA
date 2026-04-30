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
    parser = argparse.ArgumentParser(description="Build Bracken databases for Kraken2 builds")
    parser.add_argument("--config", help="Path to config.yaml")
    args = parser.parse_args()

    cfg_path = resolve_config_path(args.config)
    config = OmegaConf.load(str(cfg_path))

    config_path = config.genome_config
    db_dir = config.database
    log_dir = config.log_dir

    threads = int(os.environ.get("BRACKEN_THREADS", os.environ.get("KRAKEN_THREADS", "16")))
    kmer_len = int(os.environ.get("KRAKEN_KMER", "35"))
    read_len = int(os.environ.get("BRACKEN_READLEN", "75"))

    os.makedirs(log_dir, exist_ok=True)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    for build_name in cfg["db_builds"].keys():
        build_db = os.path.join(db_dir, build_name)
        build_log = os.path.join(log_dir, f"bracken_build_{build_name}.log")
        print(f"Bracken build: {build_name}")
        with open(build_log, "w") as lf:
            subprocess.run(
                [
                    "bracken-build",
                    "-d",
                    build_db,
                    "-t",
                    str(threads),
                    "-k",
                    str(kmer_len),
                    "-l",
                    str(read_len),
                ],
                check=True,
                stdout=lf,
                stderr=subprocess.STDOUT,
            )

    print("All Bracken builds completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
