# Tel-Megiddo Ancient DNA Analysis Pipeline

A comprehensive bioinformatics pipeline for taxonomic classification and characterization of ancient DNA (aDNA) samples from Tel-Megiddo using Kraken2, Bracken, and BLAST analysis.

## Overview

This project implements an automated workflow for analyzing ancient DNA samples against custom reference databases of specific organisms. The pipeline performs taxonomic classification, abundance estimation, k-mer analysis, and quality control on aDNA samples using modern bioinformatics tools packaged in a reproducible, containerized environment.

### Key Features

- **Taxonomic Classification**: Kraken2-based classification against custom organism databases
- **Abundance Estimation**: Bracken for species abundance estimation from Kraken2 results
- **K-mer Analysis**: Comprehensive k-mer distribution analysis of sequencing reads
- **Quality Control**: Read length distribution analysis and visualization
- **Standardized Results**: Unified output format across different classification ranks (phylum, family, genus, species)
- **Containerization**: Singularity image for reproducible deployment on HPC systems and cloud services (Azure)
- **Workflow Automation**: Nextflow-based workflow manager for distributed processing

## Project Structure

```
tel-megiddo/
├── config/                    # Configuration files
│   ├── config.yaml           # Main pipeline configuration with genome selections
│   ├── nextflow_slurm.config  # SLURM cluster execution configuration
│   └── test.config           # Testing configuration for CI/CD
├── src/                       # Source code
│   ├── main.nf               # Primary Nextflow workflow definition
│   ├── modules/              # Nextflow process modules
│   │   ├── seq_len.nf        # Sequence length analysis module
│   │   ├── kmer.nf           # K-mer analysis module
│   │   ├── plot.nf           # Plotting and visualization module
│   │   ├── tax_classification.nf  # Kraken2 and Bracken classification
│   │   ├── post_classification.nf # Result standardization and merging
│   │   └── blastdb.nf        # BLAST database utilities (in development)
│   ├── nf_helper/            # Python helper scripts
│   │   ├── kmer.py           # K-mer distribution calculations
│   │   ├── plot.py           # Visualization utilities
│   │   └── standardize_bracken.py  # Bracken result normalization
│   └── db_build/             # Database building utilities
│       ├── downloader.py      # Genome sequence downloads (NCBI)
│       ├── tagger.py          # FASTA sequence tagging
│       └── utils.py           # Common utility functions
├── scripts/                   # Standalone scripts
│   ├── kraken_bracken.sh      # Shell wrapper for Kraken/Bracken
│   └── build_kraken_database.sbatch  # Database build job script
├── tests/                     # Automated test suite
│   ├── test_kmer.py           # K-mer analysis tests
│   ├── test_standardize_braken.py  # Result standardization tests
│   └── test_utils.py          # Utility function tests
├── notebooks/                 # Jupyter notebooks for exploration
│   └── 01_eda.ipynb          # Exploratory data analysis
├── data/                      # Data directories
│   ├── telmgd_qced/          # Quality-controlled aDNA samples
│   └── test_data/            # Test dataset for CI/CD
├── results/                   # Analysis results (organized by stage)
│   ├── 01_seqlen/            # Read length distributions
│   ├── 02_kmer/              # K-mer analysis results
│   ├── 03_kmer_long/         # Extended k-mer data
│   ├── 04_kmer_plots/        # K-mer visualizations
│   ├── 05_kraken/            # Raw Kraken2 classifications
│   ├── 06_bracken/           # Bracken abundance estimates
│   ├── 07_standardize_bracken/  # Standardized results
│   └── 08_merged_bracken/    # Merged results by rank
├── logs/                      # Execution logs and reports
├── environment.yaml           # Conda environment specification
├── Makefile                   # Task automation and management
├── Singularity                # Container definition file
└── tel-megiddo.sif            # Pre-built Singularity image

```

## Getting Started

### Prerequisites

- **Conda/Mamba**: For environment management ([Install miniconda](https://docs.conda.io/en/latest/miniconda.html))
- **Nextflow**: Workflow orchestration (installed via conda environment)
- **Docker or Apptainer/Singularity**: For containerization
- **Python 3.10+**: For helper scripts (included in environment)

### Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd tel-megiddo
   ```

2. **Set Up the Conda Environment**
   ```bash
   make conda_env
   conda activate tel-megiddo
   ```

   This will create or update the `tel-megiddo` conda environment with all required dependencies including:
   - Nextflow workflow manager
   - Kraken2 (v2.17.1) for taxonomic classification
   - Bracken (v3.1) for abundance estimation
   - BLAST (v2.17.0) for sequence similarity search
   - Python 3.10 with pandas, matplotlib, and Jupyter
   - KMC for k-mer counting

3. **Verify Installation**
   ```bash
   make hello
   ```

## Configuration

### Main Configuration (config/config.yaml)

The primary configuration file defines:

- **Database Path**: Location of custom Kraken2 databases
- **Input Data**: Path to quality-controlled aDNA FASTQ files
- **Reference Genomes**: Included organisms for database construction
- **Parameters**: K-mer size (25bp), minimizer length (21bp), read length (50bp for aDNA)
- **Database Builds**: Pre-defined database selections (e.g., `run_gallus_standard`, `run_gallus_complete`)

### Example Database Build Configuration

```yaml
genomes:
  gallus_latest_ref:
    accession: "GCF_016699485.2"
    label: "Gallus gallus latest ref"
    taxid: 9031
    method: datasets

db_builds:
  run_gallus_standard:
    includes:
      - gallus_latest_ref
      - coturnix
      - turkey
      - phasianus
```

## Workflow

### Pipeline Stages

1. **Sequence Length Analysis** (`SEQ_LEN`)
   - Analyzes read length distributions
   - Output: Tab-separated read IDs and lengths

2. **K-mer Distribution** (`KMER`)
   - Calculates k-mer counts for different k-sizes
   - Assesses sequencing complexity and coverage
   - Output: CSV files with k-mer distributions

3. **K-mer Visualization** (`PLOT`)
   - Generates plots of k-mer distributions
   - Output: PNG/PDF visualizations

4. **Kraken2 Classification** (`KRAKEN`)
   - Performs taxonomic classification against custom database
   - Uses k-mer matching approach
   - Output: Classification reports and TSV files

5. **Bracken Abundance Estimation** (`BRACKEN`)
   - Estimates species abundance from Kraken2 results
   - Operates at multiple taxonomic ranks (phylum, family, genus, species)
   - Output: Abundance estimates at each rank

6. **Result Standardization** (`STANDARDIZE_BRACKEN`)
   - Normalizes Bracken output to unified format
   - Adds classifier metadata
   - Output: Standardized CSV files

7. **Result Merging** (`MERGE_BRACKEN`)
   - Combines results across all samples for each rank
   - Creates summary tables
   - Output: Merged results by taxonomic rank

## Usage

### Running the Complete Pipeline

```bash
conda activate tel-megiddo

# Run the pipeline with default configuration
make nextflow run src/main.nf -c config/config.yaml

# Or using the direct nextflow command
nextflow run src/main.nf -c config/config.yaml
```

### Pipeline Execution Options

```bash
# Run with SLURM cluster configuration
nextflow run src/main.nf -c config/nextflow_slurm.config

# Run in stub mode (for testing workflow logic without computation)
make smoke-test

# Run with specific parameters
nextflow run src/main.nf --input_dir ./data/telmgd_qced/ --output_dir ./results/
```

### Code Quality and Testing

```bash
# Run all automated tests
make test

# Run code linting
make lint

# Format code with ruff
make format

# Clean cache files and temporary outputs
make clean
```

## Containerization

### Building the Singularity Image

```bash
# Build the container image
make build-image
```

This creates `tel-megiddo.sif` that packages:
- Complete conda environment
- All Nextflow modules and scripts
- Configuration files
- Ready-to-use bioinformatics tools

### Running in Container

```bash
# Interactive shell
apptainer shell tel-megiddo.sif

# Execute commands
apptainer exec tel-megiddo.sif nextflow run src/main.nf

# Run the workflow
apptainer run tel-megiddo.sif
```

## Testing

The project includes comprehensive automated tests:

```bash
# Run all tests
make test

# Individual test files
pytest tests/test_kmer.py
pytest tests/test_standardize_braken.py
pytest tests/test_utils.py

# Run pipeline in stub mode (smoke test)
make smoke-test
```

Test coverage includes:
- K-mer distribution calculations
- Bracken result standardization
- Utility functions
- Workflow logic validation (CI/CD)

## Tools and Dependencies

| Tool | Version | Purpose |
|------|---------|---------|
| Nextflow | 24+ | Workflow orchestration |
| Kraken2 | 2.17.1 | Taxonomic classification |
| Bracken | 3.1 | Abundance estimation |
| BLAST | 2.17.0 | Sequence similarity (in development) |
| KMC | 3.2.4 | K-mer counting |
| Python | 3.10+ | Helper scripts & analysis |
| Pandas | Latest | Data manipulation |
| Matplotlib | Latest | Visualization |
| Jupyter | Latest | Interactive analysis |

## Output

Results are organized by analysis stage in the `results/` directory:

- **01_seqlen/**: Read length distribution files (tab-separated)
- **02_kmer/**: K-mer distribution analysis (CSV)
- **04_kmer_plots/**: Visualizations of k-mer distributions
- **05_kraken/**: Raw Kraken2 classification outputs
- **06_bracken/**: Bracken abundance estimates at multiple ranks
- **07_standardize_bracken/**: Normalized results (standardized format)
- **08_merged_bracken/**: Merged results by taxonomic rank

Each result file is prefixed with the sample ID for traceability.

## Project Status

⚠️ **Under Development**: This project is actively being developed. Features currently in progress include:
- BLAST analysis module
- Extended BLAST database utilities
- Azure cloud deployment integration
- Additional visualization types
- Performance optimizations for large datasets

## Development Workflow

### Makefile Targets

- `make hello` - Verify makefile setup
- `make lint` - Run code linting (ruff)
- `make format` - Format code with ruff
- `make clean` - Remove temporary files and caches
- `make conda_env` - Create/update conda environment
- `make build-image` - Build Singularity container
- `make test` - Run automated test suite
- `make smoke-test` - Run workflow in stub mode

### Single Source of Truth

The project maintains a single source of truth through:
- **environment.yaml**: All Python and system dependencies
- **Makefile**: All common tasks and workflows
- **config.yaml**: Pipeline parameters and organism selections
- **Singularity**: Reproducible container specification

## Deployment

### Local HPC (SLURM)

```bash
# Configure for SLURM cluster
nextflow run src/main.nf -c config/nextflow_slurm.config -resume
```

### Azure Cloud Services

```bash
# Use containerized workflow with Azure Batch
apptainer run tel-megiddo.sif nextflow run src/main.nf
```

## Troubleshooting

### Common Issues

1. **Environment Creation Fails**
   ```bash
   conda env remove -n tel-megiddo
   conda clean --all
   make conda_env
   ```

2. **Nextflow Cache Issues**
   ```bash
   make clean
   nextflow clean -f
   ```

3. **SLURM Submission Fails**
   - Check cluster queue configuration
   - Verify SLURM parameters in `config/nextflow_slurm.config`

### Logs and Debugging

- Pipeline logs: `logs/` directory
- Nextflow reports: `.nextflow.log`
- Process-specific logs: `work/` directory
- Enable verbose output: `nextflow run -v`

## Contributing

Contributions are welcome! Please ensure:
- All code passes linting: `make lint`
- Code is properly formatted: `make format`
- New features include tests
- Tests pass: `make test`
- Documentation is updated

## Support

For issues, questions, or suggestions:
1. Check existing GitHub issues
2. Review the troubleshooting section above
3. Create a new issue with detailed error messages and logs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Ancient DNA samples from Tel-Megiddo archaeological site
- Kraken2, Bracken, and BLAST development teams
- Nextflow and Singularity communities
- Contributors and testers

---

**Last Updated**: May 2025  
**Maintainer**: Chandrashekar C.R.  
**Status**: Active Development
