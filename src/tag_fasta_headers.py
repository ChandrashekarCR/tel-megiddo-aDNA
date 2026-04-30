import argparse
import glob
import os
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
    parser = argparse.ArgumentParser(description="Tag FASTA headers with Kraken2 taxids")
    parser.add_argument("--config", help="Path to config.yaml")
    args = parser.parse_args()

    cfg_path = resolve_config_path(args.config)
    config = OmegaConf.load(str(cfg_path))

    config_path = config.genome_config
    db_dir = config.database

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    for name, genome in cfg["genomes"].items():
        taxid = genome["taxid"]
        dl_dir = os.path.join(db_dir, "downloads", name)
        out_fa = os.path.join(db_dir, "tagged", f"{name}_tagged.fna")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(out_fa), exist_ok=True)

        if os.path.exists(out_fa):
            print(f"{name} already tagged")
            continue

        # Find the fasta (handles both direct and datasets zip structure)
        candidates = glob.glob(f"{dl_dir}/**/*.fna", recursive=True) + glob.glob(f"{dl_dir}/*.fna")

        if not candidates:
            print(f"No fasta found for {name} in {dl_dir}")
            continue

        print(f"{name} (taxid={taxid}) -> {out_fa}")
        with open(out_fa, "w") as out:
            for fa in candidates:
                with open(fa) as inp:
                    for line in inp:
                        if line.startswith(">"):
                            header = line.rstrip()
                            out.write(f"{header}|kraken:taxid|{taxid}\n")
                        else:
                            out.write(line)

    print("Done. All Fasta tagged")
    return 0


if __name__ == "__main__":
    sys.exit(main())