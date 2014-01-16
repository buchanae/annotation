from __future__ import absolute_import

from interval.closed import Interval
from more_itertools import pairwise

from annotation.models import helpers, positions


# TODO Region should have a reference?
class Region(Interval, helpers.StrandedPositions):

    start = positions.GenomicPositionDescriptor('_start')
    end = positions.GenomicPositionDescriptor('_end')

    # TODO is_reverse? is_reverse_strand? strand == ReverseStrand?
    @property
    def reverse_strand(self):
        # TODO drop strand checking by string? Use values with identity (a la None)?
        return self.strand == '-'


class Annotation(object):
    def __init__(self):
        self.references = set()


class Reference(object):
    '''Model representing a reference feature, e.g. a chromosome.'''

    def __init__(self, ID, size):
        super(Reference, self).__init__()
        self.ID = ID
        self.size = size
        self.genes = set()

    def __repr__(self):
        tpl = 'Reference({}, {})'
        return tpl.format(self.ID, self.size)


class Gene(Region):
    '''Model representing a gene feature.'''

    def __init__(self, ID, strand):
        self.ID = ID
        self.strand = strand
        self.reference = None
        self.transcripts = set()

    def __repr__(self):
        tpl = 'Gene({}, {})'
        return tpl.format(self.ID, self.strand)

    @property
    def start(self):
        return min(t.start for t in self.transcripts)

    @property
    def end(self):
        return max(t.end for t in self.transcripts)


class Intron(Region):

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.transcript = None

    def __repr__(self):
        return 'Intron({}, {}, {})'.format(self.start, self.end, self.transcript)

    @property
    def strand(self):
        return self.transcript.strand

    @property
    def donor(self):
        return self.five_prime

    @property
    def acceptor(self):
        return self.three_prime


class Transcript(helpers.TranscriptPositions):

    Intron = Intron

    def __init__(self, ID):
        self.ID = ID
        self._introns = None
        self.gene = None
        self.exons = helpers.ExonCollection()

    # TODO repr or str?
    def __repr__(self):
        return 'Transcript({})'.format(self.gene)

    @property
    def strand(self):
        return self.gene.strand

    @property
    def start(self):
        return min(e.start for e in self.exons)

    @property
    def end(self):
        return max(e.end for e in self.exons)

    @property
    def length(self):
        return sum(exon.length for exon in self.exons)

    @property
    def introns(self):
        if not self._introns:
            self.build_introns()
        return self._introns

    def build_introns(self):
        self._introns = []

        for a, b in pairwise(self.exons):
            start = a.end + 1
            end = b.start - 1
            intron = self.Intron(start, end)
            intron.transcript = self
            self._introns.append(intron)


class Exon(Region):

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.transcript = None

    def __repr__(self):
        return 'Exon({}, {}, {})'.format(self.start, self.end, self.transcript)

    @property
    def strand(self):
        return self.transcript.strand
