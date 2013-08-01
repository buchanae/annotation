from interval.closed import Interval
from more_itertools import pairwise

import sequence_utils


class PositionHelpers(object):

    @property
    def five_prime(self):
        return self.end if self.strand == '-' else self.start

    @property
    def three_prime(self):
        return self.start if self.strand == '-' else self.end


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


class Region(Interval, PositionHelpers): pass


class Annotation(object):

    def __init__(self):
        self.references = []

    @property
    def genes(self):
        for ref in self.references:
            for gene in ref.genes:
                yield gene

    @property
    def transcripts(self):
        for gene in self.genes:
            # TODO wrong
            if isinstance(gene, Gene):
                for transcript in gene.transcripts:
                    yield transcript

    @property
    def exons(self):
        for transcript in self.transcripts:
            for exon in transcript.exons:
                yield exon

    @property
    def introns(self):
        for transcript in self.transcripts:
            for intron in transcript.introns:
                yield intron


class ParentChild(object):
    def __init__(self, name, children_name):
        self.name = '_' + name
        self.children_name = children_name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.name)

    def __set__(self, obj, value):
        existing = getattr(obj, self.name, None)
        if existing:
            children = getattr(existing, self.children_name)
            children.remove(obj)

        setattr(obj, self.name, value)
        parent = getattr(obj, self.name)
        children = getattr(parent, self.children_name)
        children.append(obj)


class Reference(object):
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.genes = []

    annotation = ParentChild('annotation', 'references')


class Gene(Region):
    def __init__(self, strand):
        self.strand = strand
        self.transcripts = []

    reference = ParentChild('reference', 'genes')

    @property
    def start(self):
        return min(t.start for t in self.transcripts)

    @property
    def end(self):
        return max(t.end for t in self.transcripts)

    def sequence(self, genome):
        # TODO handle strand, i.e. reverse complement 
        return genome[self.reference.name][self.start - 1:self.end]


class Transcript(object):

    def __init__(self):
        self._exons = []

    gene = ParentChild('gene', 'transcripts')

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
    def exons(self):
        reverse = self.strand == '-'
        return sorted(self._exons, key=lambda exon: exon.five_prime,
                      reverse=reverse)

    @property
    def introns(self):
        introns = []
        for a, b in pairwise(self.exons):
            if self.strand == '-':
                i = Intron(b.five_prime + 1, a.three_prime - 1, self)
            else:
                i = Intron(a.three_prime + 1, b.five_prime - 1, self)
            introns.append(i)
        return introns

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

class Exon(Region):

    def __init__(self, start, end):
        self.start = start
        self.end = end

    transcript = ParentChild('transcript', '_exons')

    @property
    def strand(self):
        return self.transcript.strand

    @property
    def reference(self):
        return self.transcript.gene.reference


class Intron(Region):

    def __init__(self, start, end, transcript):
        super(Intron, self).__init__(start, end)
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


class AnnotationBuilderBase(object):

    # TODO what if a record has multiple parents? Duplicate it?
    def get_handler(self, node): pass

    def handle(self, nodes):
        handled = []
        for node in nodes:
            handler = self.get_handler(node)
            if handler:
                x = handler(node)
                handled.append(x)
        return handled

    __call__ = handle


class AnnotationBuilder(AnnotationBuilderBase):

    aliases = {}

    def __init__(self):
        self._aliases_inverted = {}
        for key, aliases in self.aliases.items():
            for alias in aliases:
                self._aliases_inverted[alias] = key

    def get_handler(self, node):
        name = self._aliases_inverted.get(node.type, node.type)
        return getattr(self, name, None)

    def reference(self, node):
        ref = Reference(node.ID, node.end)

        for child in self.handle(node.children):
            child.reference = ref

        return ref

    def gene(self, node):
        gene = Gene(node.strand)

        for child in self.handle(node.children):
            child.gene = gene

        return gene

    def transcript(self, node):
        t = Transcript()

        for child in self.handle(node.children):
            child.transcript = t

        return t

    def exon(self, node):
        e = Exon(node.start, node.end)
        return e

    def __call__(self, refs):
        anno = Annotation()

        for ref in self.handle(refs):
            ref.annotation = anno

        return anno
