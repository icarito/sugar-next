# Sugar Next Next — Tasks

## 1. Home View layout interface

- [ ] 1.1 Design `HomeViewLayout` interface (activate/deactivate/root widget)
- [ ] 1.2 Adapt `shell/app-grid.py` to implement the layout interface
- [ ] 1.3 Implement `shell/desktop-grid.py` (background image, floating
      icons, container folders that expand into sub-grids)
- [ ] 1.4 Implement `shell/search-first.py` (blank canvas + search bar)
- [ ] 1.5 Wire layout switching at runtime (no restart required)
- [ ] 1.6 Smoke test: switch between all three layouts, confirm state
      (search text, scroll position) resets cleanly on switch

## 2. Settings panel

- [ ] 2.1 Write `shell/settings.py` — panel shell, accessible from Frame
      or keybinding
- [ ] 2.2 Add background image picker (file chooser, stretch/tile option)
- [ ] 2.3 Add accent color picker (presets + custom hex)
- [ ] 2.4 Add contrast slider (normal → high)
- [ ] 2.5 Add icon size control (affects active Home View layout)
- [ ] 2.6 Add Home View layout selector
- [ ] 2.7 Add extension manager (list installed, enable/disable)
- [ ] 2.8 Add keybinding viewer and About section

## 3. Color tokens and theming

- [ ] 3.1 Define `--sn-bg`, `--sn-bg-alt`, `--sn-accent`, `--sn-text`,
      `--sn-text-secondary`, `--sn-surface` as a base GTK4 CSS stylesheet
- [ ] 3.2 Compute tokens from `prefers-color-scheme` at startup
- [ ] 3.3 Load `~/.config/sugar-next/colors.css` as a user override
      (applied after the base sheet)
- [ ] 3.4 Implement active-app-palette extraction (dominant color from
      focused app's icon) with static-accent fallback
- [ ] 3.5 Wire palette tint into Frame and Home View background

## 4. XDG Base Directory and FreeDesktop compliance

- [ ] 4.1 Move config reads/writes to `~/.config/sugar-next/`
- [ ] 4.2 Confirm all data writes use `~/.local/share/sugar-next/`
- [ ] 4.3 Register `org.sugarlabs.SugarNext` D-Bus name
- [ ] 4.4 Add MIME type associations for Journal entries
- [ ] 4.5 Expose a StatusNotifierItem for background services (e.g.
      presence bus, when running)

## 5. School-locked layouts

- [ ] 5.1 Design policy config file format (e.g.
      `~/.config/sugar-next/policy.conf`) for locking `home_view.layout`
- [ ] 5.2 Read policy file at startup; hide layout selector in Settings
      when a lock is present
- [ ] 5.3 Document that the lock is a cooperative default, not a security
      boundary

## 6. Peer collaboration (exploratory)

- [ ] 6.1 Add `on_peer_join`/`on_peer_leave` hooks to `api/hooks.py`
- [ ] 6.2 Research link-local transport options: XMPP link-local vs.
      WebRTC vs. custom UDP — write up findings and a recommendation
- [ ] 6.3 Write demo P2P chat extension using the chosen research-stage
      transport (link-local discovery via Avahi/DNS-SD)
- [ ] 6.4 Document the collaboration design (presence bus + share
      substrate) for future phases in `specbook/docs/`
- [ ] 6.5 Smoke test: two instances on the same LAN discover each other
      and exchange chat messages

## 7. Journal: deeper integration

- [ ] 7.1 Add `on_app_close` hook to the extension API
- [ ] 7.2 Update the Journal extension to record `kind='close'` entries
- [ ] 7.3 Evaluate Zeitgeist as an event source for the Journal (write up
      feasibility, API surface, effort — adopt/defer/reject recommendation)
- [ ] 7.4 Research integration with Nautilus/file managers for
      Journal-aware file browsing (write-up only, no implementation)

## 8. Community outreach

- [ ] 8.1 Post to sugar-devel with a demo and this change's proposal
- [ ] 8.2 Post to IAEP with educational framing
- [ ] 8.3 Reach out to Walter Bender for feedback

## 9. Documentation

- [ ] 9.1 Document the "Groups" view (activities as temporal, sharable
      workspaces spanning multiple apps) as explicit future work in
      `sugar-next/HIG.md` or `specbook/docs/`, gated on the extension API
      proving itself first
