Bootstrap: docker
From: mambaorg/micromamba:1.5.10

%labels
    Author Chandrashekar CR
    Version 1.0
    Description "Bioinformatics pipline for analysis of aDNA samples from Tel-Megiddo"

%help
    This container includes environment to replicate the analysis.
    This container also include a bioinformatics pipline to perform Kraken-Braken estimation and BLAST analysis.
    This project is mainly based on using Nextflow as workflow manager to run many aDNA samples.

    Usage:
        apptainer shell container.sif
        apptainer exec container.sif nextflow --Version
        apptainer run container.sif

%files
    # Copy files into the container which are required
    environment.yaml /opt/environment.yaml
    config /opt/config
    src /opt/src/
    Makefile /opt/Makefile
    scripts /opt/scripts

%environment
    # Set environment variables that will be available at runtime
    export LC_ALL=C
    export MAMBA_ROOT_PREFIX="/opt/conda"
    export CONDA_ENV="${MAMBA_ROOT_PREFIX}/envs/tel-megiddo"
    export PATH="$CONDA_ENV/bin:$MAMBA_ROOT_PREFIX/bin:$PATH"
    export NXF_HOME="/tmp/nextflow"
    export NXF_TEMP="/tmp"
    export TMPDIR="/tmp"
    export JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=/tmp"

# This section runs during the container build time.
%post
    # Update the system packages and install the basic utilities like wget, curl, git build-esstial etc.
    apt-get update && apt-get install -y \
        wget \
        curl \
        git \
        build-essential \
        ca-certificates \
        procps \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

    # Initialize micromamba root prefix
    export MAMBA_ROOT_PREFIX=/opt/conda
    export CONDA_ENV="$MAMBA_ROOT_PREFIX/envs/tel-megiddo"

    # Create the environemnt using mamba
    micromamba env create -f /opt/environment.yaml -p "$CONDA_ENV"

    # Clean up micromamba caches
    micromamba clean --all -y

%runscript
    echo "tel-megiddo container: running Nextflow from $CONDA_ENV"
    exec "$CONDA_ENV/bin/nextflow" "$@"