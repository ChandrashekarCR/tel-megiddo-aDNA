"""
build_db.py — config-driven Kraken2 + Bracken database builder.
Usage: python src/build_db.py --config config/config.yaml [--builds run_gallus_standard run_gallus_complete]
All behaviour is controlled by config.yaml and genome_groups.yaml.
"""

import argparse
import os
import shutil 
import subprocess
from pathlib import Path
from utils import load_configs, get_logger, sentinel, mark_done, run
from downloader import download_genome
from tagger import tag_fasta


# Taxonomy building
def build_taxonomy(taxonomy_dir: str, log_dir: str, logger):
    done_flag = os.path.join(taxonomy_dir,".done_taxonomy")
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
        fname = os.path.basename(dir)
        logger.info(f"Downloading {fname}..")
        # Rn the bash commnad for downlaoding
        run(["wget","-c","--tries=10","--waitretry=30", url, "-P", taxonomy_dir], log_file, logger)
        
        logger.info("Extracting taxdump...")
        run(["tar","-xvzf",os.path.join(taxonomy_dir),"taxdump.tar.gz","-C",taxonomy_dir],log_file,logger)

        for gz in ["nucl_gb.accession2taxid.gz", "nucl_wgs.accession2taxid.gz"]:
            run(["gunzip", os.path.join(taxonomy_dir,gz)],log_file,logger)

        # Verify
        required = ["nodes.dmp","names.dmp","nucl_gb.accession2taxid", "nucl_wgs.accession2taxid"]

        for f in required:
            if not os.path.exists(os.path.join(taxonomy_dir,f)):
                raise FileNotFoundError(f"Taxonomy incomplete -missing {f}")
        
        mark_done(done_flag)
        logger.info("Taxonomy Ready")

# Kraken2 library build

def build_kraken2(build_name: str, genome_names: list, tagged_dir: str, db_dir: str, taxonomy_dir: str, cfg: dict, log_dir: str, logger):
    
    build_log_dir = os.path.join(log_dir,build_name)
    os.makedirs(build_log_dir,exist_ok=True)
    os.makedirs(db_dir,exist_ok=True)
    
    # Copy taxonmy into the builds DB dir
    tax_dst = os.path.join(db_dir, "taxonomy")
    if not os.path.exists(tax_dst):
        logger.info(f"  Copying taxonomy into {build_name}...")
        shutil.copytree(taxonomy_dir, tax_dst,
                        ignore=shutil.ignore_patterns(".*", "*.gz", "*.tar.gz"))
        
    # Here we add each genome to the library
    for genome_name in genome_names:
        done_flag = os.path.join(db_dir,f".done_addlib_{genome_name}")
        if sentinel(done_flag):
            logger.info(f"{genome_name} already in library")
            continue

        tagged_fna = os.path.join()