# MCP Resources

The FreeCAD MCP server exposes several resources that allow AI assistants to query FreeCAD's state without executing code.

---

## Overview

MCP Resources are read-only endpoints that provide context about FreeCAD's current state. They're useful for:

- Understanding what documents and objects exist
- Getting system information
- Discovering available capabilities

---

## Available Resources

### freecad://capabilities

Returns a comprehensive JSON catalog of all available tools, resources, and prompts.

**Use case:** Understanding what the MCP server can do.

**Example response:**

```json
{
  "tools": {
    "execution": ["execute_python", "get_freecad_version", ...],
    "documents": ["create_document", "open_document", ...],
    ...
  },
  "resources": ["freecad://capabilities", "freecad://documents", ...],
  "prompts": ["create-parametric-part", "debug-macro", ...]
}
```

### freecad://documents

Lists all open FreeCAD documents with basic information.

**Use case:** Seeing what documents are currently open.

**Example response:**

```json
[
  {
    "name": "MyPart",
    "label": "My Part Design",
    "path": "/home/user/projects/mypart.FCStd",
    "is_modified": true,
    "object_count": 15
  }
]
```

### freecad://documents/{doc_name}

Gets detailed information about a specific document.

**Use case:** Examining a document's contents.

**Example response:**

```json
{
  "name": "MyPart",
  "label": "My Part Design",
  "path": "/home/user/projects/mypart.FCStd",
  "objects": ["Body", "Sketch", "Pad", "Fillet"],
  "active_object": "Fillet"
}
```

### freecad://documents/{doc_name}/objects/{obj_name}

Gets detailed information about a specific object including properties and shape data.

**Use case:** Inspecting object properties and geometry.

### freecad://console

Gets recent FreeCAD console output.

**Use case:** Debugging and seeing FreeCAD messages.

### freecad://version

Gets FreeCAD version and build information.

**Example response:**

```json
{
  "version": "1.0.0",
  "build_date": "2024-01-15",
  "python_version": "3.11.6",
  "gui_available": true
}
```

---

## Using Resources in Prompts

When talking to an AI assistant connected via MCP, resources are automatically available. The AI can read them to understand context.

**Example conversation:**

```text
User: "What documents do I have open?"

AI: [Reads freecad://documents resource]
    "You have two documents open:
     1. 'Bracket' - modified, 12 objects
     2. 'Housing' - saved, 8 objects"
```

---

## Resources vs Tools

| Aspect       | Resources               | Tools                |
| ------------ | ----------------------- | -------------------- |
| Purpose      | Query state (read-only) | Perform actions      |
| Side effects | None                    | May modify documents |
| Response     | Data/text               | Operation result     |
| Example      | `freecad://documents`   | `create_document()`  |

---

## Implementing Custom Resources

If you're extending the MCP server, you can add custom resources:

```python
@mcp.resource("freecad://custom/{param}")
async def my_custom_resource(param: str) -> str:
    """Return custom data based on param."""
    # Query FreeCAD and return data
    result = await bridge.execute_python(f"...")
    return json.dumps(result)
```

---

## Next Steps

- [Tools Reference](tools.md) - Complete API for MCP tools
- [Connection Modes](connection-modes.md) - How to connect to FreeCAD
