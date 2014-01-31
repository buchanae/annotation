import collections
import logging


log = logging.getLogger(__name__)


class StrandedPositions(object):
    '''Some basic helpers for genomic positions.'''

    @property
    def five_prime(self):
        return self.end if self.reverse_strand else self.start

    @property
    def three_prime(self):
        return self.start if self.reverse_strand else self.end


class TranscriptPositions(object):

    def rel_to_abs(self, rel):
        if rel < 1 or rel > self.length:
            # TODO better exception and/or message here
            raise IndexError()

        l = 0
        sort_key = lambda exon: exon.start
        exons = sorted(self.exons, key=sort_key, reverse=self.reverse_strand)

        for exon in exons:
            if l <= rel <= l + exon.length:
                if self.reverse_strand:
                    return exon.five_prime - (rel - l - 1)
                else:
                    return exon.five_prime + (rel - l - 1)

            l += exon.length

    def abs_to_rel(self, abs_pos):
        if abs_pos < self.start or abs_pos > self.end:
            # TODO better error class and/or message
            raise IndexError()

        l = 0
        sort_key = lambda exon: exon.start
        exons = sorted(self.exons, key=sort_key, reverse=self.reverse_strand)

        for exon in exons:
            if abs_pos in exon:
                if self.reverse_strand:
                    return exon.five_prime - abs_pos + 1 + l
                else:
                    return abs_pos - exon.five_prime + 1 + l
            l += exon.length

        # At this point, the abs_pos didn't fall within an exon,
        # i.e. it's probably in an intron.
        # TODO better error class and/or message
        raise IndexError()


class ExonCollection(collections.Sequence):

    def __init__(self):
        self._exons = []
        self._dirty = False

    @property
    def _sorted_exons(self):
        if self._dirty:
            sort_key = lambda exon: exon.start
            self._exons = sorted(self._exons, key=sort_key)
            self._dirty = False
        return self._exons

    def add(self, exon):
        self._dirty = True
        self._exons.append(exon)
        # TODO could add collections.MutableSet ABC
        # TODO could check that adding an exon doesn't overlap with existing exons
        # TODO could implment with a bisect search + insert

    def remove(self, exon):
        try:
            self._exons.remove(exon)
        except ValueError:
            raise ValueError('ExonCollection.remove(x): x is not in the collection')

    def __len__(self):
        return len(self._exons)

    def __getitem__(self, key):
        return self._sorted_exons[key]

    def __delitem__(self, key):
        del self._sorted_exons[key]
