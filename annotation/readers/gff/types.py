import re


class DefaultTypes(object):

    # Helper for turning a whitespace-separated string into a set
    _split = lambda _, s: set(re.split('\s', s))

    def __init__(self):
        self.Reference = self._split('''
            reference
            chromosome
            contig
        ''')

        self.Gene = self._split('''
            gene
            pseudogene
            transposable_element_gene
        ''')

        self.Transcript = self._split('''
            mRNA
            snRNA 
            rRNA
            snoRNA
            mRNA_TE_gene
            miRNA
            tRNA
            ncRNA
            pseudogenic_transcript
        ''')

        self.Exon = self._split('''
            exon
            pseudogenic_exon
        ''')

        self.CodingSequence = self._split('''
            CDS
        ''')


default_types = DefaultTypes()
