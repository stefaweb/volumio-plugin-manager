# Volumio Plugin Manager

Manage Volumio plugins through Socket.IO from the command line.

Tested with:

- Volumio 3.x on Raspberry Pi
- MiniDSP SHD running Volumio 3.x

## Requirements

- Python 3.8 or later
- Network access to the Volumio device
- The `python-socketio` package

## Installation

Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required package:

```bash
pip install "python-socketio[client]"
```

Save `volumio_plugin_manager.py` in the current directory, then verify the available commands:

```bash
python volumio_plugin_manager.py --help
```

## Connecting to a Volumio device

The default device address is `http://192.168.1.1:3000`.

Use `--host` to connect to another device:

```bash
python volumio_plugin_manager.py --host http://192.168.1.2:3000 --list
```

## List plugins

List the plugins installed on the target device and the plugins offered by its catalog:

```bash
python volumio_plugin_manager.py --list
```

The available catalog is filtered by the target device. For example, a MiniDSP SHD only receives plugins that Volumio declares compatible with its `minidspshd/buster/armhf` variant.

To view the standard Raspberry Pi catalog, query a Raspberry Pi Volumio device:

```bash
python volumio_plugin_manager.py \
  --host http://192.168.1.2:3000 \
  --list
```

## Display plugin information

Show the installed version, available version, selected variant, and download URL:

```bash
python volumio_plugin_manager.py --info calmradio
```

## Install a catalog plugin

Install a plugin from the catalog of the target device:

```bash
python volumio_plugin_manager.py --install calmradio
```

The script automatically selects the best available variant. It prioritizes the MiniDSP SHD Buster variant, then the standard Volumio Buster variant.

## Enable a plugin

Enable an installed but disabled plugin:

```bash
python volumio_plugin_manager.py --activate calmradio
```

The command waits for Volumio to confirm that the plugin is enabled.

## Install a plugin from a ZIP URL

Install a Volumio plugin ZIP archive hosted outside the official catalog:

```bash
python volumio_plugin_manager.py --install-url "https://example.org/my_plugin.zip"
```

The ZIP file name is used as the plugin name. For example, `radio_paradise.zip` is installed as `radio_paradise`.

Only install archives from trusted sources. A Volumio plugin may execute its bundled installation script on the player.

### Radio Paradise historical archive

Install the historical Radio Paradise archive:

```bash
python volumio_plugin_manager.py --install-url \
  "https://raw.githubusercontent.com/volumio/volumio-plugins/ea1e832f049f10ed0903c06c654510dae787dc34/plugins/volumio/armhf/music_service/radio_paradise/radio_paradise.zip"
```

Then enable it:

```bash
python volumio_plugin_manager.py --activate radio_paradise
```

## Install a specific platform variant

Some plugins are available for the standard Raspberry Pi Volumio platform but are not listed in the MiniDSP SHD catalog. If a plugin is compatible with standard Buster ARMHF, install that explicit variant:

```bash
python volumio_plugin_manager.py \
  --install-variant radio_paradise \
  --variant volumio/buster/armhf
```

Then enable it:

```bash
python volumio_plugin_manager.py --activate radio_paradise
```

Use explicit variants carefully. A plugin can depend on hardware-specific drivers or system packages and may not work on every device.

## Remove a plugin

```bash
python volumio_plugin_manager.py --remove calmradio
```

## Restart a plugin

```bash
python volumio_plugin_manager.py --restart calmradio
```

## Update a plugin

Update a plugin when a newer version is available in the target device catalog:

```bash
python volumio_plugin_manager.py --update calmradio
```

## Debugging

Show diagnostic messages:

```bash
python volumio_plugin_manager.py --list --debug
```

Show the complete Socket.IO data received from Volumio:

```bash
python volumio_plugin_manager.py --list --debug-json
```

Use `--debug-json` when a command does not complete or a plugin does not appear in the catalog.
