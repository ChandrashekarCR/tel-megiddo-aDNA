import os
import glob
import subprocess
from pathlib import Path
from utils import get_logger, sentinel, mark_done, run


def download_genome(name: str, genome: dict, downloads_dir: str, log_dir: str) -> str:
    """
    Download a genome by whatever methods is mentioned in the config file.
    Retuen the directory where the downloaded files are stored
    Retrurn None if manual intervention is needed
    """

    out_dir = os.path.join(downloads_dir, name)
    done_flag = os.path.join(out_dir, ".done_download")
    log_file = os.path.join(log_dir, f"download_{name}.log")
    logger = get_logger(f"dl.{name}",log_file)

    os.makedirs(out_dir,exist_ok=True)

    if sentinel(done_flag):
        logger.info(f"{name} already downloaded.")
        return out_dir

    method = genome["method"]
    acc    = genome["accession"]

    if method == "datasets":
        zip_path = os.path.join(out_dir,f"{name}.zip")
        logger.info(f"Downloading {name} ({acc} via datasets CLI..")
        run(["datasets", "download", "genome", "accession", acc,
             "--include", "genome",
             "--filename", zip_path],
            log_file, logger)
        run(["unzip", "-q", "-o", zip_path, "-d", out_dir],log_file, logger)
        os.remove(zip_path)
    
    else:
        raise ValueError(f"Unknown download method '{method}' for {name}")

    mark_done(done_flag)
    logger.info(f"{name} downloaded to {out_dir}")
    return out_dir