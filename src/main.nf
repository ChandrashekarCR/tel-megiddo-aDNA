

nextflow.enable.dsl=2

params.input_data = "data/telmgd_qced/*.fq.gz"
params.outdir = "results"
params.script = "src/nf_helper"
params.kraken2_db = "/home/chandru/lu2025-12-38/Students/chandru/kraken_databases/run_gallus_standard"
params.bracken_db = "/home/chandru/lu2025-12-38/Students/chandru/kraken_databases/run_gallus_standard"
params.read_len = 50

// Here we include the modules
include { SEQ_LEN; MERGE_COUNT } from "./modules/seq_len.nf"
include { KMER } from "./modules/kmer.nf"
include { PLOT } from "./modules/plot.nf"
include { KRAKEN; BRACKEN } from "./modules/tax_classification.nf"

workflow {
    // Create input channels
    // Here we will have input channel that will input the fastq.gz files
    fastq_ch = channel
                .fromPath(params.input_data)
                .map { file ->
                        def sample_id = file.name.replaceAll(/.*_/,"").replaceAll(/\.fq\.gz$/,"")
                        tuple (sample_id, file)
                    }

    // Helper scripts 
    kmer_script = file("${params.script}/kmer.py")
    plot_script = file("${params.script}/plot.py")

    // Step 1: Caculate seq length
    seqlen_ch = SEQ_LEN(fastq_ch)

    // Step 2: Merge all the sequence lengths
    //readlen_files_ch = seqlen_ch
    //                .map { _sample_id, readlen_file -> readlen_file }
    //                .collect()
//
    //MERGE_COUNT(readlen_files_ch)

    // Step 3: K-mer analysis
    kmer_ch = KMER(seqlen_ch, kmer_script)

    // Step 4: Plot K-mer
    _plot_ch = PLOT(kmer_ch,plot_script)

    // Step 5: Kraken Bracken 
    kraken_ch = KRAKEN(fastq_ch)
    kraken_report_ch = kraken_ch.map { sample_id, _kraken_tsv, kraken_report, _kraken_log -> tuple(sample_id, kraken_report)}


    ranks = ["phylum","family","genus","species"]
    ranks_ch = channel.fromList(ranks)
    // combine = Cartesian product: every sample × every rank, already flat
    bracken_input = kraken_report_ch.combine(ranks_ch)

    _bracken_ch = BRACKEN(bracken_input)

    // Step 6: Merge results
    

}