1. Recognize a new type of GFF record:

   For example, your GFF file contains a "lincRNA" type which you'd like to
   treat as a Transcript model.

       # Create a Reader
       reader = annotation.readers.gff.Reader()
       reader.types.add('lincRNA')


2. Recognize completely different types of GFF records:

   This is a contrived example. Let's say you had a GFF file with record types
   completely different from the types recognized by default.

   You want to recognize these types and map them to the existing models.

       # Define a types class
       class CustomTypes(TypesBase):
           Reference = {'custom_reference'}

           Gene = {
               'custom_gene',
               'other_custom_gene',
           }

           Transcript = {
           }

           Exon = {}
           CodingSequence = {}



3. Use a custom Gene model

       from annotation.models import Gene as GeneBase

       class Gene(GeneBase):
           def custom_method(self):
               return 'foo'

       reader = annotation.readers.gff.Reader()
       reader.models.Gene = Gene



4. Read only gene records

   This example is more in depth. Sometimes you don't care about transcripts
   and exons and all that detail, you just want references and genes.
   This is fairly easy to accomplish by creating your own reader.

   TODO this could be easier

   from annotation.readers.gff import Reader as ReaderBase

   class GenesOnlyReader(AnnotationReaderBase):

       def init_builder(self, builder):
           b = builder
           m = self.models
           t = self.types
           h = self._handlers

           h.ReferenceHandler(b, m.Reference, t.Reference)
           h.GeneHandler(b, m.Gene, m.Reference, t.Gene)


TODO document why default_handlers is a dict e.g. so you can do:

   custom_handlers = dict(default_handlers).update({
       'decode_exon': custom_exon_decoder,
   })

   essentially overriding the default decode_exon handler
