"""Ordering and filtering of app bundles for the Home View.

The Home View shows a set of apps arranged by a *mode* (layout) and
narrowed by a *filter* (which apps). Both the ordering (favorites first,
then most-recently-used, then alphabetical) and the favorites-file access
are shared by the current app grid and the unified Home View, so they live
here rather than being duplicated per widget.
"""

import json
import os
from pathlib import Path

from sugar_next.shell.app_state import normalize_app_id


def favorites_file() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    return Path(data_home) / "sugar-next" / "favorites.json"


def load_favorites() -> list:
    """Return the list of pinned favorite app ids (order preserved)."""
    path = favorites_file()
    if path.is_file():
        try:
            return list(json.loads(path.read_text()))
        except ValueError:
            pass
    return []


def order_apps(apps, favorite_ids, mru_order):
    """Order *apps* by favorites first, then MRU, then alphabetical.

    *apps* is any iterable of bundles (each with ``app_id`` and ``name``).
    *favorite_ids* and *mru_order* are lists of app ids; comparison is by
    normalized id so ``.desktop``-suffixed and bare ids match. Favorites
    keep their pinned order; MRU keeps its recency order; everything else
    falls to the end alphabetically by name.
    """
    fav = [normalize_app_id(a) for a in favorite_ids]
    mru = [normalize_app_id(a) for a in mru_order]

    def rank(bundle):
        norm = normalize_app_id(bundle.app_id)
        if norm in fav:
            return (0, fav.index(norm))
        if norm in mru:
            return (1, mru.index(norm))
        return (2, bundle.name.lower())

    return sorted(apps, key=rank)
