# semantic-color-system

## ADDED Requirements

### Requirement: Light and dark token sets

The shell SHALL maintain two complete `--sn-*` token sets, one for light
theme and one for dark theme, derived from the same accent color via HSL
computation. Switching between them SHALL be instant and not require restart.

#### Scenario: Toggling dark mode
- **WHEN** the learner toggles dark mode
- **THEN** `--sn-bg`, `--sn-text`, `--sn-bg-alt`, `--sn-surface`,
  `--sn-text-secondary`, and all other `--sn-*` tokens switch to their
  dark-theme variants while keeping the same accent color

### Requirement: Per-token overrides survive theme switch

The shell SHALL preserve a learner's manual token override (e.g. `--sn-surface`)
when switching between light and dark themes.

#### Scenario: Override in dark mode
- **WHEN** the learner overrides `--sn-surface` in dark mode, then toggles
  to light mode and back to dark mode
- **THEN** the overridden `--sn-surface` value is still applied
