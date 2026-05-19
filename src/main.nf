

nextflow.enable.dsl=2

params.input_data = "data/telmgd_qced/*.fq.gz"
params.outdir = "results"
params.script = "src/nf_helper"


// Here we include the modules
include { SEQ_LEN; MERGE_COUNT } from "./modules/seq_len.nf"
include { KMER } from "./modules/kmer.nf"
include { PLOT } from "./modules/plot.nf"
include { KRAKEN } from "./modules/tax_classification.nf"

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
    _kraken_ch = KRAKEN(fastq_ch)

    // Step 6: Merge results
    

}