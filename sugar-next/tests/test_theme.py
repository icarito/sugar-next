import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pytest

from sugar_next.shell.theme import (
    DERIVED_TOKENS,
    ThemeManager,
    colors_override_file,
    derive_palette,
)


@pytest.fixture(autouse=True)
def gtk_display():
    if not Gtk.init_check():
        pytest.skip("no display available for GTK")


def test_apply_does_not_raise_without_override_file(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    manager = ThemeManager()
    manager.apply()


def test_apply_loads_override_file(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    override = colors_override_file()
    override.parent.mkdir(parents=True, exist_ok=True)
    override.write_text("window { --sn-accent: #ff00ff; }")
    manager = ThemeManager()
    manager.apply()


def test_set_accent_tint_and_clear():
    manager = ThemeManager()
    manager.apply()
    manager.set_accent_tint("#00ff00")
    manager.set_accent_tint(None)


def test_set_contrast_high_and_normal():
    manager = ThemeManager()
    manager.apply()
    manager.set_contrast("high")
    manager.set_contrast("normal")


def test_derive_palette_covers_derived_tokens():
    for dark in (False, True):
        palette = derive_palette("#33d17a", dark)
        assert set(palette) == set(DERIVED_TOKENS)
        # Derivation must not touch the neutral readability tokens.
        assert "--sn-bg" not in palette
        assert "--sn-text" not in palette


def test_derive_palette_counterpart_is_legible_on_accent():
    from sugar_next.shell.theme import _hex_to_rgb, _relative_luminance

    def contrast(a, b):
        la, lb = _relative_luminance(_hex_to_rgb(a)), _relative_luminance(
            _hex_to_rgb(b)
        )
        lo, hi = sorted((la, lb))
        return (hi + 0.05) / (lo + 0.05)

    # Green sits at mid-luminance, the hardest case for a counterpart.
    palette = derive_palette("#33d17a", False)
    assert contrast(palette["--sn-accent"], palette["--sn-accent-counter"]) >= 4.5


def test_derive_palette_invalid_accent_falls_back():
    palette = derive_palette("not-a-color", False)
    assert set(palette) == set(DERIVED_TOKENS)


def test_per_token_override_persists_and_clears(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    manager = ThemeManager()
    manager.apply()
    manager.set_override("--sn-surface", "#123456")
    assert manager.override_value("--sn-surface") == "#123456"
    # Persisted to colors.css and re-read by a fresh manager.
    reloaded = ThemeManager()
    assert reloaded.override_value("--sn-surface") == "#123456"
    # Clearing reverts to auto-derived (no override).
    manager.clear_override("--sn-surface")
    assert manager.override_value("--sn-surface") is None
    assert ThemeManager().override_value("--sn-surface") is None


def test_set_accent_tint_regenerates_derived_palette():
    manager = ThemeManager()
    manager.apply()
    manager.set_accent_tint("#e01b24")
    palette = manager.derived_palette()
    assert palette["--sn-accent"] == "#e01b24"
