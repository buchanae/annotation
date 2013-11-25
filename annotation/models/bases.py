from __future__ import absolute_import

from interval.closed import Interval
from more_itertools import pairwise

from annotation.models import helpers


# TODO Region should have a reference?
class Region(Interval, helpers.StrandedPositions): pass


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
        super(Intron, self).__init__(start, end)
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
        self._exons = set()

    # TODO repr or str?
    def __repr__(self):
        return 'Transcript({})'.format(self.gene)

    @property
    def strand(self):
        return self.gene.strand

    # TODO move this sort of stuff to post_transform?
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
    def exons(self):
        # TODO sorting every time sucks. a lot depends on accessing exons.
        reverse = self.strand == '-'
        return sorted(self._exons, key=lambda exon: exon.five_prime,
                      reverse=reverse)

    @property
    def introns(self):
        if not self._introns:
            self.build_introns()
        return self._introns

    def build_introns(self):
        for a, b in pairwise(self.exons):
            if self.strand == '-':
                intron = self.Intron(b.five_prime + 1, a.three_prime - 1)
                intron.transcript = self
            else:
                intron = self.Intron(a.three_prime + 1, b.five_prime - 1)
            self._introns.append(intron)


class Exon(Region):

    def __init__(self, start, end):
        super(Exon, self).__init__(start, end)
        self.transcript = None

    def __repr__(self):
        return 'Exon({}, {}, {})'.format(self.start, self.end, self.transcript)

    @property
    def strand(self):
        return self.transcript.strand
