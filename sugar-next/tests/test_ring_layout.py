import math

from sugar_next.shell.ring_layout import ring_counts, ring_positions


def test_empty():
    assert ring_counts(0) == []
    assert ring_positions(0) == []


def test_single_ring_when_it_fits():
    # Base ring holds 6; five items stay on one ring.
    assert ring_counts(5, base_per_ring=6) == [5]


def test_grows_into_concentric_rings():
    # 6 fills ring 0; the next 12 fill ring 1; overflow to ring 2.
    assert ring_counts(6, base_per_ring=6) == [6]
    assert ring_counts(7, base_per_ring=6) == [6, 1]
    assert ring_counts(18, base_per_ring=6) == [6, 12]
    assert ring_counts(19, base_per_ring=6) == [6, 12, 1]


def test_positions_have_growing_radius_per_ring():
    pos = ring_positions(19, base_per_ring=6)
    assert len(pos) == 19
    # Ring index carried on each position; radius = ring_index + 1.
    for x, y, ring in pos:
        radius = math.hypot(x, y)
        assert math.isclose(radius, ring + 1, rel_tol=1e-9)
    # Three rings present for 19 items.
    assert {ring for _, _, ring in pos} == {0, 1, 2}


def test_first_item_starts_at_top():
    (x, y, ring) = ring_positions(6)[0]
    assert ring == 0
    assert math.isclose(x, 0.0, abs_tol=1e-9)
    assert math.isclose(y, -1.0, rel_tol=1e-9)  # straight up
