# Installation

This guide covers installing the FreeCAD MCP Server and connecting it to your AI assistant.

---

## Requirements

- **FreeCAD** 0.21+ or 1.0+ (with Python 3.11)
- **Python 3.11** (must match FreeCAD's bundled Python version)
- An **MCP-compatible AI assistant** (Claude Code, Cursor, etc.)

---

## Installation Methods

### Method 1: pip (Recommended)

The simplest way to install the MCP server:

```bash
pip install freecad-robust-mcp
```

### Method 2: From Source (for Development)

```bash
git clone https://github.com/spkane/freecad-robust-mcp-and-more.git
cd freecad-robust-mcp-and-more

# Install mise (if not already installed)
curl https://mise.run | sh

mise trust
mise install
just setup
```

### Method 3: Docker

Run the MCP server in a container:

```bash
# Pull from Docker Hub
docker pull spkane/freecad-robust-mcp

# Or build locally
docker build -t freecad-robust-mcp .
```

**Note:** The containerized MCP server only supports `xmlrpc` and `socket` modes since FreeCAD runs on your host machine (not in the container).

---

## Installing the MCP Bridge Workbench

The MCP Bridge Workbench runs inside FreeCAD and provides the connection point for the MCP server.

### Via FreeCAD Addon Manager (Recommended)

1. Open FreeCAD
1. Go to **Tools > Addon Manager**
1. Search for "FreeCAD MCP and More" or "MCP Bridge"
1. Click **Install**
1. Restart FreeCAD

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/spkane/freecad-robust-mcp-and-more/releases)
1. Extract to your FreeCAD Mod directory:
   - **Linux:** `~/.local/share/FreeCAD/Mod/`
   - **macOS:** `~/Library/Application Support/FreeCAD/Mod/`
   - **Windows:** `%APPDATA%\FreeCAD\Mod\`
1. Restart FreeCAD

---

## Verifying Installation

After installation, verify everything is working:

1. **Start FreeCAD** and open the MCP Bridge workbench
1. **Click "Start Bridge"** in the toolbar
1. You should see a message confirming the bridge is running on ports 9875 (XML-RPC) and 9876 (Socket)

Then test from the command line:

```bash
# With pip installation
freecad-mcp --help

# With source installation
uv run freecad-mcp --help
```

---

## Next Steps

- [Configuration](configuration.md) - Set up environment variables and MCP client settings
- [Quick Start](quickstart.md) - Create your first model with AI assistance
