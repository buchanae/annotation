from collections import namedtuple

import nose
from nose.tools import eq_

import annotation


Record = namedtuple('Record', 'ID start end strand type children')

exon_a = Record('exon_a', 20, 30, '+', 'exon', [])
exon_b = Record('exon_b', 40, 50, '+', 'exon', [])
exon_c = Record('exon_c', 60, 70, '+', 'exon', [])

transcript_a = Record('transcript_a', 20, 70, '+', 'transcript',
                      [exon_a, exon_b, exon_c])

exon_d = Record('exon_a', 20, 30, '+', 'exon', [])
exon_e = Record('exon_b', 40, 50, '+', 'exon', [])

transcript_b = Record('transcript_b', 20, 50, '+', 'transcript',
                      [exon_d, exon_e])

gene_a = Record('gene_a', 20, 70, '+', 'gene', [transcript_a, transcript_b])

unhandled_a = Record('unhandled_a', 0, 0, '', 'unhandled', [])

ref_a = Record('ref_a', 1, 300, '+', 'reference', [gene_a, unhandled_a])


def test_AnnotationBuilder():
    builder = annotation.AnnotationBuilder()

    anno = builder([ref_a])
    eq_(len(anno.references), 1)

    ref = anno.references[0]
    eq_(ref.name, 'ref_a')
    eq_(ref.size, 300)
    eq_(len(ref.genes), 1)

    gene = ref.genes[0]
    eq_(gene.strand, '+')
    eq_(len(gene.transcripts), 2)

    transcript_a, transcript_b = gene.transcripts
    eq_(len(transcript_a.exons), 3)
    eq_(len(transcript_b.exons), 2)

    exon_a, exon_b, exon_c = transcript_a.exons
    exon_d, exon_e = transcript_b.exons

    eq_(exon_a.start, 20)
    eq_(exon_a.end, 30)
    eq_(exon_b.start, 40)
    eq_(exon_b.end, 50)
    eq_(exon_c.start, 60)
    eq_(exon_c.end, 70)
    eq_(exon_d.start, 20)
    eq_(exon_d.end, 30)
    eq_(exon_e.start, 40)
    eq_(exon_e.end, 50)


def test_handler_aliases():
    pass


if __name__ == '__main__':
    nose.main()
