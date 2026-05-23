import yaml
import logging
import os
import subprocess
from pathlib import Path


def load_config(config_path: str) -> dict:
    """
    Load config.yaml and genome_groups.yaml, merge into one dict
    """
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def get_logger(name: str, log_file: str) -> logging.Logger:
    """
    Logger that writes to both console and a file.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )
    fh = logging.FileHandler(log_file)
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def sentinel(path: str) -> bool:
    """
    Return True if step already done (sentinel file exists).
    """
    return Path(path).exists()


def mark_done(path: str):
    """
    Create a sentinel file marking a step complete.
    """
    Path(path).touch()


def run(cmd: list, log_file: str, logger: logging.Logger):
    """
    Run a shell command, stream output to log file, raise on failure.
    """
    logger.info(f"CMD: {' '.join(cmd)}")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as lf:
        result = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        logger.error(f"Command failed (exit {result.returncode}). See: {log_file}")
        raise RuntimeError(f"Step failed: {' '.join(cmd)}")
