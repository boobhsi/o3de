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

import azlmbr.bus as bus
import azlmbr.editor as editor
import azlmbr.entity as entity
import azlmbr.paths

sys.path.append(os.path.join(azlmbr.paths.devroot, 'AutomatedTesting', 'Gem', 'PythonTests'))
import automatedtesting_shared.hydra_editor_utils as hydra
from automatedtesting_shared.editor_test_helper import EditorTestHelper


class TestImageGradientRequiresShape(EditorTestHelper):
    def __init__(self):
        EditorTestHelper.__init__(self, log_prefix="ImageGradientRequiresShape", args=["level"])

    def run_test(self):
        """
        Summary:
        Verify that Image Gradient component requires a
        Shape component before the Entity can become active.

        :return: None
        """
        # Create a new empty level
        self.test_success = self.create_level(
            self.args["level"],
            heightmap_resolution=1024,
            heightmap_meters_per_pixel=1,
            terrain_texture_resolution=4096,
            use_terrain=False,
        )

        # Create a new Entity in the level
        entity_id = editor.ToolsApplicationRequestBus(bus.Broadcast, 'CreateNewEntity', entity.EntityId())

        # Add an Image Gradient and Gradient Transform Component (should be disabled until a Shape exists on the Entity)
        image_gradient_component = hydra.add_component('Image Gradient', entity_id)
        hydra.add_component('Gradient Transform Modifier', entity_id)

        # Verify the Image Gradient Component is not active before adding the Shape
        active = editor.EditorComponentAPIBus(bus.Broadcast, 'IsComponentEnabled', image_gradient_component)
        self.test_success = self.test_success and not active
        if not active:
            self.log("Image Gradient component is not active without a Shape component on the Entity")

        # Add a Shape component to the same Entity
        hydra.add_component('Box Shape', entity_id)

        # Check if the Image Gradient Component is active now after adding the Shape
        active = editor.EditorComponentAPIBus(bus.Broadcast, 'IsComponentEnabled', image_gradient_component)
        self.test_success = self.test_success and active
        if active:
            self.log("Image Gradient component is active now that the Entity has a Shape")


test = TestImageGradientRequiresShape()
test.run()