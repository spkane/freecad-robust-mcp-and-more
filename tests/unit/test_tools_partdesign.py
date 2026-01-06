"""Tests for PartDesign tools module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from freecad_mcp.bridge.base import ExecutionResult, ObjectInfo


class TestPartDesignTools:
    """Tests for PartDesign tools."""

    @pytest.fixture
    def mock_mcp(self):
        """Create a mock MCP server that captures tool registrations."""
        mcp = MagicMock()
        mcp._registered_tools = {}

        def tool_decorator():
            def wrapper(func):
                mcp._registered_tools[func.__name__] = func
                return func

            return wrapper

        mcp.tool = tool_decorator
        return mcp

    @pytest.fixture
    def mock_bridge(self):
        """Create a mock FreeCAD bridge."""
        return AsyncMock()

    @pytest.fixture
    def register_tools(self, mock_mcp, mock_bridge):
        """Register PartDesign tools and return the registered functions."""
        from freecad_mcp.tools.partdesign import register_partdesign_tools

        async def get_bridge():
            return mock_bridge

        register_partdesign_tools(mock_mcp, get_bridge)
        return mock_mcp._registered_tools

    @pytest.mark.asyncio
    async def test_create_partdesign_body(self, register_tools, mock_bridge):
        """create_partdesign_body should create a body container via create_object."""
        mock_object = ObjectInfo(
            name="Body",
            label="Body",
            type_id="PartDesign::Body",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_body = register_tools["create_partdesign_body"]
        result = await create_body(name="Body")

        assert result["name"] == "Body"
        assert result["type_id"] == "PartDesign::Body"
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sketch(self, register_tools, mock_bridge):
        """create_sketch should create a sketch via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Sketch",
                    "label": "Sketch",
                    "type_id": "Sketcher::SketchObject",
                    "support": "XY_Plane",
                },
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        create_sketch = register_tools["create_sketch"]
        result = await create_sketch(body_name="Body", plane="XY_Plane")

        assert result["name"] == "Sketch"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_sketch_rectangle(self, register_tools, mock_bridge):
        """add_sketch_rectangle should add a rectangle via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"constraint_count": 8, "geometry_count": 4},
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        add_rectangle = register_tools["add_sketch_rectangle"]
        result = await add_rectangle(
            sketch_name="Sketch", x=-10, y=-10, width=20, height=20
        )

        assert result["constraint_count"] == 8
        assert result["geometry_count"] == 4
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_sketch_circle(self, register_tools, mock_bridge):
        """add_sketch_circle should add a circle via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"geometry_index": 0, "geometry_count": 1},
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        add_circle = register_tools["add_sketch_circle"]
        result = await add_circle(
            sketch_name="Sketch", center_x=0, center_y=0, radius=10
        )

        assert result["geometry_index"] == 0
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_sketch_line(self, register_tools, mock_bridge):
        """add_sketch_line should add a line via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"geometry_index": 0, "geometry_count": 1},
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        add_line = register_tools["add_sketch_line"]
        result = await add_line(sketch_name="Sketch", x1=0, y1=0, x2=10, y2=10)

        assert result["geometry_index"] == 0
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_sketch_arc(self, register_tools, mock_bridge):
        """add_sketch_arc should add an arc via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"geometry_index": 0, "geometry_count": 1},
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        add_arc = register_tools["add_sketch_arc"]
        result = await add_arc(
            sketch_name="Sketch",
            center_x=0,
            center_y=0,
            radius=10,
            start_angle=0,
            end_angle=90,
        )

        assert result["geometry_index"] == 0
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_sketch_point(self, register_tools, mock_bridge):
        """add_sketch_point should add a point via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"geometry_index": 0, "geometry_count": 1},
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        add_point = register_tools["add_sketch_point"]
        result = await add_point(sketch_name="Sketch", x=5, y=5)

        assert result["geometry_index"] == 0
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_pad_sketch(self, register_tools, mock_bridge):
        """pad_sketch should extrude a sketch via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"name": "Pad", "label": "Pad", "type_id": "PartDesign::Pad"},
                stdout="",
                stderr="",
                execution_time_ms=15.0,
            )
        )

        pad_sketch = register_tools["pad_sketch"]
        result = await pad_sketch(sketch_name="Sketch", length=10)

        assert result["name"] == "Pad"
        assert result["type_id"] == "PartDesign::Pad"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_pocket_sketch(self, register_tools, mock_bridge):
        """pocket_sketch should cut into solid via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Pocket",
                    "label": "Pocket",
                    "type_id": "PartDesign::Pocket",
                },
                stdout="",
                stderr="",
                execution_time_ms=15.0,
            )
        )

        pocket_sketch = register_tools["pocket_sketch"]
        result = await pocket_sketch(sketch_name="Sketch", length=5)

        assert result["name"] == "Pocket"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_revolution_sketch(self, register_tools, mock_bridge):
        """revolution_sketch should revolve a sketch via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Revolution",
                    "label": "Revolution",
                    "type_id": "PartDesign::Revolution",
                },
                stdout="",
                stderr="",
                execution_time_ms=20.0,
            )
        )

        revolution = register_tools["revolution_sketch"]
        result = await revolution(sketch_name="Sketch", angle=360)

        assert result["name"] == "Revolution"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_groove_sketch(self, register_tools, mock_bridge):
        """groove_sketch should cut by revolving via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Groove",
                    "label": "Groove",
                    "type_id": "PartDesign::Groove",
                },
                stdout="",
                stderr="",
                execution_time_ms=20.0,
            )
        )

        groove = register_tools["groove_sketch"]
        result = await groove(sketch_name="Sketch", angle=180)

        assert result["name"] == "Groove"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_fillet_edges(self, register_tools, mock_bridge):
        """fillet_edges should add rounded edges via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Fillet",
                    "label": "Fillet",
                    "type_id": "PartDesign::Fillet",
                },
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        fillet = register_tools["fillet_edges"]
        result = await fillet(object_name="Pad", radius=2.0)

        assert result["name"] == "Fillet"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_chamfer_edges(self, register_tools, mock_bridge):
        """chamfer_edges should add beveled edges via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Chamfer",
                    "label": "Chamfer",
                    "type_id": "PartDesign::Chamfer",
                },
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        chamfer = register_tools["chamfer_edges"]
        result = await chamfer(object_name="Pad", size=1.0)

        assert result["name"] == "Chamfer"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_hole(self, register_tools, mock_bridge):
        """create_hole should create parametric holes via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"name": "Hole", "label": "Hole", "type_id": "PartDesign::Hole"},
                stdout="",
                stderr="",
                execution_time_ms=15.0,
            )
        )

        create_hole = register_tools["create_hole"]
        result = await create_hole(sketch_name="HoleSketch", diameter=6.0, depth=10.0)

        assert result["name"] == "Hole"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_linear_pattern(self, register_tools, mock_bridge):
        """linear_pattern should create linear pattern via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "LinearPattern",
                    "label": "LinearPattern",
                    "type_id": "PartDesign::LinearPattern",
                },
                stdout="",
                stderr="",
                execution_time_ms=20.0,
            )
        )

        pattern = register_tools["linear_pattern"]
        result = await pattern(
            feature_name="Pad", direction="X", length=50, occurrences=5
        )

        assert result["name"] == "LinearPattern"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_polar_pattern(self, register_tools, mock_bridge):
        """polar_pattern should create circular pattern via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "PolarPattern",
                    "label": "PolarPattern",
                    "type_id": "PartDesign::PolarPattern",
                },
                stdout="",
                stderr="",
                execution_time_ms=20.0,
            )
        )

        pattern = register_tools["polar_pattern"]
        result = await pattern(feature_name="Pad", axis="Z", angle=360, occurrences=6)

        assert result["name"] == "PolarPattern"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_mirrored_feature(self, register_tools, mock_bridge):
        """mirrored_feature should mirror a feature via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Mirrored",
                    "label": "Mirrored",
                    "type_id": "PartDesign::Mirrored",
                },
                stdout="",
                stderr="",
                execution_time_ms=15.0,
            )
        )

        mirrored = register_tools["mirrored_feature"]
        result = await mirrored(feature_name="Pad", plane="XY")

        assert result["name"] == "Mirrored"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_loft_sketches(self, register_tools, mock_bridge):
        """loft_sketches should create a loft via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Loft",
                    "label": "Loft",
                    "type_id": "PartDesign::AdditiveLoft",
                },
                stdout="",
                stderr="",
                execution_time_ms=25.0,
            )
        )

        loft = register_tools["loft_sketches"]
        result = await loft(sketch_names=["Sketch", "Sketch001"])

        assert result["name"] == "Loft"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_sweep_sketch(self, register_tools, mock_bridge):
        """sweep_sketch should sweep a profile via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Sweep",
                    "label": "Sweep",
                    "type_id": "PartDesign::AdditivePipe",
                },
                stdout="",
                stderr="",
                execution_time_ms=25.0,
            )
        )

        sweep = register_tools["sweep_sketch"]
        result = await sweep(profile_sketch="Profile", spine_sketch="Spine")

        assert result["name"] == "Sweep"
        mock_bridge.execute_python.assert_called_once()
