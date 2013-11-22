import sequence_utils

class TranscriptSequencesMixin(object):

    @property
    def sequence(self):
        ref_seq = self.reference.sequence
        reverse = self.strand == '-'
        return sequence_utils.get_transcript_seq(ref_seq, self.exons, reverse)

    @property
    def orfs(self):
        orfs = sequence_utils.find_orfs(self.sequence)

        # find_orfs() returns relative positions,
        # so we need to translate those to absolute positions
        abs_orfs = []

        for orf in orfs:
            start = self.rel_to_abs(orf.start)
            end = self.rel_to_abs(orf.end)

            # If this transcript is on the reverse strand,
            # our positions are backwards, so swap them.
            if self.strand == '-':
                start, end = end, start

            interval = Interval(start, end)
            abs_orfs.append(interval)

        return abs_orfs
