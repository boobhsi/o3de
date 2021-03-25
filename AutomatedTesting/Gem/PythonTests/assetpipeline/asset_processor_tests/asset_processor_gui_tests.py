"""
All or portions of this file Copyright (c) Amazon.com, Inc. or its affiliates or
its licensors.

For complete copyright and license terms please see the LICENSE at the root of this
distribution (the "License"). All use of this software is governed by the License,
or, if provided, by the license below or the license accompanying this file. Do not
remove or modify any license notices. This file is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

General Asset Processor GUI Tests
"""

# Import builtin libraries
import pytest
import logging
import os
import time
import configparser
from pathlib import Path

# Import LyTestTools
import ly_test_tools.builtin.helpers as helpers
import ly_test_tools.environment.waiter as waiter
import ly_test_tools.environment.file_system as fs
import ly_test_tools.environment.process_utils as process_utils
import ly_test_tools.launchers.launcher_helper as launcher_helper
from ly_test_tools.lumberyard.asset_processor import ASSET_PROCESSOR_PLATFORM_MAP
from ly_test_tools.lumberyard.asset_processor import AssetProcessorError

# Import fixtures
from ..ap_fixtures.asset_processor_fixture import asset_processor as asset_processor
from ..ap_fixtures.ap_setup_fixture import ap_setup_fixture as ap_setup_fixture
from ..ap_fixtures.ap_idle_fixture import TimestampChecker
from ..ap_fixtures.ap_fast_scan_setting_backup_fixture import (
    ap_fast_scan_setting_backup_fixture as fast_scan_backup,
)


# Import LyShared
import ly_test_tools.lumberyard.pipeline_utils as utils

# Use the following logging pattern to hook all test logging together:
logger = logging.getLogger(__name__)
# Configuring the logging is done in ly_test_tools at the following location:
# ~/dev/Tools/LyTestTools/ly_test_tools/log/py_logging_util.py

# Helper: variables we will use for parameter values in the test:
targetProjects = ["AutomatedTesting"]



@pytest.fixture
def local_resources(request, workspace, ap_setup_fixture):
    # Test-level asset folder. Directory contains a subfolder for each test (i.e. C1234567)
    ap_setup_fixture["tests_dir"] = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def ap_idle(workspace, ap_setup_fixture):
    gui_timeout_max = 30
    return TimestampChecker(workspace.paths.asset_catalog(ASSET_PROCESSOR_PLATFORM_MAP[workspace.asset_processor_platform]), gui_timeout_max)


@pytest.mark.usefixtures("asset_processor")
@pytest.mark.usefixtures("ap_setup_fixture")
@pytest.mark.usefixtures("local_resources")
@pytest.mark.parametrize("project", targetProjects)
@pytest.mark.SUITE_sandbox
@pytest.mark.assetpipeline
class TestsAssetProcessorGUI_Windows(object):
    """
    Specific Tests for Asset Processor GUI To Only Run on Windows
    """

    @pytest.mark.assetpipeline
    def test_SendInputOnControlChannel_ReceivedAndResponded(self, asset_processor):
        """
        Test that the control channel connects and that communication works both directions
        """

        asset_processor.create_temp_asset_root()

        # start the AP
        asset_processor.gui_process()
        asset_processor.send_message("ping")
        output_message = asset_processor.read_message()
        assert output_message == "pong", "Failed to receive response on control channel socket"
        asset_processor.stop()

    @pytest.mark.test_case_id("C1564070")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    def test_WindowsPlatforms_ProcessAssets_ReprocessDeletedCache(self, asset_processor, workspace):
        """
        Deleting assets from Cache will make them re-processed in the already running AP
        """

        START_UP_SECONDS = 3
        asset_processor.create_temp_asset_root()
        asset_processor.add_source_folder_assets(os.path.join(workspace.project, 'Fonts'))
        font_path = os.path.join(asset_processor.temp_project_cache(), "fonts")

        # start the AP
        result, _ = asset_processor.gui_process()
        assert result, "AP GUI failed"

        # check that files exist in the cache: dev\Cache\AutomatedTesting\pc\automatedtesting\fonts
        assert os.path.exists(font_path), "Fonts folder was not found initially."

        # delete the cached files
        assert fs.delete([font_path], True, True), "File System could not delete the Fonts directory."

        # Wait for the above work to complete
        asset_processor.next_idle()

        # check that the cached files exist again
        assert os.path.exists(font_path), "Fonts folder was not found after waiting for rebuild."

        # close the AP
        asset_processor.stop()

    @pytest.mark.test_case_id("C1564065")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    # fmt:off
    def test_WindowsPlatforms_RemoveProjectAssets_ProcessedAssetsDeleted(self, asset_processor, ap_setup_fixture,
                                                                         ):
        # fmt:on
        """
        Asset Processor Deletes processed assets when source is removed from project folder (while running)
        """
        env = ap_setup_fixture

        # Copy test assets to project folder and verify test assets folder exists
        test_assets_folder, _ = asset_processor.prepare_test_environment(env["tests_dir"], "C1564065")
        assert os.path.exists(test_assets_folder), f"Test assets folder was not copied {test_assets_folder}"

        # Start Asset Processor GUI
        result, _ = asset_processor.gui_process(quitonidle=False)
        assert result, "AP GUI failed"

        # Wait for test assets to be copied to cache or timeout
        def test_assets_copied_to_cache() -> bool:
            missing_assets, _ = asset_processor.compare_assets_with_cache(
            )
            return not missing_assets

        waiter.wait_for(test_assets_copied_to_cache, timeout=10, exc=Exception("Test assets are missing from cache"))

        asset_processor.clear_project_test_assets_dir()

        # Wait for test assets to be deleted from cache or timeout
        def test_assets_deleted_from_cache() -> bool:
            _, existing_assets = asset_processor.compare_assets_with_cache(
            )
            return not existing_assets

        waiter.wait_for(test_assets_deleted_from_cache, timeout=10, exc=Exception("Test assets are lingering in cache"))

        # Stop Asset Processor GUI
        asset_processor.stop()

    @pytest.mark.test_case_id("C1591563")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    # fmt:off
    def test_WindowsPlatforms_ModifyAsset_UpdatedAssetProcessed(self, asset_processor, ap_setup_fixture,
                                                                ):
        # fmt:on
        """
        Processing changed files (while running)
        """
        env = ap_setup_fixture

        # Copy test assets to project folder and verify test assets folder exists
        test_assets_folder, cache_path = asset_processor.prepare_test_environment(env["tests_dir"], "C1591563")
        assert os.path.exists(test_assets_folder), f"Test assets folder was not copied {test_assets_folder}"

        # Save path to test asset in project folder and path to test asset in cache
        project_asset_path = os.path.join(test_assets_folder, "C1591563_test_asset.txt")
        cache_asset_path = os.path.join(cache_path, "C1591563_test_asset.txt")

        result, _ = asset_processor.gui_process(quitonidle=False)
        assert result, "AP GUI failed"

        # Verify contents of test asset in project folder before modication
        with open(project_asset_path, "r") as project_asset_file:
            assert project_asset_file.read() == "before_state"

        # Verify contents of cached asset before modification
        with open(cache_asset_path, "r") as cache_asset_file:
            assert cache_asset_file.read() == "before_state"

        # Modify contents of test asset in project folder
        fs.unlock_file(project_asset_path)
        with open(project_asset_path, "w") as project_asset_file:
            project_asset_file.write("after_state")

        # Wait for AP to have finished processing
        asset_processor.next_idle()

        # Verify contents of test asset in project folder after modification
        with open(project_asset_path, "r") as project_asset_file:
            assert project_asset_file.read() == "after_state"

        # Verify contents of cached asset after modification
        with open(cache_asset_path, "r") as cache_asset_file:
            assert cache_asset_file.read() == "after_state"

        asset_processor.stop()

    @pytest.mark.test_case_id("C24168803")
    @pytest.mark.BAT
    @pytest.mark.SUITE_sandbox
    @pytest.mark.assetpipeline
    def test_WindowsPlatforms_RunAP_ProcessesIdle(self, asset_processor):
        """
        Asset Processor goes idle
        """
        CPU_USAGE_THRESHOLD = 1.0  # CPU usage percentage delimiting idle from active
        CPU_USAGE_WIND_DOWN = 10  # Time allowed in seconds for idle processes to stop using CPU

        asset_processor.create_temp_asset_root()

        # Launch Asset Processor and wait for it to go idle
        result, _ = asset_processor.gui_process(quitonidle=False)
        assert result, "AP GUI failed"

        # Wait for AssetProcessor process to wrap up and reach <1% CPU usage after idle status has been flagged
        waiter.wait_for(
            lambda: asset_processor.process_cpu_usage_below(CPU_USAGE_THRESHOLD),
            timeout=CPU_USAGE_WIND_DOWN,
            exc=Exception("Asset Processor did not reach <1% CPU usage before timeout"),
        )

        # Stop Asset Processor GUI
        asset_processor.stop()

    @pytest.mark.test_case_id("C1564064")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    def test_WindowsPlatforms_AddAssetsWhileRunning_AssetsProcessed(
        self, ap_setup_fixture, workspace, asset_processor
    ):
        """
        Processing newly added files to project folder (while running)
        """
        env = ap_setup_fixture
        level_name = "C1564064_level"
        new_asset = "C1564064.scriptcanvas"
        new_asset_lower = new_asset.lower()

        asset_processor.create_temp_asset_root()
        assets_src_path = os.path.join(env["tests_dir"], "assets", "C1564064")
        level_dst_path = os.path.join(asset_processor.temp_asset_root(), workspace.project, "Levels")
        project_level_dir = os.path.join(level_dst_path, level_name)
        cache_level_dir = os.path.join(asset_processor.temp_project_cache(), "levels", level_name.lower())

        # Expected test asset sources and products
        exp_project_level_assets = [
            "filelist.xml",
            "level.pak",
            "tags.txt",
            "terraintexture.pak",
            f"{level_name}.ly",
            os.path.join("leveldata", "Environment.xml"),
            os.path.join("leveldata", "Heightmap.dat"),
            os.path.join("leveldata", "TerrainTexture.xml"),
            os.path.join("leveldata", "TimeOfDay.xml"),
            os.path.join("leveldata", "VegetationMap.dat"),
            os.path.join("terrain", "cover.ctc"),
        ]
        exp_project_test_assets = [new_asset]
        exp_cache_level_assets = [asset.lower() for asset in exp_project_level_assets if not asset.endswith(".ly")]
        exp_cache_test_assets = [new_asset_lower, f"{new_asset_lower}_compiled"]

        result, _ = asset_processor.gui_process(quitonidle=False)
        assert result, "AP GUI failed"

        # Add the prepared level and the additional asset to project folder and wait for AP idle
        if not os.path.isdir(level_dst_path):
            os.makedirs(level_dst_path)
        fs.unzip(level_dst_path, os.path.join(assets_src_path, f"{level_name}.zip"))
        test_project_asset_dir = os.path.join(asset_processor.temp_asset_root(), workspace.project,
                                              env["test_asset_dir_name"])

        asset_processor.copy_assets_to_project([new_asset], assets_src_path, test_project_asset_dir)
        asset_processor.next_idle()

        # Verify level and test assets in project folder
        level_assets_list = utils.get_relative_file_paths(project_level_dir)
        test_assets_list = utils.get_relative_file_paths(test_project_asset_dir)
        # fmt:off
        assert utils.compare_lists(level_assets_list, exp_project_level_assets), \
            "One or more assets is missing between the level in the project and its expected source assets"
        assert utils.compare_lists(test_assets_list, exp_project_test_assets), \
            "One or more assets is missing between the test assets in the project and the expected source assets"
        # fmt:on

        # Verify level and test assets in cache folder
        level_assets_list = utils.get_relative_file_paths(cache_level_dir)
        test_assets_list = utils.get_relative_file_paths(os.path.join(asset_processor.temp_project_cache(),
                                                                      env["test_asset_dir_name"]))
        # fmt:off
        assert utils.compare_lists(level_assets_list, exp_cache_level_assets), \
            "One or more assets is missing between the level in the cache and its expected product assets"
        assert utils.compare_lists(test_assets_list, exp_cache_test_assets), \
            "One or more assets is missing between the test assets in the cache and the expected product assets"
        # fmt:on
        asset_processor.stop()

    @pytest.mark.test_case_id("C24256593")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    def test_WindowsPlatforms_LaunchAP_LogReportsIdle(self, asset_processor, workspace, ap_idle):
        """
        Asset Processor creates a log entry when it goes idle
        """
        asset_processor.create_temp_asset_root()
        # Run batch process to ensure project assets are processed
        assert asset_processor.batch_process(), "AP Batch failed"

        ap_idle.set_file_path(workspace.paths.ap_gui_log())
        # Launch Asset Processor and wait for it to go idle
        result, _ = asset_processor.gui_process()
        assert result, "AP GUI failed"
        ap_idle.check_if_idle()
        asset_processor.stop()


    @pytest.mark.assetpipeline
    def test_APStopTimesOut_ExceptionThrown(self, ap_setup_fixture, asset_processor):
        asset_processor.create_temp_asset_root()
        asset_processor.start()

        # Copy in some assets, so that the AP will be busy when the stop command is called.
        asset_processor.prepare_test_environment(ap_setup_fixture["tests_dir"], "TimeOutTest")

        ap_quit_timed_out = False
        try:
            asset_processor.stop(timeout=1)
        except AssetProcessorError:
            ap_quit_timed_out = True
        assert ap_quit_timed_out, "AP did not time out as expected"


    @pytest.mark.assetpipeline
    def test_APStopDefaultTimeout_NoException(self, asset_processor):
        # If this test fails, it means other tests using the default timeout may have issues.
        # In that case, either the default timeout should either be raised, or the performance
        # of AP launching should be improved.
        asset_processor.create_temp_asset_root()
        asset_processor.start()
        ap_quit_timed_out = False
        try:
            asset_processor.stop()
        except AssetProcessorError:
            ap_quit_timed_out = True
        assert not ap_quit_timed_out, "AP timed out"