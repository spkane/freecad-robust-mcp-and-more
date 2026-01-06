"""Tests for object tools module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from freecad_mcp.bridge.base import ExecutionResult, ObjectInfo


class TestObjectTools:
    """Tests for object management tools."""

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
        """Register object tools and return the registered functions."""
        from freecad_mcp.tools.objects import register_object_tools

        async def get_bridge():
            return mock_bridge

        register_object_tools(mock_mcp, get_bridge)
        return mock_mcp._registered_tools

    @pytest.mark.asyncio
    async def test_list_objects_empty(self, register_tools, mock_bridge):
        """list_objects should return empty list when no objects."""
        mock_bridge.get_objects = AsyncMock(return_value=[])

        list_objects = register_tools["list_objects"]
        result = await list_objects()

        assert result == []
        mock_bridge.get_objects.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_list_objects_with_objects(self, register_tools, mock_bridge):
        """list_objects should return object info."""
        mock_objects = [
            ObjectInfo(
                name="Box",
                label="My Box",
                type_id="Part::Box",
                visibility=True,
                children=[],
                parents=[],
            ),
            ObjectInfo(
                name="Cylinder",
                label="My Cylinder",
                type_id="Part::Cylinder",
                visibility=False,
                children=[],
                parents=[],
            ),
        ]
        mock_bridge.get_objects = AsyncMock(return_value=mock_objects)

        list_objects = register_tools["list_objects"]
        result = await list_objects(doc_name="TestDoc")

        assert len(result) == 2
        assert result[0]["name"] == "Box"
        assert result[0]["type_id"] == "Part::Box"
        assert result[0]["visibility"] is True
        assert result[1]["name"] == "Cylinder"
        assert result[1]["visibility"] is False
        mock_bridge.get_objects.assert_called_once_with("TestDoc")

    @pytest.mark.asyncio
    async def test_inspect_object(self, register_tools, mock_bridge):
        """inspect_object should return detailed object info."""
        mock_object = ObjectInfo(
            name="Box",
            label="My Box",
            type_id="Part::Box",
            properties={"Length": 10.0, "Width": 20.0, "Height": 30.0},
            shape_info={
                "shape_type": "Solid",
                "volume": 6000.0,
                "area": 2200.0,
                "is_valid": True,
            },
            visibility=True,
            children=["Fillet001"],
            parents=[],
        )
        mock_bridge.get_object = AsyncMock(return_value=mock_object)

        inspect_object = register_tools["inspect_object"]
        result = await inspect_object(object_name="Box")

        assert result["name"] == "Box"
        assert result["type_id"] == "Part::Box"
        assert result["properties"]["Length"] == 10.0
        assert result["shape_info"]["volume"] == 6000.0
        assert result["children"] == ["Fillet001"]
        mock_bridge.get_object.assert_called_once_with("Box", None)

    @pytest.mark.asyncio
    async def test_inspect_object_without_properties(self, register_tools, mock_bridge):
        """inspect_object should exclude properties when not requested."""
        mock_object = ObjectInfo(
            name="Box",
            label="My Box",
            type_id="Part::Box",
            properties={"Length": 10.0},
            shape_info=None,
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.get_object = AsyncMock(return_value=mock_object)

        inspect_object = register_tools["inspect_object"]
        result = await inspect_object(
            object_name="Box", include_properties=False, include_shape=False
        )

        assert result["name"] == "Box"
        assert "properties" not in result
        assert "shape_info" not in result

    @pytest.mark.asyncio
    async def test_create_object(self, register_tools, mock_bridge):
        """create_object should create and return object info."""
        mock_object = ObjectInfo(
            name="Box",
            label="Box",
            type_id="Part::Box",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_object = register_tools["create_object"]
        result = await create_object(type_id="Part::Box", name="Box")

        assert result["name"] == "Box"
        assert result["type_id"] == "Part::Box"
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_object(self, register_tools, mock_bridge):
        """edit_object should update object properties."""
        mock_object = ObjectInfo(
            name="Box",
            label="Box",
            type_id="Part::Box",
            properties={"Length": 20.0, "Width": 10.0},
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.edit_object = AsyncMock(return_value=mock_object)

        edit_object = register_tools["edit_object"]
        result = await edit_object(object_name="Box", properties={"Length": 20.0})

        assert result["name"] == "Box"
        mock_bridge.edit_object.assert_called_once_with("Box", {"Length": 20.0}, None)

    @pytest.mark.asyncio
    async def test_delete_object(self, register_tools, mock_bridge):
        """delete_object should delete and return success."""
        mock_bridge.delete_object = AsyncMock(return_value=True)

        delete_object = register_tools["delete_object"]
        result = await delete_object(object_name="Box")

        assert result["success"] is True
        mock_bridge.delete_object.assert_called_once_with("Box", None)

    @pytest.mark.asyncio
    async def test_create_box(self, register_tools, mock_bridge):
        """create_box should create a box primitive via create_object."""
        mock_object = ObjectInfo(
            name="Box",
            label="Box",
            type_id="Part::Box",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_box = register_tools["create_box"]
        result = await create_box(length=20.0, width=10.0, height=5.0)

        assert result["name"] == "Box"
        assert result["volume"] == 20.0 * 10.0 * 5.0
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_cylinder(self, register_tools, mock_bridge):
        """create_cylinder should create a cylinder primitive via create_object."""
        mock_object = ObjectInfo(
            name="Cylinder",
            label="Cylinder",
            type_id="Part::Cylinder",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_cylinder = register_tools["create_cylinder"]
        result = await create_cylinder(radius=5.0, height=20.0)

        assert result["name"] == "Cylinder"
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sphere(self, register_tools, mock_bridge):
        """create_sphere should create a sphere primitive via create_object."""
        mock_object = ObjectInfo(
            name="Sphere",
            label="Sphere",
            type_id="Part::Sphere",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_sphere = register_tools["create_sphere"]
        result = await create_sphere(radius=10.0)

        assert result["name"] == "Sphere"
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_cone(self, register_tools, mock_bridge):
        """create_cone should create a cone primitive via create_object."""
        mock_object = ObjectInfo(
            name="Cone",
            label="Cone",
            type_id="Part::Cone",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_cone = register_tools["create_cone"]
        result = await create_cone(radius1=10.0, radius2=0.0, height=20.0)

        assert result["name"] == "Cone"
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_torus(self, register_tools, mock_bridge):
        """create_torus should create a torus primitive via create_object."""
        mock_object = ObjectInfo(
            name="Torus",
            label="Torus",
            type_id="Part::Torus",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_torus = register_tools["create_torus"]
        result = await create_torus(radius1=20.0, radius2=5.0)

        assert result["name"] == "Torus"
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wedge(self, register_tools, mock_bridge):
        """create_wedge should create a wedge primitive via create_object."""
        mock_object = ObjectInfo(
            name="Wedge",
            label="Wedge",
            type_id="Part::Wedge",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_wedge = register_tools["create_wedge"]
        result = await create_wedge()

        assert result["name"] == "Wedge"
        mock_bridge.create_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_helix(self, register_tools, mock_bridge):
        """create_helix should create a helix primitive via create_object."""
        mock_object = ObjectInfo(
            name="Helix",
            label="Helix",
            type_id="Part::Helix",
            visibility=True,
            children=[],
            parents=[],
        )
        mock_bridge.create_object = AsyncMock(return_value=mock_object)

        create_helix = register_tools["create_helix"]
        result = await create_helix(pitch=5.0, height=20.0)

        assert result["name"] == "Helix"
        mock_bridge.create_object.assert_called_once()

    # Tests for execute_python based tools

    @pytest.mark.asyncio
    async def test_boolean_operation_fuse(self, register_tools, mock_bridge):
        """boolean_operation should perform union operation via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "Fusion",
                    "label": "Fusion",
                    "type_id": "Part::MultiFuse",
                },
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        boolean_operation = register_tools["boolean_operation"]
        result = await boolean_operation(
            operation="fuse", object1_name="Box", object2_name="Cylinder"
        )

        assert result["name"] == "Fusion"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_placement(self, register_tools, mock_bridge):
        """set_placement should set position and rotation via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"position": [10.0, 20.0, 30.0], "rotation": [0.0, 0.0, 45.0]},
                stdout="",
                stderr="",
                execution_time_ms=5.0,
            )
        )

        set_placement = register_tools["set_placement"]
        result = await set_placement(object_name="Box", position=[10.0, 20.0, 30.0])

        assert result["position"] == [10.0, 20.0, 30.0]
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_scale_object(self, register_tools, mock_bridge):
        """scale_object should scale an object via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "ScaledBox",
                    "label": "ScaledBox",
                    "type_id": "Part::Feature",
                },
                stdout="",
                stderr="",
                execution_time_ms=15.0,
            )
        )

        scale_object = register_tools["scale_object"]
        result = await scale_object(object_name="Box", scale=2.0)

        assert result["name"] == "ScaledBox"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_rotate_object(self, register_tools, mock_bridge):
        """rotate_object should rotate an object via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 45.0]},
                stdout="",
                stderr="",
                execution_time_ms=5.0,
            )
        )

        rotate_object = register_tools["rotate_object"]
        result = await rotate_object(
            object_name="Box", axis=[0.0, 0.0, 1.0], angle=45.0
        )

        assert result["rotation"] == [0.0, 0.0, 45.0]
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_copy_object(self, register_tools, mock_bridge):
        """copy_object should create a copy via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"name": "Box001", "label": "Box001", "type_id": "Part::Box"},
                stdout="",
                stderr="",
                execution_time_ms=10.0,
            )
        )

        copy_object = register_tools["copy_object"]
        result = await copy_object(object_name="Box")

        assert result["name"] == "Box001"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_mirror_object(self, register_tools, mock_bridge):
        """mirror_object should mirror across a plane via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={
                    "name": "MirroredBox",
                    "label": "MirroredBox",
                    "type_id": "Part::Feature",
                },
                stdout="",
                stderr="",
                execution_time_ms=15.0,
            )
        )

        mirror_object = register_tools["mirror_object"]
        result = await mirror_object(object_name="Box", plane="XY")

        assert result["name"] == "MirroredBox"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_selection(self, register_tools, mock_bridge):
        """get_selection should return selected objects via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result=[
                    {
                        "name": "Box",
                        "label": "Box",
                        "type_id": "Part::Box",
                        "sub_elements": ["Face1"],
                    }
                ],
                stdout="",
                stderr="",
                execution_time_ms=5.0,
            )
        )

        get_selection = register_tools["get_selection"]
        result = await get_selection()

        assert len(result) == 1
        assert result[0]["name"] == "Box"
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_selection(self, register_tools, mock_bridge):
        """set_selection should select objects via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"success": True, "selected_count": 2},
                stdout="",
                stderr="",
                execution_time_ms=5.0,
            )
        )

        set_selection = register_tools["set_selection"]
        result = await set_selection(object_names=["Box", "Cylinder"])

        assert result["success"] is True
        assert result["selected_count"] == 2
        mock_bridge.execute_python.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_selection(self, register_tools, mock_bridge):
        """clear_selection should clear selections via execute_python."""
        mock_bridge.execute_python = AsyncMock(
            return_value=ExecutionResult(
                success=True,
                result={"success": True},
                stdout="",
                stderr="",
                execution_time_ms=5.0,
            )
        )

        clear_selection = register_tools["clear_selection"]
        result = await clear_selection()

        assert result["success"] is True
        mock_bridge.execute_python.assert_called_once()
