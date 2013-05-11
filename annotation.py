import types

import interval
from more_itertools import pairwise


class PositionHelpers(object):

    @property
    def five_prime(self):
        return self.end if self.strand == '-' else self.start

    @property
    def three_prime(self):
        return self.start if self.strand == '-' else self.end


class Region(interval.Closed, PositionHelpers): pass


class Annotation(object):

    def __init__(self, references):
        self.references = references

    @property
    def genes(self):
        for ref in self.references:
            for gene in ref.genes:
                yield gene

    @property
    def transcripts(self):
        for gene in self.genes:
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


class Reference(object):
    def __init__(self, name, size, genes=None):
        self.name = name
        self.size = size
        self.genes = []
        if genes:
            for gene in genes:
                gene.reference = self
                self.genes.append(gene)


class Gene(Region):
    def __init__(self, strand, transcripts=None):
        self.strand = strand

        self.reference = None
        self.transcripts = []
        if transcripts:
            for transcript in transcripts:
                transcript.gene = self
                self.transcripts.append(transcript)

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

    def __init__(self, exons=None):
        self.gene = None
        self._exons = []
        if exons:
            for exon in exons:
                exon.transcript = self
                self._exons.append(exon)

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


class Exon(Region):
    def __init__(self, start, end):
        self.transcript = None
        self.start = start
        self.end = end

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


class AnnotationBuilderMeta(type):
    def __new__(cls, name, bases, attrs):
        handlers = {}
        attrs['handlers'] = handlers

        handlers_cls = attrs.get('Handlers')
        if handlers_cls:
            for key, value in handlers_cls.__dict__.items():
                if isinstance(value, types.FunctionType):
                    handlers[key] = value

            aliases = getattr(handlers_cls, 'aliases')
            if aliases:
                for key, value in aliases.items():
                    handlers[key] = value

            del attrs['Handlers']

        return super(AnnotationBuilderMeta, cls).__new__(cls, name, bases, attrs)
        

class AnnotationBuilderBase(object):
    __metaclass__ = AnnotationBuilderMeta


class AnnotationBuilder(AnnotationBuilderBase):

    # TODO and if a record has multiple parents? Duplicate it?

    class Handlers:

        def reference(record, parent):
            ref = Reference(record.ID, record.end)
            ref.parent = parent
            return ref

        def gene(record, parent):
            gene = Gene(record.strand)
            gene.reference = parent
            return gene

        def transcript(record, parent):
            t = Transcript()
            t.gene = parent
            return t

        def exon(record, parent):
            e = Exon(record.start, record.end)
            e.transcript = parent
            return e

        aliases = {}

    def __call__(self, tree):

        def func(node, parent=None):

            handler = self.handlers[node.record.type]
            x = handler(node.record, parent)

            for child in node.children:
                func(child, x)

            return x

        anno = Annotation()
        refs = []
        for child in tree.root.children:
            ref = func(child, anno)
            refs.append(ref)

        return anno
