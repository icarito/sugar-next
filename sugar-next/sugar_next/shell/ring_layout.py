"""Concentric-ring placement for the Home View's spiral mode.

Sugar classic arranged favorites on a ring around the central figure, and
grew into additional concentric rings as the count exceeded what one ring
could hold. This keeps the spiral legible with many apps (the "Spiral +
All apps" case) instead of one oversized circle.

The math here is pure — no GTK — so it can be unit-tested. The widget
multiplies these unit offsets by a pixel radius and adds the center.
"""

import math

#: How many items the innermost ring holds. Each subsequent ring holds
#: this many more, so capacity grows outward (6, 12, 18, ...).
_BASE_PER_RING = 6


def ring_counts(total, base_per_ring=_BASE_PER_RING):
    """Distribute *total* items across concentric rings.

    Returns a list of per-ring counts. Ring ``k`` (0-based) holds up to
    ``base_per_ring * (k + 1)`` items; the last ring holds the remainder.
    """
    if total <= 0:
        return []
    counts = []
    remaining = total
    ring = 0
    while remaining > 0:
        capacity = base_per_ring * (ring + 1)
        take = min(capacity, remaining)
        counts.append(take)
        remaining -= take
        ring += 1
    return counts


def ring_positions(total, base_per_ring=_BASE_PER_RING):
    """Unit (x, y, ring) positions for *total* items across rings.

    Each position is a tuple ``(x, y, ring)`` where x/y are in ring units
    (ring 1 sits at radius 1.0, ring 2 at 2.0, ...) with the origin at the
    center; the caller scales by a pixel radius. Items are placed evenly by
    angle within each ring, starting at the top (-90°).
    """
    positions = []
    for ring_index, count in enumerate(ring_counts(total, base_per_ring)):
        radius = ring_index + 1
        step = 2 * math.pi / count
        for i in range(count):
            angle = -math.pi / 2 + i * step
            positions.append(
                (radius * math.cos(angle), radius * math.sin(angle), ring_index)
            )
    return positions
