#!/bin/sh
# Bootstrap Sugar Next on any Linux distro: venv install + desktop entry.
#
# Requires GTK4 and PyGObject from your distro (pip cannot build PyGObject
# without GObject headers):
#   Fedora:      sudo dnf install python3-gobject gtk4
#   Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0
#   Arch:        sudo pacman -S python-gobject gtk4
#
# Installs into a dedicated venv (--system-site-packages, so PyGObject
# resolves against the distro's compiled GI bindings) rather than
# `pip install --user`, which fails outright on PEP 668
# externally-managed distros such as Arch.

set -eu

here="$(cd "$(dirname "$0")" && pwd)"
venv_dir="${XDG_DATA_HOME:-$HOME/.local/share}/sugar-next/venv"

echo "Installing sugar-next from $here into $venv_dir ..."
python3 -m venv --system-site-packages "$venv_dir"
"$venv_dir/bin/pip" install --upgrade pip
"$venv_dir/bin/pip" install "$here"

exec_path="$venv_dir/bin/sugar-next"

bin_dir="${XDG_BIN_HOME:-$HOME/.local/bin}"
mkdir -p "$bin_dir"
ln -sf "$exec_path" "$bin_dir/sugar-next"
case ":$PATH:" in
	*":$bin_dir:"*) ;;
	*) echo "Note: $bin_dir is not on your PATH. Add it, or run sugar-next via $exec_path" >&2 ;;
esac

apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$apps_dir"
cat > "$apps_dir/org.sugarlabs.SugarNext.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Sugar Next
Comment=A Learning Shell for Everyday Computing
Exec=$exec_path
Icon=org.sugarlabs.SugarNext
Categories=System;Education;
MimeType=application/x-sugar-next-journal;
EOF

mime_dir="${XDG_DATA_HOME:-$HOME/.local/share}/mime/packages"
mkdir -p "$mime_dir"
cp "$here/data/org.sugarlabs.SugarNext.mime.xml" "$mime_dir/"
if command -v update-mime-database >/dev/null 2>&1; then
	update-mime-database "${XDG_DATA_HOME:-$HOME/.local/share}/mime" >/dev/null 2>&1 || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
	update-desktop-database "$apps_dir" >/dev/null 2>&1 || true
fi

# Hosted mode (shell-startup spec) needs the sugar-next-windows GNOME
# Shell extension for window-observation — Mutter does not implement
# wlr-foreign-toplevel-management, so this extension is the only way to
# get real window open/close/focus data while developing inside GNOME.
# Only attempt this on a GNOME session; standalone-mode users (Wayfire,
# see session/wayfire.ini) don't need it and won't have gnome-extensions.
gnome_ext_uuid="sugar-next-windows@sugarlabs.org"
gnome_ext_src="$here/extensions/gnome-shell/$gnome_ext_uuid"
case ":${XDG_CURRENT_DESKTOP:-}:" in
	*:GNOME:*)
		if ! command -v gnome-extensions >/dev/null 2>&1; then
			echo "ERROR: GNOME session detected but 'gnome-extensions' is not on PATH." >&2
			echo "Install your distro's gnome-shell package, then re-run bootstrap.sh." >&2
			exit 1
		fi
		gnome_ext_dir="${XDG_DATA_HOME:-$HOME/.local/share}/gnome-shell/extensions/$gnome_ext_uuid"
		mkdir -p "$(dirname "$gnome_ext_dir")"
		rm -rf "$gnome_ext_dir"
		cp -r "$gnome_ext_src" "$gnome_ext_dir"
		if gnome-extensions enable "$gnome_ext_uuid" >/dev/null 2>&1; then
			echo "GNOME Shell extension '$gnome_ext_uuid' installed and enabled."
		else
			# GNOME Shell only discovers new extensions at its own startup
			# (no in-session directory rescan, notably on Wayland where
			# there is no Alt+F2 'r' restart) — this is not a bug in the
			# install, so fail with a specific, actionable next step
			# rather than silently leaving window tracking broken
			# (shell-startup spec: "Bootstrap failure is actionable").
			echo "ERROR: Installed '$gnome_ext_uuid' to $gnome_ext_dir but GNOME Shell" >&2
			echo "could not enable it yet — GNOME Shell only discovers new extensions" >&2
			echo "at its own startup. Log out and back in, then run:" >&2
			echo "  gnome-extensions enable $gnome_ext_uuid" >&2
			exit 1
		fi
		;;
	*)
		echo "No GNOME session detected; skipping the GNOME Shell extension."
		echo "For a standalone session, see sugar-next/session/wayfire.ini."
		;;
esac

# Standalone session entry (shell-startup spec): only offered if Wayfire
# (the verified reference standalone compositor — see design.md D3 in the
# casilda-activity-host change) is present and passwordless sudo is
# available. This is optional and best-effort — unlike the GNOME extension
# above, a missing standalone entry does not break the primary hosted-mode
# workflow, so failure here is a note, not a fatal error.
if command -v wayfire >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
	session_dir="/usr/share/wayland-sessions"
	sudo install -d "$session_dir"
	sudo tee "$session_dir/sugar-next.desktop" >/dev/null <<EOF
[Desktop Entry]
Name=Sugar Next
Comment=Sugar Next learning shell on Wayfire
Exec=wayfire -c $here/session/wayfire.ini
Type=Application
EOF
	echo "Standalone session entry installed: '$session_dir/sugar-next.desktop'."
	echo "Select 'Sugar Next' from your login manager to try it."
else
	echo "Skipping the standalone session entry (needs Wayfire + passwordless"
	echo "sudo). Try it nested instead: wayfire -c $here/session/wayfire.ini"
	echo "Or install manually — see the header comment in session/wayfire.ini."
fi

echo "Done. Launch with 'sugar-next' or from your app menu."
echo "Extensions go in \${XDG_DATA_HOME:-~/.local/share}/sugar-next/extensions/"
