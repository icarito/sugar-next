{
  description = "Sugar Labs GTK4 modernization monorepo devShell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    sugar-artwork-src = {
      url = "github:MostlyKIGuess/sugar-artwork";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, sugar-artwork-src, ... } @ inputs:
    let
      overlay = final: prev: {
        sugarlabs-monorepo = prev.python311.pkgs.buildPythonPackage {
          pname = "sugarlabs-workspace";
          version = "0.121.0";
          format = "pyproject";
          src = self;
          nativeBuildInputs = with final; [
            wrapGAppsHook4
            gobject-introspection
            pkg-config
            dbus
            dbus-glib
          ];
          buildInputs = with final; [
            gtk4
            gtk4.dev
            glib
            glib.dev
            gobject-introspection
            gdk-pixbuf
            librsvg
            dconf
            gsettings-desktop-schemas
            hicolor-icon-theme
            adwaita-icon-theme
            dbus
            dbus-glib
          ];
          propagatedBuildInputs = with final.python311.pkgs; [
            pygobject3
            dbus-python
          ];
          pythonNamespaces = [ "sugar4" "jarabe" ];
        };
      };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];
        };

        sugar-artwork = pkgs.stdenv.mkDerivation {
          pname = "sugar-artwork";
          version = "0.121-local";

          src = sugar-artwork-src;

          nativeBuildInputs = with pkgs; [
            autoconf
            automake
            libtool
            pkg-config
            intltool
            gtk3
            gdk-pixbuf
            librsvg
            xorg.xcursorgen
            python3
            python3Packages.empy
            iconnamingutils
          ];

          buildInputs = with pkgs; [
            gtk3
            gdk-pixbuf
            librsvg
            hicolor-icon-theme
            gtk2
          ];

          preConfigure = ''
            autoreconf -fi
          '';

          configureFlags = [
            "--with-gtk3"
            "--without-gtk2"
            "--enable-icon-theme"
            "--enable-cursor-theme"
          ];
        };

        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pygobject3
          dbus-python
          pytest
          pytest-cov
          ruff
          mypy
          debugpy
          sphinx
          sphinx-rtd-theme
          six
          decorator
          build
          twine
          setuptools
          wheel
        ]);

        gtkDeps = with pkgs; [
          gtk4
          gtk4.dev
          gobject-introspection
          glib
          glib.dev
          gdk-pixbuf
          librsvg
          dconf
          gsettings-desktop-schemas
          hicolor-icon-theme
          adwaita-icon-theme
          dbus
          dbus-glib
          gtk3
          gtk3.dev
        ];

        waylandDeps = with pkgs; [
          wayland
          wayland-protocols
          wayland-scanner
          wlroots_0_20
          pixman
          xorg.xcbutil
          xorg.libxcb
          xorg.xcbproto
          libxkbcommon
          mesa
          libdrm
          seatd
        ];

        mutterDeps = with pkgs; [
          mutter
          mutter.dev
          graphene
          json-glib
          libinput
          pipewire
          libcanberra-gtk3
          upower
          gnome-desktop
          gcr
          accountsservice
          geoclue2
          gnome-settings-daemon
          xdg-dbus-proxy
        ];

      in
      {
        devShells.default = pkgs.mkShell {
          name = "sugarlabs-devshell";

          buildInputs = [
            sugar-artwork
            pythonEnv
          ] ++ gtkDeps ++ waylandDeps ++ mutterDeps ++ (with pkgs; [
            git
            gnumake
            pkg-config
            meson
            ninja
            autoconf
            automake
            libtool
            intltool
            gettext
            gnome.gnome-common
            cairo
            pango
            atk
            wrapGAppsHook4
            gobject-introspection
            jq
            ripgrep
            fd
            gdb
            valgrind
          ]);

          nativeBuildInputs = with pkgs; [
            wrapGAppsHook4
            gobject-introspection
            pkg-config
            dbus
            dbus-glib
          ];

          GI_TYPELIB_PATH = pkgs.lib.makeSearchPath "lib/girepository-1.0" ([
            "${pkgs.gtk4.dev}/lib/girepository-1.0"
            "${pkgs.glib.dev}/lib/girepository-1.0"
            "${pkgs.glib.out}/lib/girepository-1.0"
            "${pkgs.gdk-pixbuf.dev}/lib/girepository-1.0"
            "${pkgs.librsvg.dev}/lib/girepository-1.0"
            "${pkgs.dbus-glib.out}/lib/girepository-1.0"
            "${pkgs.pango.dev}/lib/girepository-1.0"
            "${pkgs.atk.dev}/lib/girepository-1.0"
            "${pkgs.cairo.dev}/lib/girepository-1.0"
            "${pkgs.mutter.dev}/lib/girepository-1.0"
          ]);

          XDG_DATA_DIRS = pkgs.lib.makeSearchPath "share" ([
            "${pkgs.gtk4.dev}"
            "${pkgs.gsettings-desktop-schemas}"
            "${pkgs.hicolor-icon-theme}"
            "${pkgs.adwaita-icon-theme}"
            "${sugar-artwork}"
          ] ++ (with pkgs; [
            "${mutter}"
            "${gnome-desktop}"
          ]));

          GIO_EXTRA_MODULES = "${pkgs.dconf.lib}/lib/gio/modules";
          PYTHONPATH = "${toString ./.}/repos/sugar-toolkit-gtk4/src:${toString ./.}/repos/sugar/src";
          DBUS_SESSION_BUS_ADDRESS = "unix:path=/run/user/$UID/bus";

          WLR_RENDERER = "gles2";
          WLR_BACKENDS = "wayland,libinput";
          XDG_RUNTIME_DIR = "/run/user/$UID";

          CFLAGS = "-I${pkgs.gtk4.dev}/include/gtk-4.0 -I${pkgs.glib.dev}/include -I${pkgs.mutter.dev}/include/mutter-14";
          LDFLAGS = "-L${pkgs.gtk4.out}/lib -L${pkgs.glib.out}/lib -L${pkgs.mutter}/lib";

          shellHook = ''
            echo "Sugar Labs GTK4 modernization devShell"
            echo "  Python:  $(python --version)"
            echo "  GTK4:    $(pkg-config --modversion gtk4 2>/dev/null || echo 'not found')"
            echo "  Meson:   $(meson --version 2>/dev/null || echo 'not found')"
            echo ""
            echo "Repos:"
            echo "  sugar (shell):           repos/sugar/"
            echo "  sugar-toolkit-gtk4:      repos/sugar-toolkit-gtk4/"
            echo "  sugar-toolkit-gtk3 (ref):repos/sugar-toolkit-gtk3/"
            echo "  casilda (compositor):    repos/casilda/"
            echo ""
            echo "Quick start:"
            echo "  make run        # windowed shell"
            echo "  make debug      # shell with debugpy on :5678"
            echo "  make test       # run test suite"
            echo "  make lint       # ruff + mypy"
            echo "  make format     # auto-format"
          '';
        };

        packages.default = self.packages.${system}.sugarlabs-workspace;

        packages.sugarlabs-workspace = pkgs.sugarlabs-monorepo;
      });
}
