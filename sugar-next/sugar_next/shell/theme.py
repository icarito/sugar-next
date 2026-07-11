"""Sugar Next color token system.

Defines the ``--sn-*`` CSS custom properties used throughout the shell,
computed from the system light/dark preference. Users may override any
token via ``~/.config/sugar-next/colors.css``, loaded after the base
stylesheet so overrides win through the normal CSS cascade.
"""

import colorsys
import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk

try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    _HAS_ADW = True
except (ImportError, ValueError):
    _HAS_ADW = False

#: Default accent used when no user override and no active-app tint apply.
DEFAULT_ACCENT = "#3584e4"

#: Tokens the shell derives from the accent color (see derive_palette).
#: Everything else in the token dicts is a fixed light/dark neutral that
#: carries the readability contract and must not shift with the accent.
DERIVED_TOKENS = ("--sn-accent", "--sn-accent-counter", "--sn-bg-alt", "--sn-surface")

_LIGHT_TOKENS = {
    "--sn-bg": "#f6f6f6",
    "--sn-bg-alt": "#e8e8ea",
    "--sn-accent": DEFAULT_ACCENT,
    "--sn-accent-counter": "#ffffff",
    "--sn-text": "#1a1a1a",
    "--sn-text-secondary": "#5c5c5c",
    "--sn-surface": "#ffffff",
}

_DARK_TOKENS = {
    "--sn-bg": "#1a1a2e",
    "--sn-bg-alt": "#282850",
    "--sn-accent": DEFAULT_ACCENT,
    "--sn-accent-counter": "#ffffff",
    "--sn-text": "#f0f0f0",
    "--sn-text-secondary": "#b0b0b8",
    "--sn-surface": "#242438",
}


def _hex_to_rgb(value: str) -> tuple:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple) -> str:
    return "#" + "".join(
        f"{max(0, min(255, round(c * 255))):02x}" for c in rgb
    )


def _relative_luminance(rgb: tuple) -> float:
    # WCAG relative luminance, used to pick a legible foreground.
    def _lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (_lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(lum_a: float, lum_b: float) -> float:
    lo, hi = sorted((lum_a, lum_b))
    return (hi + 0.05) / (lo + 0.05)


def derive_palette(accent_hex: str, dark: bool) -> dict:
    """Derive the accent-driven tokens from a single accent color.

    Uses HSL math only (``colorsys``, stdlib) — no perceptual color
    science. ``--sn-bg`` / ``--sn-text`` are intentionally *not* returned:
    they stay neutral so contrast and high-contrast mode remain
    predictable. Returns a dict covering exactly ``DERIVED_TOKENS``.
    """
    try:
        r, g, b = _hex_to_rgb(accent_hex)
    except (ValueError, IndexError):
        r, g, b = _hex_to_rgb(DEFAULT_ACCENT)
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Counterpart: rotate hue ~170° (a near-complement, but nudged off a
    # flat 180° so it stays legible across the hue circle) for its
    # secondary-semantic role, then drive its lightness toward whichever
    # extreme (near-white or near-black) actually clears a legible
    # contrast ratio against the accent — a mid-luminance accent (e.g.
    # green) needs a hard push to one end, not a fixed offset.
    counter_h = (h + 170.0 / 360.0) % 1.0
    counter_s = min(1.0, s * 0.9 + 0.1)
    accent_lum = _relative_luminance((r, g, b))

    def _counter_at(lightness_value):
        return colorsys.hls_to_rgb(counter_h, lightness_value, counter_s)

    # Prefer the direction away from the accent's luminance, but fall back
    # to the other extreme if it reads better.
    light_rgb = _counter_at(0.95)
    dark_rgb = _counter_at(0.10)
    light_contrast = _contrast(accent_lum, _relative_luminance(light_rgb))
    dark_contrast = _contrast(accent_lum, _relative_luminance(dark_rgb))
    cr, cg, cb = light_rgb if light_contrast >= dark_contrast else dark_rgb

    # Surfaces: keep the base neutral's lightness (readability contract),
    # only shift hue toward the accent and lend a faint saturation so the
    # chrome reads as "tinted", not repainted.
    base = _DARK_TOKENS if dark else _LIGHT_TOKENS

    def _tint(token_hex: str, sat: float) -> str:
        tr, tg, tb = _hex_to_rgb(token_hex)
        _, tl, _ = colorsys.rgb_to_hls(tr, tg, tb)
        nr, ng, nb = colorsys.hls_to_rgb(h, tl, sat)
        return _rgb_to_hex((nr, ng, nb))

    return {
        "--sn-accent": _rgb_to_hex((r, g, b)),
        "--sn-accent-counter": _rgb_to_hex((cr, cg, cb)),
        "--sn-bg-alt": _tint(base["--sn-bg-alt"], 0.22),
        "--sn-surface": _tint(base["--sn-surface"], 0.10),
    }

#: Token overrides applied on top of the base palette when contrast is
#: set to "high" — wider gap between text and background, no mid-gray.
_HIGH_CONTRAST_LIGHT = {
    "--sn-text": "#000000",
    "--sn-text-secondary": "#000000",
    "--sn-bg": "#ffffff",
    "--sn-surface": "#ffffff",
}

_HIGH_CONTRAST_DARK = {
    "--sn-text": "#ffffff",
    "--sn-text-secondary": "#ffffff",
    "--sn-bg": "#000000",
    "--sn-surface": "#000000",
}


def config_dir() -> Path:
    config_home = os.environ.get(
        "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
    )
    return Path(config_home) / "sugar-next"


def colors_override_file() -> Path:
    return config_dir() / "colors.css"


def prefers_dark() -> bool:
    if _HAS_ADW:
        style_manager = Adw.StyleManager.get_default()
        return style_manager.get_dark()
    settings = Gtk.Settings.get_default()
    if settings is not None:
        return bool(settings.get_property("gtk-application-prefer-dark-theme"))
    return True


def _tokens_css(tokens: dict) -> str:
    lines = ["window {"]
    for name, value in tokens.items():
        lines.append(f"    {name}: {value};")
    lines.append("}")
    return "\n".join(lines)


def _parse_override_file(path: Path) -> dict:
    """Read ``--sn-*: value;`` declarations from a colors.css file.

    Tolerant of hand-editing: any ``--token: value;`` pair is picked up
    regardless of the surrounding selector/braces. Returns {} if the file
    is missing or unreadable.
    """
    overrides = {}
    try:
        text = path.read_text()
    except OSError:
        return overrides
    for raw in text.replace("{", "\n").replace("}", "\n").split("\n"):
        line = raw.strip().rstrip(";").strip()
        if not line.startswith("--") or ":" not in line:
            continue
        name, _, value = line.partition(":")
        name = name.strip()
        value = value.strip()
        if name and value:
            overrides[name] = value
    return overrides


class ThemeManager:
    """Loads the token providers and manages accent-derived colors.

    Provider cascade (low → high priority):

    1. ``_base_provider`` — fixed light/dark neutral tokens.
    2. ``_tint_provider`` — the accent-derived palette (regenerated
       whenever the accent changes).
    3. ``_override_provider`` — per-token manual overrides, persisted to
       ``colors.css`` so they win over the generated palette.
    4. ``_contrast_provider`` — high-contrast neutral overrides.
    """

    def __init__(self):
        self._base_provider = Gtk.CssProvider()
        self._override_provider = Gtk.CssProvider()
        self._tint_provider = Gtk.CssProvider()
        self._contrast_provider = Gtk.CssProvider()
        self._dark = prefers_dark()
        self._tokens = dict(_DARK_TOKENS if self._dark else _LIGHT_TOKENS)
        self._accent = DEFAULT_ACCENT
        self._contrast_level = "normal"
        #: token name -> value, manually set by the user; wins over derived.
        self._overrides = _parse_override_file(colors_override_file())

    def apply(self, display=None):
        display = display or Gdk.Display.get_default()
        self._base_provider.load_from_string(_tokens_css(self._tokens))
        Gtk.StyleContext.add_provider_for_display(
            display, self._base_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        Gtk.StyleContext.add_provider_for_display(
            display,
            self._tint_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
        )
        Gtk.StyleContext.add_provider_for_display(
            display,
            self._override_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2,
        )
        Gtk.StyleContext.add_provider_for_display(
            display,
            self._contrast_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 3,
        )
        self._reload_overrides()

    def set_contrast(self, level):
        """*level* is ``"normal"`` or ``"high"``."""
        self._contrast_level = level
        if level != "high":
            self._contrast_provider.load_from_string("")
            return
        overrides = _HIGH_CONTRAST_DARK if self._dark else _HIGH_CONTRAST_LIGHT
        self._contrast_provider.load_from_string(_tokens_css(overrides))

    def set_dark_mode(self, is_dark):
        """Toggle between light and dark mode."""
        self._dark = is_dark
        self._tokens = dict(_DARK_TOKENS if is_dark else _LIGHT_TOKENS)
        self._base_provider.load_from_string(_tokens_css(self._tokens))
        self.set_accent_tint(self._accent)
        self.set_contrast(self._contrast_level)

    def set_accent_tint(self, hex_color):
        """Set the accent and regenerate the derived palette from it.

        Passing ``None`` clears the derived layer, falling back to the
        fixed base tokens (used when no accent override applies).
        """
        if hex_color is None:
            self._tint_provider.load_from_string("")
            return
        self._accent = hex_color
        palette = derive_palette(hex_color, self._dark)
        self._tint_provider.load_from_string(
            "window {\n"
            + "".join(f"    {name}: {value};\n" for name, value in palette.items())
            + "}"
        )

    def derived_palette(self):
        """The current accent-derived token values (for the Settings UI)."""
        return derive_palette(self._accent, self._dark)

    def override_value(self, token):
        """The user override for *token*, or None if it is auto-derived."""
        return self._overrides.get(token)

    def set_override(self, token, hex_color):
        """Pin *token* to *hex_color*, persisting it to ``colors.css``."""
        self._overrides[token] = hex_color
        self._persist_overrides()

    def clear_override(self, token):
        """Drop the user override for *token*, reverting to the derived value."""
        if token in self._overrides:
            del self._overrides[token]
            self._persist_overrides()

    def _reload_overrides(self):
        if self._overrides:
            self._override_provider.load_from_string(_tokens_css(self._overrides))
        else:
            self._override_provider.load_from_string("")

    def _persist_overrides(self):
        path = colors_override_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._overrides:
            path.write_text(_tokens_css(self._overrides) + "\n")
        elif path.is_file():
            path.write_text("")
        self._reload_overrides()

    def token(self, name):
        return self._tokens.get(name)


#: Shared theme manager used by the shell.
manager = ThemeManager()
