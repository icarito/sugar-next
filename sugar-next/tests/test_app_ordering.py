from sugar_next.shell.app_ordering import order_apps


class _Bundle:
    def __init__(self, app_id, name):
        self.app_id = app_id
        self.name = name


def test_favorites_first_then_mru_then_alphabetical():
    apps = [
        _Bundle("zoo.desktop", "Zoo"),
        _Bundle("apple.desktop", "Apple"),
        _Bundle("firefox.desktop", "Firefox"),
        _Bundle("calc.desktop", "Calculator"),
        _Bundle("banana.desktop", "Banana"),
    ]
    favorites = ["firefox.desktop"]
    # Calculator launched more recently than Zoo.
    mru = ["calc.desktop", "zoo.desktop"]

    ordered = [b.app_id for b in order_apps(apps, favorites, mru)]

    assert ordered == [
        "firefox.desktop",  # favorite, first
        "calc.desktop",     # MRU[0]
        "zoo.desktop",      # MRU[1]
        "apple.desktop",    # never-launched, alphabetical
        "banana.desktop",
    ]


def test_normalized_ids_match_across_desktop_suffix():
    apps = [_Bundle("firefox.desktop", "Firefox"), _Bundle("gimp.desktop", "GIMP")]
    # favorites/mru stored without the .desktop suffix still match.
    ordered = [b.app_id for b in order_apps(apps, ["gimp"], ["firefox"])]
    assert ordered == ["gimp.desktop", "firefox.desktop"]


def test_empty_favorites_and_mru_is_alphabetical():
    apps = [_Bundle("b.desktop", "Beta"), _Bundle("a.desktop", "Alpha")]
    ordered = [b.app_id for b in order_apps(apps, [], [])]
    assert ordered == ["a.desktop", "b.desktop"]
