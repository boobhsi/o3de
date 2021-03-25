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
import azlmbr.editor.graph as graph
import azlmbr.legacy.general as general
import azlmbr.paths

sys.path.append(os.path.join(azlmbr.paths.devroot, 'AutomatedTesting', 'Gem', 'PythonTests'))
from automatedtesting_shared.editor_test_helper import EditorTestHelper

editorId = azlmbr.globals.property.LANDSCAPE_CANVAS_EDITOR_ID
newRootEntityId = None


class TestGraphClosedOnEntityDelete(EditorTestHelper):

    def __init__(self):
        EditorTestHelper.__init__(self, log_prefix="GraphClosedOnEntityDelete", args=["level"])

    def run_test(self):

        def onEntityCreated(parameters):
            global newRootEntityId
            newRootEntityId = parameters[0]

        # Create a new empty level
        self.test_success = self.create_level(
            self.args["level"],
            heightmap_resolution=128,
            heightmap_meters_per_pixel=1,
            terrain_texture_resolution=128,
            use_terrain=False,
        )

        # Open Landscape Canvas tool and verify
        general.open_pane('Landscape Canvas')
        self.test_success = self.test_success and general.is_pane_visible('Landscape Canvas')
        if general.is_pane_visible('Landscape Canvas'):
            self.log('Landscape Canvas pane is open')

        # Listen for entity creation notifications so we can store the top-level Entity created
        # when a new graph is created, and then delete it to test if the graph is closed
        handler = editor.EditorEntityContextNotificationBusHandler()
        handler.connect()
        handler.add_callback('OnEditorEntityCreated', onEntityCreated)

        # Create a new graph in Landscape Canvas and verify
        newGraphId = graph.AssetEditorRequestBus(bus.Event, 'CreateNewGraph', editorId)
        graphIsOpen = graph.AssetEditorRequestBus(bus.Event, 'ContainsGraph', editorId, newGraphId)
        self.test_success = self.test_success and graphIsOpen
        if graphIsOpen:
            self.log("Graph registered with Landscape Canvas")

        # Delete the top-level Entity created by the new graph
        editor.ToolsApplicationRequestBus(bus.Broadcast, 'DeleteEntityById', newRootEntityId)

        # We need to delay here because the closing of the graph due to Entity deletion
        # is actually queued in order to workaround an undo/redo issue
        # Alternatively, we could add a notifications bus for AssetEditorRequests
        # that could trigger when graphs are opened/closed and then do the check there
        general.idle_enable(True)
        general.idle_wait(1.0)

        # Verify that the corresponding graph is no longer open
        graphIsClosed = not graph.AssetEditorRequestBus(bus.Event, 'ContainsGraph', editorId, newGraphId)
        self.test_success = self.test_success and graphIsClosed
        if graphIsClosed:
            self.log("The graph is no longer open after deleting the Entity")

        # Stop listening for entity creation notifications
        handler.disconnect()


test = TestGraphClosedOnEntityDelete()
test.run()