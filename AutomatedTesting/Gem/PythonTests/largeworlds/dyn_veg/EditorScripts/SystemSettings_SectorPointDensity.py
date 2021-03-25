"""
All or portions of this file Copyright (c) Amazon.com, Inc. or its affiliates or
its licensors.

For complete copyright and license terms please see the LICENSE at the root of this
distribution (the "License"). All use of this software is governed by the License,
or, if provided, by the license below or the license accompanying this file. Do not
remove or modify any license notices. This file is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

import os
import sys
import azlmbr.math as math
import azlmbr.paths
import azlmbr.editor as editor
import azlmbr.bus as bus

sys.path.append(os.path.join(azlmbr.paths.devroot, "AutomatedTesting", "Gem", "PythonTests"))
import automatedtesting_shared.hydra_editor_utils as hydra
from automatedtesting_shared.editor_test_helper import EditorTestHelper
from largeworlds.large_worlds_utils import editor_dynveg_test_helper as dynveg


class TestSystemSettingsSectorPointDensity(EditorTestHelper):
    def __init__(self):
        EditorTestHelper.__init__(self, log_prefix="SystemSettings_SectorPointDensity", args=["level"])

    def run_test(self):
        """
        Summary:
        Sector Point Density increases/reduces the number of vegetation points within a sector

        Expected Result:
        Default value for Sector Point Density is 20.
        20 vegetation meshes appear on each side of the established vegetation area with the default value.
        When altered, the specified number of vegetation meshes along a side of a vegetation area matches the value set
        in Sector Point Density.

        :return: None
        """

        INSTANCE_COUNT_BEFORE_DENSITY_CHANGE = 400
        INSTANCE_COUNT_AFTER_DENSITY_CHANGE = 100

        # Create empty level
        self.test_success = self.create_level(
            self.args["level"],
            heightmap_resolution=1024,
            heightmap_meters_per_pixel=1,
            terrain_texture_resolution=4096,
            use_terrain=False,
        )

        # Create basic vegetation entity
        position = math.Vector3(512.0, 512.0, 32.0)
        asset_path = os.path.join("Slices", "PinkFlower.dynamicslice")
        dynveg.create_vegetation_area("vegetation", position, 16.0, 16.0, 1.0, asset_path)
        dynveg.create_surface_entity("Surface_Entity", position, 16.0, 16.0, 1.0)

        # Count the number of vegetation meshes along one side of the new vegetation area.                                                                           #
        result = self.wait_for_condition(
            lambda: dynveg.validate_instance_count(position, 8.0, INSTANCE_COUNT_BEFORE_DENSITY_CHANGE), 2.0
        )
        self.log(f"Vegetation instances count equal to expected value before changing sector point density: {result}")

        # Add the Vegetation Debugger component to the Level Inspector
        veg_system_settings_component = hydra.add_level_component("Vegetation System Settings")

        # Change Sector Point Density to 10
        editor.EditorComponentAPIBus(
            bus.Broadcast,
            "SetComponentProperty",
            veg_system_settings_component,
            "Configuration|Area System Settings|Sector Point Snap Mode",
            1,
        )
        editor.EditorComponentAPIBus(
            bus.Broadcast,
            "SetComponentProperty",
            veg_system_settings_component,
            "Configuration|Area System Settings|Sector Point Density",
            10,
        )

        # Count the number of vegetation meshes along one side of the new vegetation area.
        result = self.wait_for_condition(
            lambda: dynveg.validate_instance_count(position, 8.0, INSTANCE_COUNT_AFTER_DENSITY_CHANGE), 2.0
        )
        self.log(f"Vegetation instances count equal to expected value after changing sector point density: {result}")


test = TestSystemSettingsSectorPointDensity()
test.run()