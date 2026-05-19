

nextflow.enable.dsl=2

params.input_data = "data/telmgd_qced/*.fq.gz"
params.outdir = "results"


// Here we include the modules
include { SEQ_LEN; MERGE_COUNT } from "./modules/seq_len.nf"
include { KMER } from "./modules/kmer.nf"

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
    readlen_files_ch = seqlen_ch
                    .map { _sample_id, readlen_file -> readlen_file }
                    .collect()

    MERGE_COUNT(readlen_files_ch)

    // Step 3: K-mer analysis
    kmer_script = file("${workflow.projectDir}/src/kmer.py")
    _kmer_ch = KMER(seqlen_ch, kmer_script)

}