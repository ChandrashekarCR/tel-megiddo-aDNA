import os
import glob
from utils import get_logger, sentinel, mark_done


def find_fasta(download_dir: str) -> list:
    """
    Find all the FASTA files inside a download directory
    """

    patterns = [
        f"{download_dir}/**/*.fna",
        f"{download_dir}/*.fna",
        f"{download_dir}/**/*.fna",
        f"{download_dir}/**/*.fasta",
    ]

    found = []
    for p in patterns:
        found.extend(glob.glob(p, recursive=True))

    return list(set(found))


def tag_fasta(
    name: str, taxid: int, download_dir: str, tagged_dir: str, log_dir: str
) -> str:
    """
    Rewrite FASTA headers to include the |kraken:taxid|<TAXID>.
    Returns path to tagged FASTA
    """
    os.makedirs(tagged_dir, exist_ok=True)
    out_fna = os.path.join(tagged_dir, f"{name}_tagged.fna")
    done_flag = os.path.join(tagged_dir, f".done_tag_{name}")
    log_file = os.path.join(log_dir, f"tag_{name}.log")
    logger = get_logger(f"tag.{name}", log_file)

    if sentinel(done_flag):
        logger.info(f"{name} already tagged.")
        return out_fna

    fastas = find_fasta(download_dir)
    if not fastas:
        raise FileNotFoundError(f"No FASTA files found for {name} in {download_dir}")

    logger.info(
        f"Tagging {name} (taxid={taxid}) from {len(fastas)} file(s) -> {out_fna}"
    )

    seqs_tagged = 0
    with open(out_fna, "w") as f:
        for fa in sorted(fastas):
            with open(fa) as inp:
                for line in inp:
                    if line.startswith(">"):
                        # Append taxid -keep original header intact only chage this
                        f.write(f"{line.strip()}|kraken:taxid|{taxid}\n")
                        seqs_tagged += 1
                    else:
                        f.write(line)

    logger.info(f"Tagged {seqs_tagged} sequences for {name}")
    mark_done(done_flag)
    return out_fna
