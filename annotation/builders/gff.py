from __future__ import absolute_import

import logging

import gff

from annotation.builders.core import Builder, Linker


REFERENCE_TYPES = [
    'reference',
    'chromosome',
    'contig',
]

GENE_TYPES = [
    'gene',
    'pseudogene',
    'transposable_element_gene',
]

TRANSCRIPT_TYPES = [
    'mRNA',
    'snRNA', 
    'rRNA',
    'snoRNA',
    'mRNA_TE_gene',
    'miRNA',
    'tRNA',
    'ncRNA',
    'pseudogenic_transcript',
]

EXON_TYPES = [
    'exon',
    'pseudogenic_exon',
]

log = logging.getLogger('annotation.builders.gff')


_multiple_parents_error_msg = "A record with multiple parents was found. Currently this library doesn't know how to handle that. Try using the MultipleParentsGeneHandler."

class MultipleParentsError(Exception):
    def __init__(self):
        super(MultipleParentsError, self).__init__(_multiple_parents_error_msg)

class GFF(gff.GFF):

    @property
    def parent_ID(self):
        parent_IDs = self.parent_IDs

        if parent_IDs:
            if len(parent_IDs) > 1:
                # Note: this library doesn't yet know how to handle multiple parents.
                #       We raise an exception to ensure the user knows that.
                raise MultipleParentsError()
            else:
                return parent_IDs[0]


#class Annotation:
    #Transcript = CustomTranscript
    
    # Define the relationships between models
    #parent_child('Gene.transcripts', 'Transcript.gene')


#class AnnotationWithProteins:
    #Protein = Protein
    #parent_child('Transcript.proteins', 'Protein.transcript')

# OR

# Begging for name conflicts
#annotation.model(CustomTranscript, name='Transcript')
#annotation.model(Protein)

#annotation.parent_child('Gene.transcripts', 'Transcript.gene')

#linker = Linker()
#linker.add_pattern('reference')
#linker.add_pattern('gene')
#linker.add_pattern('transcript')
