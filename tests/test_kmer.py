"""Unit tests for kmer distribution logic."""

import pandas as pd

from src.nf_helper.kmer import Kmer


class TestKmerReadFile:
    def test_read_file_counts_lengths(self, tmp_path):
        input_file = tmp_path / "reads.tsv"
        input_file.write_text(
            "read1\t5\nread2\t5\nread3\t7\nread4\t10\n"
        )

        kmer = Kmer(str(input_file))
        df = kmer.read_file()

        expected = pd.DataFrame(
            {
                "length": [5, 7, 10],
                "count": [2, 1, 1],
            }
        )

        pd.testing.assert_frame_equal(df.reset_index(drop=True), expected)


class TestKmerDistribution:
    def test_kmer_dist_basic_counts(self):
        len_df = pd.DataFrame(
            {
                "length": [5, 7],
                "count": [2, 1],
            }
        )

        kmer = Kmer("unused")
        result = kmer.kmer_dist(len_df, min_kmer=3, step_size=1)

        # Expected k-mer counts for k=3,4,5 based on (length - k + 1) * count
        expected_k3 = ((5 - 3 + 1) * 2) + ((7 - 3 + 1) * 1)  # 6 + 5 = 11
        expected_k4 = ((5 - 4 + 1) * 2) + ((7 - 4 + 1) * 1)  # 4 + 4 = 8
        expected_k5 = ((5 - 5 + 1) * 2) + ((7 - 5 + 1) * 1)  # 2 + 3 = 5

        assert result["k_3"].sum() == expected_k3
        assert result["k_4"].sum() == expected_k4
        assert result["k_5"].sum() == expected_k5

    def test_kmer_dist_clips_below_zero(self):
        len_df = pd.DataFrame(
            {
                "length": [2, 3],
                "count": [1, 1],
            }
        )

        kmer = Kmer("unused")
        result = kmer.kmer_dist(len_df, min_kmer=3, step_size=1)

        # For length 2, k=3 should clip to 0; for length 3, k=3 should be 1
        assert list(result["k_3"]) == [0, 1]
