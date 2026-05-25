
process DOWNLOAD_GALLUS {

    publishDir "${params.blast_db}", mode: "copy"

    input:
    val base

    output:
    path "${base}.zip"
    path "${base}/ncbi_dataset/data/${params.gallus_accession}/*.fna"

    script:
    """
    datasets download genome accession ${params.gallus_accession} \
        --include genome \
        --filename ${base}.zip
    
    unzip ${base}.zip -d ${base}
    """

    stub:
    """
    touch ${base}.zip

    mkdir -p ${base}/ncbi_dataset/data/${params.gallus_accession}
    echo ">stub_chr1" > ${base}/ncbi_dataset/data/${params.gallus_accession}/genome.fna
    echo "ACGTACGT" >> ${base}/ncbi_dataset/data/${params.gallus_accession}/genome.fna
    """

}


process MAKE_BLAST_DB {

    publishDir "${params.blast_db}", mode: "copy"

    input:
    path(gallus_fasta)

    output: 
    path("gallus_blast_db")

    script:
    """
    mkdir -p gallus_blast_db

    makeblastdb \
        -in ${gallus_fasta} \
        -dbtype nucl \
        -out gallus_blast_db/gallus \
        -title "Gallus_gallue_GRCg7b" \
        -parse_seqids \
        -taxid 9031
    """

    stub:
    """
    # Stub: create a dummy gallus_blast_db directory in the workdir
    mkdir -p gallus_blast_db

    # Put dummy BLAST DB files so tools later in the pipeline can find them
    echo "dummy_gallus_1" > gallus_blast_db/gallus.nin
    echo "dummy_gallus_2" > gallus_blast_db/gallus.nhr
    echo "dummy_gallus_3" > gallus_blast_db/gallus.ndb
    touch gallus_blast_db/gallus.nsq
    """
}