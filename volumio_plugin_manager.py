#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Volumio Plugin Manager
Author: Stef
Date:   18/08/2026

Manage Volumio plugins through Socket.IO.

Compatible:
- Volumio 3.x and 4.x
- MiniDSP SHD Volumio 3.x

Commands:
    --list
    --info PLUGIN
    --install PLUGIN
    --install-url URL
    --install-variant PLUGIN --variant PLATFORM
    --activate PLUGIN
    --deactivate PLUGIN
    --remove PLUGIN
    --restart PLUGIN
    --update PLUGIN
    --version

Debug:
    --debug
    --debug-json
"""

import argparse
from pathlib import PurePosixPath
import sys
import time
import socketio
from urllib.parse import urlparse

# Plugin manager version
VERSION = "1.1.6"

# Operation timeouts
DEFAULT_TIMEOUT = 30
INSTALL_TIMEOUT = 300
REMOVE_TIMEOUT = 120
RESTART_TIMEOUT = 60


class VolumioPluginManager:
    def __init__(self, host, debug=False, debug_json=False):
        self.host = host.rstrip("/")
        self.debug = debug
        self.debug_json = debug_json
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=5
        )
        self.connected = False
        self.installed_plugins = []
        self.available_plugins = []
        self.installed_plugins_received = False
        self.available_plugins_received = False
        self.install_result = None
        self.operation_done = False
        self.install_status = None
        self.register_events()

    def log(self, msg):
        if self.debug:
            print("[DEBUG]", msg)

    def log_json(self, data):
        if self.debug_json:
            print(data)

    # Socket.IO event handlers
    def register_events(self):
        @self.sio.event
        def connect():
            self.connected = True
            self.log("Socket.IO connected")
            self.sio.emit("getInstalledPlugins")
            self.sio.emit("getAvailablePlugins")

        @self.sio.event
        def disconnect():
            self.connected = False
            self.log("Socket.IO disconnected")

        @self.sio.on("*")
        def socket_all(event, data):
            if self.debug_json:
                print("\n[SOCKET EVENT]", event)
                print(data)

        # Installed plugins list received
        @self.sio.on("pushInstalledPlugins")
        def push_installed(data):
            self.log_json(data)
            if isinstance(data, list):
                self.installed_plugins = data
            else:
                self.installed_plugins = []
            self.installed_plugins_received = True
            self.log(
                f"Installed plugins received: {len(self.installed_plugins)}"
            )

        # Available plugins catalog received
        @self.sio.on("pushAvailablePlugins")
        def push_available(data):
            self.log_json(data)
            try:
                plugins = []
                if isinstance(data, list):
                    plugins = data
                elif isinstance(data, dict):
                    plugins.extend(data.get("plugins", []))
                    for category in data.get("categories", []):
                        plugins.extend(category.get("plugins", []))
                self.available_plugins = plugins
                self.available_plugins_received = True
                self.log(
                    f"Available plugins received: {len(plugins)}"
                )
            except Exception as e:
                print("Catalog error:", e)

        # Installation result
        @self.sio.on("installPlugin")
        def install_event(data):
            self.log_json(data)
            if data is None:
                return
            self.install_result = data
            self.operation_done = True

        # Installation error
        @self.sio.on("pluginInstallError")
        def install_error(data):
            print()
            print("Plugin installation error:")
            print(data)
            self.install_result = False
            self.operation_done = True

        # Installation progress
        @self.sio.on("pushInstallStatus")
        def install_status(data):
            self.install_status = data
            print("[INSTALL]", data)
            if isinstance(data, dict) and data.get("progress", 0) >= 100:
                self.install_result = True
                self.operation_done = True

        @self.sio.on("installPluginStatus")
        def install_status2(data):
            self.install_status = data
            print("[INSTALL]", data)
            if isinstance(data, dict) and data.get("progress", 0) >= 100:
                self.install_result = True
                self.operation_done = True

    # Connect to Volumio Socket.IO server
    def connect(self):
        print("Connecting:", self.host)
        self.sio.connect(self.host, transports=["websocket"])
        timeout = time.time() + 15
        while time.time() < timeout:
            if (
                self.installed_plugins_received
                and self.available_plugins_received
            ):
                break
            time.sleep(0.2)
        self.log("Synchronization complete")

    def close(self):
        try:
            self.sio.disconnect()
        except Exception:
            pass

    # Find plugin in installed/catalog lists
    def find_plugin(self, name):
        installed = None
        available = None
        for plugin in self.installed_plugins:
            if plugin.get("name") == name:
                installed = plugin
        for plugin in self.available_plugins:
            if plugin.get("name") == name:
                available = plugin
        return installed, available

    # Return the available plugin version and its release channel
    def catalog_version(self, plugin):
        stable_version = plugin.get("stableVersion")
        if stable_version:
            return stable_version, "stable"
        beta_version = plugin.get("betaVersion") or plugin.get("version")
        if beta_version:
            return beta_version, "beta"
        return None, None

    # Select best compatible plugin variant
    def choose_variant(self, plugin):
        variants = plugin.get("stableVariants", [])
        preferred = [
            "minidspshd/buster/armhf",
            "volumio/buster/armhf",
            "minidspshd/bookworm/armhf",
            "volumio/bookworm/armhf"
        ]
        for variant in preferred:
            if variant in variants:
                return variant
        if variants:
            return variants[0]
        return None

    # Display installed and available plugins
    def list_plugins(self):
        print()
        print("Installed plugins:")
        if not self.installed_plugins:
            print("  No plugins installed")
        else:
            for plugin in self.installed_plugins:
                print(
                    " ",
                    plugin.get("name"),
                    plugin.get("version", "?")
                )
        print()
        print("Available plugins:")
        for plugin in self.available_plugins:
            version, channel = self.catalog_version(plugin)
            if version:
                label = version
                if channel == "beta":
                    label += " (beta)"
            else:
                label = "unknown"
            print(
                " ",
                plugin.get("name"), "-",
                plugin.get("prettyName", ""), "- v",
                label
            )

    # Display plugin information
    def show_info(self, name):
        installed, available = self.find_plugin(name)
        print()
        if available:
            print("Plugin:", available.get("prettyName", name))
            print("Internal name:", name)
            print("Category:", available.get("category", "?"))
            print("Available version:", available.get("stableVersion"))
            variant = self.choose_variant(available)
            print("Selected variant:", variant)
            url = (
                "https://plugins.volumio.workers.dev/"
                "pluginsv2/downloadLatestStable/"
                f"{name}/{variant}"
            )
            print("Download URL:", url)
        elif installed:
            print("Plugin:", installed.get("prettyName", name))
            print("Internal name:", name)
            print("Category:", installed.get("category", "?"))
            print("Catalog status: not available")
        else:
            print("Plugin not found:", name)
        print()
        if installed:
            print("Installed: yes")
            print("Installed version:", installed.get("version", "?"))
        else:
            print("Installed: no")

    # Install plugin from official catalog
    def install(self, name):
        installed, plugin = self.find_plugin(name)
        if installed:
            print("Plugin already installed")
            return False
        if not plugin:
            print("Plugin not found:", name)
            return False
        variant = self.choose_variant(plugin)
        url = (
            "https://plugins.volumio.workers.dev/"
            "pluginsv2/downloadLatestStable/"
            f"{name}/{variant}"
        )
        print()
        print("Installing:", plugin.get("prettyName", name))
        print("Version:", plugin.get("stableVersion"))
        print("Variant:", variant)
        print("URL:", url)
        payload = {
            "url": url,
            "name": name,
            "category": plugin.get("category", "music_service"),
            "confirm": True
        }
        self.operation_done = False
        self.install_result = None
        self.install_status = None
        self.sio.emit("installPlugin", payload)
        timeout = time.time() + INSTALL_TIMEOUT
        while not self.operation_done and time.time() < timeout:
            time.sleep(0.5)
        if not self.operation_done:
            print("Installation timeout")
            return False
        if self.install_result is False:
            print("Installation failed")
            return False
        print("Installation complete")
        self.sio.emit(
            "pluginManager",
            {
                "name": name,
                "category": plugin.get("category", "music_service"),
                "action": "enable"
            }
        )
        return True

    # Enable plugin
    def activate(self, name):
        installed, plugin = self.find_plugin(name)
        if not installed:
            print("Plugin not installed")
            return False
        if installed.get("enabled"):
            print("Plugin already enabled")
            return True
        print("Enabling:", name)
        self.sio.emit(
            "pluginManager",
            {
                "name": name,
                "category": installed.get("category", "music_service"),
                "action": "enable"
            }
        )
        timeout = time.time() + DEFAULT_TIMEOUT
        while time.time() < timeout:
            self.sio.emit("getInstalledPlugins")
            time.sleep(1)
            activated, plugin = self.find_plugin(name)
            if activated and activated.get("enabled"):
                print("Plugin enabled")
                return True
        print("Plugin enablement not confirmed")
        return False

    # Disable plugin
    def deactivate(self, name):
        installed, plugin = self.find_plugin(name)
        if not installed:
            print("Plugin not installed")
            return False
        print("Disabling:", name)
        self.sio.emit(
            "pluginManager",
            {
                "name": name,
                "category": installed.get("category", "music_service"),
                "action": "disable"
            }
        )
        timeout = time.time() + DEFAULT_TIMEOUT
        while time.time() < timeout:
            self.sio.emit("getInstalledPlugins")
            time.sleep(1)
            disabled, plugin = self.find_plugin(name)
            if disabled and disabled.get("enabled") is False:
                print("Plugin disabled")
                return True
        print("Plugin disablement not confirmed")
        return False

    # Install plugin from URL
    def install_url(self, url, name=None, category="music_service"):
        if name is None:
            filename = PurePosixPath(urlparse(url).path).name
            name = filename.rsplit(".", 1)[0]
        if not name:
            print("Invalid plugin URL")
            return False
        installed, plugin = self.find_plugin(name)
        if installed:
            print("Plugin already installed")
            return False
        print()
        print("Installing from:", url)
        print("Plugin:", name)
        payload = {
            "url": url,
            "name": name,
            "category": category,
            "confirm": True
        }
        self.operation_done = False
        self.install_result = None
        self.install_status = None
        self.sio.emit("installPlugin", payload)
        timeout = time.time() + INSTALL_TIMEOUT
        while not self.operation_done and time.time() < timeout:
            time.sleep(0.5)
        if not self.operation_done:
            print("Installation timeout")
            return False
        if self.install_result is False:
            print("Installation failed")
            return False
        print("Installation complete")
        return True

    # Install a specific platform variant
    def install_variant(self, name, variant):
        url = (
            "https://plugins.volumio.workers.dev/pluginsv2/downloadLatestStable/"
            + name + "/" + variant
        )
        return self.install_url(url, name)

    # Remove plugin
    def remove(self, name):
        installed, plugin = self.find_plugin(name)
        if not installed:
            print("Plugin not installed")
            return False

        print("Removing:", name)
        payload = {
            "category": installed.get("category", "music_service"),
            "name": name
        }
        print("[DEBUG] unInstallPlugin payload:", payload)
        self.sio.emit("unInstallPlugin", payload)
        print("[DEBUG] unInstallPlugin emitted")

        time.sleep(2)
        print("[DEBUG] Requesting installed plugins")
        self.sio.emit("getInstalledPlugins")
        time.sleep(2)

        installed, plugin = self.find_plugin(name)
        if installed:
            print("[DEBUG] Plugin still installed")
            return False

        print("[DEBUG] Plugin no longer installed")
        return True

    # Restart plugin
    def restart(self, name):
        print("Restarting:", name)
        self.operation_done = False
        self.sio.emit(
            "restartPlugin",
            {
                "plugin": name,
                "name": name
            }
        )
        timeout = time.time() + RESTART_TIMEOUT
        while not self.operation_done and time.time() < timeout:
            time.sleep(0.5)
        if not self.operation_done:
            print("Restart timeout")
            return False
        print("Restart complete")
        return True

    # Update plugin
    def update(self, name):
        installed, available = self.find_plugin(name)
        if not installed:
            print("Plugin not installed")
            return False
        if not available:
            print("Plugin not found in catalog")
            return False
        current = installed.get("version")
        latest = available.get("stableVersion")
        print("Current version:", current)
        print("Latest version:", latest)
        if current == latest:
            print("Plugin already up to date")
            return True
        print("Updating...")
        if not self.remove(name):
            return False
        time.sleep(3)
        return self.install(name)


# Command line interface
def main():
    parser = argparse.ArgumentParser(
        description=f"Volumio Plugin Manager v{VERSION}"
    )
    parser.add_argument(
        "--host",
        default="http://192.168.15.50:3000",
        help="Volumio address"
    )
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--info", metavar="PLUGIN")
    parser.add_argument("--install", metavar="PLUGIN")
    parser.add_argument("--install-url", metavar="URL")
    parser.add_argument("--install-variant", metavar="PLUGIN")
    parser.add_argument("--variant", metavar="PLATFORM")
    parser.add_argument("--activate", metavar="PLUGIN")
    parser.add_argument("--deactivate", metavar="PLUGIN")
    parser.add_argument("--remove", metavar="PLUGIN")
    parser.add_argument("--restart", metavar="PLUGIN")
    parser.add_argument("--update", metavar="PLUGIN")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--debug-json", action="store_true")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Volumio Plugin Manager v{VERSION}"
    )
    args = parser.parse_args()
    if not any([
        args.list,
        args.info,
        args.install,
        args.install_url,
        args.install_variant,
        args.activate,
        args.deactivate,
        args.remove,
        args.restart,
        args.update
    ]):
        parser.print_help()
        sys.exit(1)
    if args.install_variant and not args.variant:
        parser.error("--install-variant requires --variant")
    if args.variant and not args.install_variant:
        parser.error("--variant requires --install-variant")
    manager = VolumioPluginManager(
        args.host,
        debug=args.debug,
        debug_json=args.debug_json
    )
    try:
        manager.connect()
        if args.list:
            manager.list_plugins()
        elif args.info:
            manager.show_info(args.info)
        elif args.install:
            manager.install(args.install)
        elif args.install_url:
            manager.install_url(args.install_url)
        elif args.install_variant:
            manager.install_variant(
                args.install_variant,
                args.variant
            )
        elif args.activate:
            manager.activate(args.activate)
        elif args.deactivate:
            manager.deactivate(args.deactivate)
        elif args.remove:
            manager.remove(args.remove)
        elif args.restart:
            manager.restart(args.restart)
        elif args.update:
            manager.update(args.update)
    except KeyboardInterrupt:
        print()
        print("Interrupted by user")
    except Exception as e:
        print()
        print("Error:", e)
    finally:
        manager.close()


if __name__ == "__main__":
    main()
