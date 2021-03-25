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
import azlmbr.bus as bus
import azlmbr.asset as asset
import azlmbr.slice as slice

sys.path.append(os.path.join(azlmbr.paths.devroot, "AutomatedTesting", "Gem", "PythonTests"))
import automatedtesting_shared.hydra_editor_utils as hydra
from automatedtesting_shared.editor_test_helper import EditorTestHelper


class TestLandscapeCanvasSliceCreateInstantiate(EditorTestHelper):
    def __init__(self):
        EditorTestHelper.__init__(self, log_prefix="LandscapeCanvas_SliceCreateInstantiate", args=["level"])

    def run_test(self):
        """
        Summary:
        C22602016 A slice containing the LandscapeCanvas component can be created/instantiated.

        Expected Result:
        Slice is created and processed successfully and free of errors/warnings.
        Another copy of the slice is instantiated.

        :return: None
        """

        def path_is_valid_asset(asset_path):
            asset_id = asset.AssetCatalogRequestBus(bus.Broadcast, "GetAssetIdByPath", asset_path, math.Uuid(), False)
            return asset_id.invoke("IsValid")

        # Create empty level
        self.test_success = self.create_level(
            self.args["level"],
            heightmap_resolution=1024,
            heightmap_meters_per_pixel=1,
            terrain_texture_resolution=4096,
            use_terrain=False,
        )

        # Create entity with LandScape Canvas component
        position = math.Vector3(512.0, 512.0, 32.0)
        landscape_canvas = hydra.Entity("landscape_canvas_entity")
        landscape_canvas.create_entity(position, ["Landscape Canvas"])

        # Create slice from the created entity
        slice_path = os.path.join("slices", "TestSlice.slice")
        slice.SliceRequestBus(bus.Broadcast, "CreateNewSlice", landscape_canvas.id, slice_path)

        # Verify if slice is created
        self.wait_for_condition(lambda: path_is_valid_asset(slice_path), 5.0)
        self.log(f"Slice has been created successfully: {path_is_valid_asset(slice_path)}")

        # Instantiate slice
        transform = math.Transform_CreateIdentity()
        asset_id = asset.AssetCatalogRequestBus(bus.Broadcast, "GetAssetIdByPath", slice_path, math.Uuid(), False)
        test_slice = slice.SliceRequestBus(bus.Broadcast, "InstantiateSliceFromAssetId", asset_id, transform)
        self.wait_for_condition(lambda: test_slice.IsValid(), 3.0)
        self.log(f"Slice instantiated: {test_slice.IsValid()}")


test = TestLandscapeCanvasSliceCreateInstantiate()
test.run()