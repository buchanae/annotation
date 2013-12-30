import itertools

from annotation import Annotation, models, exporters
import fasta
from gff import GFF

"""
Use cases:
x 1. Recognize a new gff type and map to an existing feature class
   e.g. recognize "foo_gene" and return a Gene instance

x 2. Replace a feature class, such as Transcript, with a custom version

3. Add a new feature class, such as CDS

4. Add a new import format, such as genbank

5. Handle missing reference records

6. Extend to hook into other data, such as sequence or iprscan.
   Allow this to be independent of the importer, if possible,
   e.g. so that it's not necessary to manually configure all importers
   (GFF, Genbank, XYZ, etc) with the sequence/iprscan/other database info

7. Export to GFF

8. Handle multiple parents in GFF
"""

class CustomReference(models.Reference):
    def update_GFF(self, record):
        record.seqid = self.ID
        record.start = 1
        record.end = self.size


class CustomGene(models.Gene):
    def __init__(self, ID, strand, source):
        super(CustomGene, self).__init__(ID, strand)
        self.source = source

    @classmethod
    def from_GFF(cls, record):
        return cls(record.ID, record.strand, record.source)

    def update_GFF(self, record):
        record.parent_ID = self.reference.ID


class CustomTranscript(models.Transcript):
    def __init__(self, ID, source):
        super(CustomTranscript, self).__init__(ID)
        self.source = source

    # TODO does this belong on the model? I can't decide. I think not
    #      but it seems like a more simple API. but, it couples to
    #      a specific GFF API, whereas a more decoupled approach would
    #      be to define this on the GFF Importer that has its own GFF API.
    #      on the other hand, it's really only coupled to an interface,
    #      and a reasonable and reliable one at that.
    @classmethod
    def from_GFF(cls, record):
        return cls(record.ID, record.source)

    def update_GFF(self, record):
        record.parent_ID = self.gene.ID


class CustomExon(object):
    def update_GFF(self, record):
        record.parent_ID = self.transcript.ID


# TODO what if models could tell builders what hooks/handlers they have/need?


class CustomAnnotation(Annotation):
    Reference = CustomReference
    Gene = CustomGene
    Transcript = CustomTranscript

    def __init__(self, sequences):
        super(CustomAnnotation, self).__init__()

        self.sequences = sequences

        self.gff_builder.Reference_types.append('fooref')

    @classmethod
    def from_GFF(cls, records, sequences):
        anno = cls(sequences)
        anno.gff_builder.from_GFF(records)
        return anno


def read_genome(fh):
    """
    The headers in the genome sequence file don't match the IDs in the GFF file.
    This helper fixes that.
    """

    name_map = {
        'chloroplast': 'ChrC',
        'mitochondria': 'ChrM',
    }

    for rec in fasta.parse(fh):
        name = rec.header.split()[0]
        name = name_map.get(name, name)
        yield name, rec.sequence


if __name__ == '__main__':
    #fh = open('combined_genome.fas')
    #sequences = dict(read_genome(fh))
    sequences = {}

    fh = open('annotation.gff')
    records = GFF.from_stream(fh)
    records = itertools.islice(records, 10)
    anno = CustomAnnotation.from_GFF(records, sequences)


    def generate_all_features(anno):
        for reference in anno.references:
            yield reference

            for gene in reference.genes:
                yield gene

                for transcript in gene.transcripts:
                    yield transcript

                    for exon in transcript.exons:
                        yield exon

                #transcript.five_prime_UTR

                #transcript.CDS

                #transcript.three_prime_UTR

    all_features = generate_all_features(anno)

    gff_exporter = exporters.gff.GFFExporter(GFF)
    gff_exporter.defaults['source'] = 'custom_source'

    out = gff_exporter.iterbuild(all_features)
    print out.next()
    #for rec in gff_exporter.iterbuild(all_features):
        #print rec
