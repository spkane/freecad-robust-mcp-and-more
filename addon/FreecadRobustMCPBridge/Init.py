"""Robust MCP Bridge Workbench - Initialization.

SPDX-License-Identifier: MIT
Copyright (c) 2025 Sean P. Kane (GitHub: spkane)

This module is executed when FreeCAD starts up. It handles initialization
tasks for the Robust MCP Bridge workbench, including auto-start of the
MCP bridge if configured. Works in both GUI and headless modes.

Note: Status bar updates are handled by InitGui.py since Qt operations
must run on the main thread.
"""

import FreeCAD

FreeCAD.Console.PrintMessage("Robust MCP Bridge: Init loaded\n")

# Global reference to timers to prevent garbage collection
_auto_start_timer = None
_deferred_start_timer = None

# Counter for GUI wait retries
_gui_wait_retries = 0
# Increase timeout to 60 seconds (600 retries * 100ms) - FreeCAD GUI can take
# 10-30 seconds to fully initialize on macOS, especially on first launch
_GUI_WAIT_MAX_RETRIES = 600


def _auto_start_bridge() -> None:
    """Auto-start the MCP bridge if configured in preferences.

    This function is called via a deferred timer (GUI mode) or directly
    (headless mode) after FreeCAD finishes loading. It starts the bridge
    without requiring the workbench to be selected.
    """
    try:
        from preferences import get_auto_start

        if not get_auto_start():
            return

        # Check if bridge is already running
        from commands import _mcp_plugin

        if _mcp_plugin is not None and _mcp_plugin.is_running:
            return

        FreeCAD.Console.PrintMessage(
            "Auto-starting MCP Bridge (configured in preferences)...\n"
        )

        # Import and start the bridge directly
        import commands
        from freecad_mcp_bridge.server import FreecadMCPPlugin
        from preferences import get_socket_port, get_xmlrpc_port

        xmlrpc_port = get_xmlrpc_port()
        socket_port = get_socket_port()

        commands._mcp_plugin = FreecadMCPPlugin(
            host="localhost",
            port=socket_port,
            xmlrpc_port=xmlrpc_port,
            enable_xmlrpc=True,
        )
        commands._mcp_plugin.start()

        # Track running configuration for restart detection
        commands._running_config = {
            "xmlrpc_port": xmlrpc_port,
            "socket_port": socket_port,
        }

        FreeCAD.Console.PrintMessage("\n")
        FreeCAD.Console.PrintMessage("=" * 50 + "\n")
        FreeCAD.Console.PrintMessage("MCP Bridge started!\n")
        FreeCAD.Console.PrintMessage(f"  - XML-RPC: localhost:{xmlrpc_port}\n")
        FreeCAD.Console.PrintMessage(f"  - Socket:  localhost:{socket_port}\n")
        FreeCAD.Console.PrintMessage("=" * 50 + "\n")
        FreeCAD.Console.PrintMessage(
            "\nYou can now connect your MCP client (Claude Code, etc.) to FreeCAD.\n"
        )

    except Exception as e:
        FreeCAD.Console.PrintError(f"Failed to auto-start MCP Bridge: {e}\n")


def _wait_for_gui_and_start() -> None:
    """Wait for FreeCAD GUI to be ready, then start the bridge.

    This function is called repeatedly by a timer when Qt is available but
    FreeCAD.GuiUp is not yet True. It waits for the GUI to initialize before
    starting the bridge, ensuring the bridge uses Qt timer for queue processing
    instead of a background thread.

    This prevents crashes caused by executing Qt operations from background threads.
    """
    global _auto_start_timer, _deferred_start_timer, _gui_wait_retries

    _gui_wait_retries += 1

    # Log progress every 50 checks (5 seconds)
    if _gui_wait_retries % 50 == 0:
        elapsed = _gui_wait_retries * 0.1
        FreeCAD.Console.PrintMessage(
            f"Robust MCP Bridge: Still waiting for GUI... ({elapsed:.1f}s elapsed)\n"
        )

    if FreeCAD.GuiUp:
        # GUI is ready! Stop the repeating timer
        if _auto_start_timer is not None:
            _auto_start_timer.stop()
            _auto_start_timer = None
        elapsed = _gui_wait_retries * 0.1
        FreeCAD.Console.PrintMessage(
            f"Robust MCP Bridge: GUI ready after {elapsed:.1f}s, "
            "deferring bridge start...\n"
        )
        # IMPORTANT: Don't start the bridge immediately from this timer callback!
        # Even though GuiUp is True, FreeCAD may still be initializing internally.
        # Use a single-shot timer to defer the actual start to a later, more stable
        # point in the event loop. This mimics the behavior of manual start via
        # toolbar buttons, which works reliably.
        try:
            from PySide2 import QtCore as DeferQtCore  # type: ignore[import]
        except ImportError:
            from PySide6 import QtCore as DeferQtCore  # type: ignore[import]
        _deferred_start_timer = DeferQtCore.QTimer()
        _deferred_start_timer.setSingleShot(True)
        _deferred_start_timer.timeout.connect(_auto_start_bridge)
        _deferred_start_timer.start(2000)  # 2 second delay for FreeCAD to stabilize
    elif _gui_wait_retries >= _GUI_WAIT_MAX_RETRIES:
        # Timeout - DO NOT start with background thread, it will crash!
        if _auto_start_timer is not None:
            _auto_start_timer.stop()
            _auto_start_timer = None
        FreeCAD.Console.PrintError(
            "\n" + "=" * 60 + "\n"
            "ROBUST MCP BRIDGE ERROR: GUI did not become ready within 60s!\n"
            "=" * 60 + "\n\n"
            "Auto-start was NOT performed because starting with a background\n"
            "thread would cause FreeCAD to crash when executing Qt operations.\n\n"
            "Possible causes:\n"
            "  - FreeCAD is running in headless mode (auto-start disabled)\n"
            "  - FreeCAD GUI initialization is extremely slow\n"
            "  - There's an issue with the FreeCAD installation\n\n"
            "To start the bridge manually, select the Robust MCP Bridge workbench\n"
            "and click 'Start MCP Bridge'.\n"
            "=" * 60 + "\n"
        )
        # Do NOT call _auto_start_bridge() here - it would use background thread and crash
    # Otherwise, timer will fire again and we'll check again


# Schedule auto-start after FreeCAD finishes loading
# Strategy:
# - If FreeCAD.GuiUp is True: Qt event loop is running, use timer for deferred start
# - If FreeCAD.GuiUp is False but Qt is available: FreeCAD GUI is initializing.
#   Use a repeating timer to wait for GuiUp to become True before starting.
#   This ensures the bridge uses Qt timer (not background thread) for queue processing.
# - If Qt is not available: Pure headless mode, start bridge directly
#
# CRITICAL: We must wait for FreeCAD.GuiUp to be True before starting the bridge
# in GUI mode. If we start when GuiUp is False, the bridge's _start_queue_processor()
# will see GuiUp=False and use a background thread. Later, code executed on that
# thread will try to do Qt operations, causing crashes (SIGABRT in QCocoaWindow).
try:
    from preferences import get_auto_start

    if get_auto_start():
        # Try to import Qt
        import contextlib

        QtCore = None
        try:
            from PySide2 import QtCore  # type: ignore[assignment, no-redef]
        except ImportError:
            with contextlib.suppress(ImportError):
                from PySide6 import QtCore  # type: ignore[assignment, no-redef]

        if FreeCAD.GuiUp:
            # GUI is already up - use timer for deferred start
            if QtCore is not None:
                _auto_start_timer = QtCore.QTimer()
                _auto_start_timer.setSingleShot(True)
                _auto_start_timer.timeout.connect(_auto_start_bridge)
                _auto_start_timer.start(1000)
            else:
                # GUI is up but Qt import failed - start directly
                _auto_start_bridge()
        elif QtCore is not None:
            # GUI not ready yet, but Qt is available (FreeCAD starting in GUI mode)
            # Use a repeating timer to wait for GuiUp to become True
            # This prevents starting the bridge with a background thread that will
            # later crash when executing Qt operations
            _auto_start_timer = QtCore.QTimer()
            _auto_start_timer.setSingleShot(False)  # Repeating timer
            _auto_start_timer.timeout.connect(_wait_for_gui_and_start)
            _auto_start_timer.start(100)  # Check every 100ms
            FreeCAD.Console.PrintMessage(
                "Robust MCP Bridge: Waiting for GUI to be ready...\n"
            )
        else:
            # True headless mode - no Qt, no GUI
            _auto_start_bridge()
except Exception as e:
    FreeCAD.Console.PrintWarning(f"Could not set up auto-start: {e}\n")
