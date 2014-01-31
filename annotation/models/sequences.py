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


class TranscriptPartSequencesMixin(object):
    @property
    def sequence(self):
        rel_start = self.transcript.abs_to_rel(self.start)
        rel_end = self.transcript.abs_to_rel(self.end)

        # If this transcript is on the reverse strand,
        # our positions are backwards, so swap them.
        if self.reverse_strand:
            rel_end, rel_start = rel_start, rel_end

        return self.transcript.sequence[rel_start - 1:rel_end]


# TODO find a better place for this
class InvalidCDS(Exception): pass

class CodingSequencesMixin(TranscriptPartSequencesMixin):

    @property
    def amino_acid_sequence(self):
        # TODO this should really happen on initialization
        if len(self.sequence) % 3 != 0:
            raise InvalidCDS()

        # TODO it's also invalid if it doesn't end with a stop codon

        return sequence_utils.translate(self.sequence)
