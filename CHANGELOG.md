# Changelog

## Version 1.1.6 - 18/08/2026

- Improved catalog version display for beta-only plugins.
- Added beta channel labels when no stable release is available.
- Fixed installation URLs for plugins without a stable version.
- Prevented updates to beta releases by default.

## Version 1.1.5 - 18/08/2026

- Fixed plugin uninstallation on Volumio 4.
- Uses the correct `unInstallPlugin` Socket.IO command.
- Automatically verifies that the plugin has been removed.
- Improved debug messages during plugin removal.

## Version 1.1.4 - 15/08/2026

### Added
- Added `--deactivate PLUGIN` command to disable installed plugins.
- Added dedicated timeout configuration constants:
  - `DEFAULT_TIMEOUT`
  - `INSTALL_TIMEOUT`
  - `REMOVE_TIMEOUT`
  - `RESTART_TIMEOUT`

### Changed
- Improved timeout handling with operation-specific values instead of fixed delays.
- Updated restart operation to use `RESTART_TIMEOUT`.
- Updated remove operation to use `REMOVE_TIMEOUT`.
- Updated activate and deactivate operations to use `DEFAULT_TIMEOUT`.
- Improved code organization with clearer section comments.
- Reduced unnecessary blank lines for better readability.

### Fixed
- Fixed command line handling for `--deactivate`.
- Fixed indentation issues introduced during deactivate command integration.
- Improved plugin enable/disable status verification after Socket.IO commands.

### Compatibility
- Maintained compatibility with:
  - Volumio 3.x
  - Volumio 4.x
  - MiniDSP SHD Volumio builds