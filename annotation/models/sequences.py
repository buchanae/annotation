import sequence_utils


class ReferenceSequencesMixin(object):
    @property
    def sequence(self):
        return self.annotation.sequences[self.ID]


class RegionSequencesMixin(object):
    @property
    def sequence(self):
        # Region positions are 1-based, closed intervals,
        # Python strings are 0-based, half-open intervals,
        # so we need to transform the start position.
        start = self.start - 1
        return self.reference.sequence[start:self.end]


class TranscriptSequencesMixin(object):

    @property
    def sequence(self):
        ref_seq = self.reference.sequence
        return sequence_utils.get_transcript_seq(ref_seq, self.exons, self.reverse_strand)

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
            if self.reverse_strand:
                start, end = end, start

            interval = Interval(start, end)
            abs_orfs.append(interval)

        return abs_orfs
