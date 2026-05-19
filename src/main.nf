

nextflow.enable.dsl=2

params.input_data = "data/telmgd_qced/*.fq.gz"
params.outdir = "results"
params.bin = "bin"

// Here we include the modules
include { SEQ_LEN; MERGE_COUNT } from "./modules/seq_len.nf"

workflow {
    // Create input channels
    // Here we will have input channel that will input the fastq.gz files
    fastq_ch = channel
                .fromPath(params.input_data)
                .map { file ->
                        def sample_id = file.name.replaceAll(/.*_/,"").replaceAll(/\.fq\.gz$/,"")
                        tuple (sample_id, file)
                    }

    // Step 1: Caculate seq length
    seqlen_ch = SEQ_LEN(fastq_ch)

    // Step 2: Merge all the sequence lengths
    merged_input = seqlen_ch.map { sample_id, f -> f }.collect()

    MERGE_COUNT(merged_input)

}