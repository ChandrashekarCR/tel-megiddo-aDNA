"""
build_db.py — config-driven Kraken2 + Bracken database builder.
Usage: python src/build_db.py --config config/config.yaml [--builds run_gallus_standard run_gallus_complete]
All behaviour is controlled by config.yaml and genome_groups.yaml.
"""

import argparse
import os
import shutil
from utils import load_config, get_logger, sentinel, mark_done, run
from downloader import download_genome
from tagger import tag_fasta


# Taxonomy building
def build_taxonomy(taxonomy_dir: str, log_dir: str, logger):
    done_flag = os.path.join(taxonomy_dir, ".done_taxonomy")
    if sentinel(done_flag):
        logger.info("Txonomy already doenloaded")
        return

    os.makedirs(taxonomy_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "taxonomy.log")

    TAXONOMY_BASE = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy"
    files = [
        f"{TAXONOMY_BASE}/taxdump.tar.gz",
        f"{TAXONOMY_BASE}/accession2taxid/nucl_gb.accession2taxid.gz",
        f"{TAXONOMY_BASE}/accession2taxid/nucl_wgs.accession2taxid.gz",
    ]

    for url in files:
        fname = os.path.basename(url)
        logger.info(f"Downloading {fname}..")
        # Rn the bash commnad for downlaoding
        run(
            ["wget", "-c", "--tries=10", "--waitretry=30", url, "-P", taxonomy_dir],
            log_file,
            logger,
        )

        logger.info("Extracting taxdump...")
        run(
            [
                "tar",
                "-xvzf",
                os.path.join(taxonomy_dir, "taxdump.tar.gz"),
                "-C",
                taxonomy_dir,
            ],
            log_file,
            logger,
        )

    for gz in ["nucl_gb.accession2taxid.gz", "nucl_wgs.accession2taxid.gz"]:
        run(["gunzip", os.path.join(taxonomy_dir, gz)], log_file, logger)

    # Verify
    required = [
        "nodes.dmp",
        "names.dmp",
        "nucl_gb.accession2taxid",
        "nucl_wgs.accession2taxid",
    ]
    for f in required:
        if not os.path.exists(os.path.join(taxonomy_dir, f)):
            raise FileNotFoundError(f"Taxonomy incomplete -missing {f}")

    mark_done(done_flag)
    logger.info("Taxonomy Ready")


# Kraken2 library build


def build_kraken2(
    build_name: str,
    genome_names: list,
    tagged_dir: str,
    db_dir: str,
    taxonomy_dir: str,
    cfg: dict,
    log_dir: str,
    logger,
):

    build_log_dir = os.path.join(log_dir, build_name)
    os.makedirs(build_log_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)

    # Copy taxonmy into the builds DB dir
    tax_dst = os.path.join(db_dir, "taxonomy")
    if not os.path.exists(tax_dst):
        logger.info(f"  Copying taxonomy into {build_name}...")
        shutil.copytree(
            taxonomy_dir,
            tax_dst,
            ignore=shutil.ignore_patterns(".*", "*.gz", "*.tar.gz"),
        )

    # Here we add each genome to the library
    for genome_name in genome_names:
        done_flag = os.path.join(db_dir, f".done_addlib_{genome_name}")
        if sentinel(done_flag):
            logger.info(f"{genome_name} already in library")
            continue

        tagged_fna = os.path.join(tagged_dir, f"{genome_name}_tagged.fna")
        if not os.path.exists(tagged_fna):
            raise FileNotFoundError(
                f"Tagged FASTA missing for {genome_name}:  {tagged_fna}"
            )

        logger.info(f"Adding to library: {genome_name}")
        run(
            ["kraken2-build", "--add-to-library", tagged_fna, "--db", db_dir],
            os.path.join(build_log_dir, f"addlib_{genome_name}.log"),
            logger,
        )
        mark_done(done_flag)

    # Build the Kraken databse
    done_flag = os.path.join(db_dir, ".done_kraken2_build")
    if sentinel(done_flag):
        logger.info(f"Kraken2 build already done for {build_name}.")
    else:
        logger.info(f"Running kraken2-build --build for {build_name}...")
        run(
            [
                "kraken2-build",
                "--build",
                "--db",
                db_dir,
                "--threads",
                str(cfg["threads"]),
                "--kmer-len",
                str(cfg["kmer_len"]),
                "--minimizer-len",
                str(cfg["minimizer_len"]),
                "--minimizer-spaces",
                str(cfg["minimizer_spaces"]),
            ],
            os.path.join(build_log_dir, "kraken2_build.log"),
            logger,
        )
        mark_done(done_flag)
        logger.info(f"Kraken2 build complete: {build_name}")

    # Build the bracken database
    done_flag = os.path.join(db_dir, ".done_bracken_build")
    if sentinel(done_flag):
        logger.info(f"Bracken build already done for {build_name}.")
    else:
        logger.info(f"  Running bracken-build for {build_name}...")
        run(
            [
                "bracken-build",
                "-d",
                db_dir,
                "-t",
                str(cfg["threads"]),
                "-k",
                str(cfg["kmer_len"]),
                "-l",
                str(cfg["read_length"]),
            ],
            os.path.join(build_log_dir, "bracken_build.log"),
            logger,
        )
        mark_done(done_flag)
        logger.info(f"Bracken build complete: {build_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--builds", nargs="*", help="Which db_builds to run (default: all)"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    db_base = cfg["database_base"]
    log_dir = cfg["log_dir"]
    taxonomy_dir = os.path.join(db_base, "shared_taxonomy")
    downloads_dir = os.path.join(db_base, "downloads")
    tagged_dir = os.path.join(db_base, "tagged")

    os.makedirs(log_dir, exist_ok=True)
    logger = get_logger("main", os.path.join(log_dir, "main.log"))

    builds_to_run = args.builds or list(cfg["db_builds"].keys())
    logger.info(f"Builds to run: {builds_to_run}")

    # Step 1: Taxonomy (shared across all builds)
    logger.info("STEP 1: Taxonomy")
    build_taxonomy(taxonomy_dir, log_dir, logger)

    # Step 2: Download + tag all needed genomes
    needed_genomes = set()
    for build_name in builds_to_run:
        needed_genomes.update(cfg["db_builds"][build_name]["includes"])

    logger.info(f"STEP 2: Downloading {len(needed_genomes)} genomes")
    for genome_name in needed_genomes:
        genome = cfg["genomes"][genome_name]
        dl_dir = download_genome(genome_name, genome, downloads_dir, log_dir)
        if dl_dir is None:
            logger.warning(f"Skipping {genome_name} — manual download needed.")
            continue
        tag_fasta(genome_name, genome["taxid"], dl_dir, tagged_dir, log_dir)

    # Step 3: Build each DB
    logger.info("STEP 3: Building databases")
    for build_name in builds_to_run:
        logger.info(f"\nBuilding: {build_name}")
        db_dir = os.path.join(db_base, build_name)
        genome_names = cfg["db_builds"][build_name]["includes"]
        build_kraken2(
            build_name,
            genome_names,
            tagged_dir,
            db_dir,
            taxonomy_dir,
            cfg,
            log_dir,
            logger,
        )

    logger.info("Completed")
    for build_name in builds_to_run:
        db_dir = os.path.join(db_base, build_name)
        logger.info(f"{build_name}: {db_dir}")


if __name__ == "__main__":
    main()
