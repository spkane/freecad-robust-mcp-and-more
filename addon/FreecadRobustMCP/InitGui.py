"""Robust MCP Bridge Workbench - GUI Initialization.

SPDX-License-Identifier: MIT
Copyright (c) 2025 Sean P. Kane (GitHub: spkane)

This module defines the workbench class for the Robust MCP Bridge.
It provides toolbar buttons and menu items to start and stop the
MCP bridge server. Commands are defined in the commands module.
"""

from __future__ import annotations

import FreeCAD
import FreeCADGui

# Register icons path for preferences page icon
# This must be done at module level, before the preferences page is registered
try:
    import os as _os  # noqa: PTH

    # Find the addon's icons directory
    _icons_dir = ""
    _base = FreeCAD.getUserAppDataDir()
    for _item in _os.listdir(_base):  # noqa: PTH208
        if _item.startswith("v1-"):
            _candidate = _os.path.join(  # noqa: PTH118
                _base, _item, "Mod", "FreecadRobustMCP", "icons"
            )
            if _os.path.isdir(_candidate):  # noqa: PTH112
                _icons_dir = _candidate
                break
    if not _icons_dir:
        _candidate = _os.path.join(  # noqa: PTH118
            _base, "Mod", "FreecadRobustMCP", "icons"
        )
        if _os.path.isdir(_candidate):  # noqa: PTH112
            _icons_dir = _candidate

    if _icons_dir:
        FreeCADGui.addIconPath(_icons_dir)
except Exception as e:
    FreeCAD.Console.PrintWarning(f"Could not register icon path: {e}\n")

# Register preferences page with FreeCAD's Preferences dialog
# This must be done at module level, before the workbench is registered
try:
    from preferences_page import MCPBridgePreferencesPage

    FreeCADGui.addPreferencePage(MCPBridgePreferencesPage, "Robust MCP Bridge")
except Exception as e:
    FreeCAD.Console.PrintWarning(
        f"Could not register MCP Bridge preferences page: {e}\n"
    )


class FreecadRobustMCPWorkbench(FreeCADGui.Workbench):
    """FreeCAD Robust MCP Workbench.

    Provides toolbar and menu commands to start, stop, and monitor
    the MCP bridge server for AI assistant integration.
    """

    MenuText = "Robust MCP Bridge"
    ToolTip = "Robust MCP Bridge for AI assistant integration with FreeCAD"

    def __init__(self) -> None:
        """Initialize workbench with icon path."""
        # NOTE: Using os.path instead of pathlib due to FreeCAD's module loading
        # behavior which can have issues with some Python features at load time
        import os as _os  # noqa: PTH

        icon_path = ""
        # Try versioned FreeCAD directory first (FreeCAD 1.x)
        try:
            base = FreeCAD.getUserAppDataDir()
            for item in _os.listdir(base):  # noqa: PTH208
                if item.startswith("v1-"):
                    candidate = _os.path.join(  # noqa: PTH118
                        base, item, "Mod", "FreecadRobustMCP", "FreecadRobustMCP.svg"
                    )
                    if _os.path.exists(candidate):  # noqa: PTH110
                        icon_path = candidate
                        break
        except Exception:
            pass

        # Fallback to non-versioned path
        if not icon_path:
            try:
                candidate = _os.path.join(  # noqa: PTH118
                    FreeCAD.getUserAppDataDir(),
                    "Mod",
                    "FreecadRobustMCP",
                    "FreecadRobustMCP.svg",
                )
                if _os.path.exists(candidate):  # noqa: PTH110
                    icon_path = candidate
            except Exception:
                pass

        self.Icon = icon_path

    def Initialize(self) -> None:
        """Initialize the workbench - called once when first activated."""
        # Import commands module here (not at top level) to ensure
        # it's available during FreeCAD's module loading process
        from commands import (
            MCPBridgePreferencesCommand,
            MCPBridgeStatusCommand,
            StartMCPBridgeCommand,
            StopMCPBridgeCommand,
        )

        # Register commands
        FreeCADGui.addCommand("Start_MCP_Bridge", StartMCPBridgeCommand())
        FreeCADGui.addCommand("Stop_MCP_Bridge", StopMCPBridgeCommand())
        FreeCADGui.addCommand("MCP_Bridge_Status", MCPBridgeStatusCommand())
        FreeCADGui.addCommand("MCP_Bridge_Preferences", MCPBridgePreferencesCommand())

        # Create toolbar with main commands
        toolbar_commands = [
            "Start_MCP_Bridge",
            "Stop_MCP_Bridge",
            "MCP_Bridge_Status",
        ]
        self.appendToolbar("Robust MCP Bridge", toolbar_commands)

        # Create menu with all commands including preferences
        menu_commands = [
            "Start_MCP_Bridge",
            "Stop_MCP_Bridge",
            "MCP_Bridge_Status",
            "Separator",
            "MCP_Bridge_Preferences",
        ]
        self.appendMenu("Robust MCP Bridge", menu_commands)

        FreeCAD.Console.PrintMessage("Robust MCP Bridge workbench initialized\n")

        # Auto-start bridge if preference is enabled
        # This is a fallback if the module-level timer didn't fire
        # (which can happen if the module isn't loaded until workbench selection)
        try:
            from preferences import get_auto_start

            if get_auto_start():
                # Check if already running (timer might have started it)
                from commands import _mcp_plugin

                if _mcp_plugin is None or not _mcp_plugin.is_running:
                    FreeCAD.Console.PrintMessage(
                        "Auto-starting MCP Bridge (configured in preferences)...\n"
                    )
                    FreeCADGui.runCommand("Start_MCP_Bridge")
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Could not auto-start MCP Bridge: {e}\n")

        # Sync status bar widget with current bridge state
        # (bridge may have been started by Init.py before workbench was selected)
        self._sync_status_bar()

    def Activated(self) -> None:
        """Called when the workbench is activated."""
        # Sync status bar widget with current bridge state
        self._sync_status_bar()

    def _sync_status_bar(self) -> None:
        """Sync status bar widget with current bridge state."""
        try:
            from commands import _mcp_plugin
            from preferences import get_status_bar_enabled

            if not get_status_bar_enabled():
                return

            from status_widget import (
                update_status_running,
                update_status_stopped,
            )

            if _mcp_plugin is not None and _mcp_plugin.is_running:
                update_status_running(
                    _mcp_plugin.xmlrpc_port,
                    _mcp_plugin.socket_port,
                    _mcp_plugin.request_count,
                )
            else:
                update_status_stopped()
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Could not sync status bar: {e}\n")

    def Deactivated(self) -> None:
        """Called when the workbench is deactivated."""
        pass

    def GetClassName(self) -> str:
        """Return the C++ class name for this workbench."""
        return "Gui::PythonWorkbench"


# Register the workbench
FreeCADGui.addWorkbench(FreecadRobustMCPWorkbench())

# Schedule status bar sync after a short delay to allow GUI to finish initializing
# This runs on the main thread (InitGui.py is executed on main thread)
try:
    try:
        from PySide2 import QtCore
    except ImportError:
        from PySide6 import QtCore

    def _deferred_status_bar_sync() -> None:
        """Sync status bar with bridge state after GUI is ready."""
        try:
            from commands import _mcp_plugin
            from preferences import get_status_bar_enabled
            from status_widget import sync_status_with_bridge

            if (
                get_status_bar_enabled()
                and _mcp_plugin is not None
                and _mcp_plugin.is_running
            ):
                FreeCAD.Console.PrintMessage(
                    "Robust MCP Bridge: Syncing status bar from InitGui...\n"
                )
                sync_status_with_bridge()
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"Robust MCP Bridge: Deferred status bar sync failed: {e}\n"
            )

    # Use QTimer.singleShot on the main thread - this should work
    QtCore.QTimer.singleShot(2000, _deferred_status_bar_sync)
    FreeCAD.Console.PrintMessage(
        "Robust MCP Bridge: Status bar sync scheduled from InitGui (2s)\n"
    )
except Exception as e:
    FreeCAD.Console.PrintWarning(
        f"Robust MCP Bridge: Could not schedule status bar sync: {e}\n"
    )
