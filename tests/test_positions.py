from nose.tools import eq_, assert_raises


def test_GenomicPosition():
    o = GenomicPosition()
    eq_(o, 1)

    p = GenomicPosition(5)

    eq_(p, 5)

    eq_(p.upstream(2), 3)
    eq_(p.downstream(2), 7)


    q = GenomicPosition(5, reverse_strand=True)
    eq_(q, 5)

    eq_(q.upstream(2), 7)
    eq_(q.downstream(2), 3)

    r = p + 5
    assert isinstance(r, GenomicPosition)
    eq_(r, 10)

    s = 5 + p
    assert isinstance(s, GenomicPosition)
    eq_(s, 10)


    eq_(GenomicPosition.from_zero_based(0), 1)

    # converts to int type
    t = int(p)
    assert isinstance(t, int)
    eq_(t, 5)

    # works in slices
    eq_(range(20)[:p], [0, 1, 2, 3, 4])

    # increment works
    u = GenomicPosition(5)
    u += 5
    assert isinstance(u, GenomicPosition)
    eq_(u, 10)

    eq_(u._pos, 10)

    class Exon(object):
        start = GenomicPositionDescriptor('_start')

    e = Exon()
    eq_(e.start, 1)
    eq_(e.start.downstream(2), 3)

    e.start = 10
    assert isinstance(e.start, GenomicPosition)

    eq_(e.start.downstream(2), 12)

    with assert_raises(ValueError):
        v = GenomicPosition(0)


    with assert_raises(ValueError):
        v = GenomicPosition(1)
        v.upstream(1)


    with assert_raises(ValueError):
        v = GenomicPosition(1, reverse_strand=True)
        v.downstream(1)
