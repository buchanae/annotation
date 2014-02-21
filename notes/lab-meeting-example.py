import annotation


gff_file = open('path/to/annotation.gff')
anno = annotation.from_GFF(gff_file)


# Only GFF is supported so far, but other formats could be added
anno = annotation.from_GenBank(genbank_file)


genome_sequences = load_genome_sequence('path/to/genome.fasta')
anno.sequences.update(genome_sequences)


# Easily loop through features
for reference in anno.references:
    for gene in reference.genes:

        if gene.reverse_strand:
            print 'This gene is on the reverse strand'
            print gene.ID, gene.start, gene.end, gene.length


        # Features are linked to their parents as well
        print gene.reference.ID


        for transcript in gene.transcripts:

            # A transcript's length is the sum of the length of its exons
            print transcript.length

            for exon in transcript.exons:
                pass

            for intron in transcript.introns:
                # Helpers for working with genomic positions in an obvious way.
                print intron.donor.upstream(25)
                print intron.acceptor.downstream(50)

                # Positions have normal arithmetic operations
                print intron.donor + 10
                print intron.acceptor - 10

                print intron.five_prime
                print intron.three_prime


            # Need to convert between relative and absolute positions?
            print transcript.rel_to_abs(15)
            print transcript.abs_to_rel(35502)


            # Access to feature sequences
            # Note, I'm not sure I like this, but it's possible
            print transcript.sequence

            if transcript.cds:
                print transcript.cds.amino_acid_sequence
                print transcript.cds.signal_peptide

            # TODO there's a line to walk between what should and shouldn't
            #      be included in the annotation model. Should ORFs be included?
            #      probably not.
            print transcript.orfs


        # For PCU, I created an extension for dealing with alternative splicing
        for retained in gene.retained_introns():
            do_something_useful(retained)


        # Also for PCU, I created an extension for adding/removing introns
        transcript.introns[2].remove()


        # You might want to modify the features and write them back out
        transcript.exons[0].start += 5



gff_exporter = annotation.exporters.GFFExporter()
gff_exporter.defaults['source'] = 'custom source field'

for record in gff_exporter.export(anno):
    print record
