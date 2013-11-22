from __future__ import absolute_import

from interval.closed import Interval
from more_itertools import pairwise

import sequence_utils

from annotation import gff_types
from annotation.builders import GFFBuilder, Handler


__version__ = '2.0.0'


class PositionHelpers(object):

    @property
    def five_prime(self):
        return self.end if self.strand == '-' else self.start

    @property
    def three_prime(self):
        return self.start if self.strand == '-' else self.end


class TreeNode(object):
    def __init__(self):
        self._parent = None
        self.children = []

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        # If this node already has a parent,
        # delete this node from that parent's children
        if self._parent:
            self._parent.children.remove(self)
        self._parent = value
        self._parent.children.append(self)


class Region(Interval, PositionHelpers): pass


class Reference(TreeNode):
    def __init__(self, name, size):
        super(Reference, self).__init__()
        self.name = name
        self.size = size

    @classmethod
    def from_GFF(cls, record):
        return cls(record.ID, record.end)


class Gene(Region, TreeNode):
    def __init__(self, strand):
        TreeNode.__init__(self)
        self.strand = strand

    @classmethod
    def from_GFF(cls, record):
        return cls(record.strand)

    @property
    def start(self):
        return min(t.start for t in self.transcripts)

    @property
    def end(self):
        return max(t.end for t in self.transcripts)

    # TODO find an appropriate place for sequence stuff
    def sequence(self, genome):
        # TODO handle strand, i.e. reverse complement 
        return genome[self.reference.name][self.start - 1:self.end]


class Intron(Region, TreeNode):

    def __init__(self, start, end, transcript):
        TreeNode.__init__(self)
        Region.__init__(self, start, end)
        self.transcript = transcript

    @property
    def strand(self):
        return self.transcript.strand

    @property
    def reference(self):
        return self.transcript.gene.reference

    @property
    def donor(self):
        return self.five_prime

    @property
    def acceptor(self):
        return self.three_prime

    def __repr__(self):
        return 'Intron({}, {}, {})'.format(self.start, self.end, self.transcript)


class Transcript(TreeNode):

    Intron = Intron

    @classmethod
    def from_GFF(cls, record):
        return cls()

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
    def exons(self):
        reverse = self.strand == '-'
        return sorted(self._exons, key=lambda exon: exon.five_prime,
                      reverse=reverse)

    @property
    def introns(self):
        # TODO
        pass

    def build_introns(self):
        for a, b in pairwise(self.exons):
            if self.strand == '-':
                self.Intron(b.five_prime + 1, a.three_prime - 1, self)
            else:
                self.Intron(a.three_prime + 1, b.five_prime - 1, self)

    @property
    def length(self):
        return sum(exon.length for exon in self.exons)

    def rel_to_abs(self, rel):
        if rel < 1 or rel > self.length:
            # TODO better exception and/or message here
            raise IndexError()

        l = 0
        for exon in self.exons:
            if l <= rel <= l + exon.length:
                if self.strand == '-':
                    return exon.five_prime - (rel - l - 1)
                else:
                    return exon.five_prime + (rel - l - 1)

            l += exon.length


class Exon(Region, TreeNode):

    def __init__(self, start, end):
        TreeNode.__init__(self)
        Region.__init__(self, start, end)
        self.start = start
        self.end = end

    @classmethod
    def from_GFF(cls, record):
        return cls(record.start, record.end)

    @property
    def strand(self):
        return self.transcript.strand

    @property
    def reference(self):
        return self.transcript.gene.reference



def make_introns(transcript):
    pass

def transcript_post_transform(transcript, node):
    make_introns(transcript)

reference_handler = Handler(gff_types.reference_types, Reference.from_GFF)

gene_handler = Handler(gff_types.gene_types, Gene.from_GFF)

transcript_handler = Handler(gff_types.transcript_types, Transcript.from_GFF,
                             transcript_post_transform)

exon_handler = Handler(gff_types.exon_types, Exon.from_GFF)

default_handlers = [
    reference_handler,
    gene_handler,
    transcript_handler,
    exon_handler,
]

default_builder = GFFBuilder(default_handlers)
        

class Annotation(TreeNode):

    # TODO the way I'm adding these builder methods seems a little weird to me
    builder = default_builder

    @classmethod
    def from_GFF_tree(cls, tree):
        anno = cls()
        cls.builder.from_tree(tree, anno)
        return anno

    @classmethod
    def from_GFF(cls, records):
        anno = cls()
        cls.builder.from_records(records, anno)
        return anno

    @classmethod
    def from_GFF_file(cls, path):
        anno = cls()
        cls.builder.from_file(path, anno)
        return anno
