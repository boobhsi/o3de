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
@pytest.mark.assetpipeline
class TestsAssetProcessorGUI_WindowsAndMac(object):
    """
    Specific Tests for Asset Processor GUI To Only Run on Windows and Mac
    """

    @pytest.mark.test_case_id("C3540434")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    def test_WindowsAndMacPlatforms_AP_GUI_FastScanSettingCreated(self, asset_processor, fast_scan_backup):
        """
         Tests that a fast scan settings entry gets created for the AP if it does not exist
         and ensures that the entry is defaulted to fast-scan enabled
        """

        asset_processor.create_temp_asset_root()
        fast_scan_setting = fast_scan_backup

        # Delete registry value (if it exists)
        fast_scan_setting.delete_entry()

        # Make sure registry was deleted
        assert not fast_scan_setting.entry_exists(), "Registry Key's Value was not deleted"

        # AssetProcessor registry value should be set to true once AssetProcessor.exe has been executed
        result, _ = asset_processor.gui_process(quitonidle=False)
        assert result, "AP GUI failed"

        # Wait for AP GUI long enough to create the registry entry before killing AP
        waiter.wait_for(
            lambda: fast_scan_setting.entry_exists(),
            timeout=20,
            exc=Exception("AP failed to create a fast scan setting in 20 seconds"),
        )

        # Ensure that the DEFAULT value for fast scan is ENABLED
        key_value = fast_scan_setting.get_value()
        asset_processor.stop()

        assert key_value.lower() == "true", f"The fast scan setting found was {key_value}"

    @pytest.mark.test_case_id("C3635822")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    @pytest.mark.skip("Not working in Jenkins")
    # fmt:off
    def test_WindowsMacPlatforms_GUIFastScanEnabled_GameLauncherWorksWithAP(self, asset_processor, workspace,
                                                                            fast_scan_backup):
        # fmt:on
        """
        Make sure game launcher working with Asset Processor set to turbo mode
        Validate that no fatal errors (crashes) are reported within a certain
        time frame for the AP and the GameLauncher
        """
        CHECK_ALIVE_SECONDS = 15

        # AP is running in turbo mode
        fast_scan = fast_scan_backup
        fast_scan.set_value("True")

        value = fast_scan.get_value()
        assert value.lower() == "true", f"The fast scan setting found is {value}"

        # Launch GameLauncher.exe with Null Renderer enabled so that Non-GPU Automation Nodes don't fail on the renderer
        launcher = launcher_helper.create_launcher(workspace, ["-NullRenderer"])
        launcher.start()

        # Validate that no fatal errors (crashes) are reported within a certain time frame (10 seconds timeout)
        #   This applies to AP and GameLauncher.exe
        time.sleep(CHECK_ALIVE_SECONDS)
        launcher_name = f"{workspace.project.title()}Launcher"
        # fmt:off
        assert process_utils.process_exists(launcher_name, ignore_extensions=True), \
            f"{launcher_name} was not live during the check."
        assert process_utils.process_exists("AssetProcessor", ignore_extensions=True), \
            "AssetProcessor was not live during the check."
        # fmt:on

        launcher.stop()


@pytest.mark.usefixtures("asset_processor")
@pytest.mark.usefixtures("ap_setup_fixture")
@pytest.mark.usefixtures("local_resources")
@pytest.mark.parametrize("project", targetProjects)
@pytest.mark.assetpipeline
class TestsAssetProcessorGUI_AllPlatforms(object):
    """
    Tests for Asset Processor GUI To Run on All Supported Host Platforms
    """

    @pytest.mark.test_case_id("C1591337")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    # fmt:off
    def test_AllSupportedPlatforms_DeleteCachedAssets_AssetsReprocessed(self, ap_setup_fixture,
                                                                        asset_processor):
        # fmt:on
        """
        Deleting slices and uicanvases while AP is running
        """
        env = ap_setup_fixture

        # Copy test assets to project folder and verify test assets folder exists in project folder
        test_assets_folder, cache_folder = asset_processor.prepare_test_environment(env["tests_dir"], "C1591337")
        assert os.path.exists(test_assets_folder), f"Test assets folder was not found {test_assets_folder}"

        # Launch Asset Processor and wait for it to go idle
        result, _ = asset_processor.gui_process(quitonidle=False)
        assert result, "AP GUI failed"

        # Verify test assets were added to cache
        def test_assets_added_to_cache() -> bool:
            missing_assets, _ = asset_processor.compare_assets_with_cache()
            return not missing_assets

        assert test_assets_added_to_cache(), "Test assets are missing from cache"

        # Delete test assets from cache
        asset_processor.delete_temp_cache()

        asset_processor.next_idle()

        # Verify test assets were repopulated in cache
        assert test_assets_added_to_cache(), "Test assets are missing from cache"
        asset_processor.stop()

    @pytest.mark.test_case_id("C4874115")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    def test_AllSupportedPlatforms_AddScanFolder_AssetsProcessed(
        self, ap_setup_fixture, asset_processor, workspace, request
    ):
        """
        Process slice files and uicanvas files from the additional scanfolder
        """
        env = ap_setup_fixture
        # Copy test assets to new folder in dev folder
        # This new folder will be created outside the default project folder and will not be added as a scan folder
        # by default, instead we'll modify the temporary AssetProcessorPlatformConfig.ini to add it
        test_assets_folder, cache_folder = asset_processor.prepare_test_environment(env["tests_dir"], "C4874115",
                                                                                    relative_asset_root='',
                                                                                    add_scan_folder=False)
        assert os.path.exists(test_assets_folder), f"Test assets folder was not found {test_assets_folder}"

        # Run AP Batch
        assert asset_processor.batch_process(), "AP Batch failed"

        # Check whether assets currently exist in the cache
        def test_assets_added_to_cache():
            missing_assets, _ = asset_processor.compare_assets_with_cache()
            return not missing_assets

        assert not test_assets_added_to_cache(), "Test assets are present in cache before adding scan folder"

        # Add test assets folder in dev to AP config file (AssetProcessorPlatformConfig.ini) to be scanned
        ap_config_file = os.path.join(asset_processor.temp_asset_root(), 'AssetProcessorPlatformConfig.ini')
        config = configparser.ConfigParser()
        config.read(ap_config_file)
        config["ScanFolder C4874115"] = {
            "watch": "@ROOT@/C4874115",
            "output": "C4874115",
            "recursive": "1",
            "order": "5000",
        }
        with open(ap_config_file, "w") as configfile:
            config.write(configfile)

        # Run AP GUI and read the config file we just modified to pick up our scan folder
        # Pass in a pattern so we don't spend time processing unrelated folders
        result, _ = asset_processor.gui_process(quitonidle=True, add_config_scan_folders=True,
                                                scan_folder_pattern="*C4874115*")
        assert result, "AP GUI failed"

        # Verify test assets processed into cache after adding scan folder
        assert test_assets_added_to_cache(), "Test assets are missing from cache after adding scan folder"

    @pytest.mark.test_case_id("C4874114")
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    @pytest.mark.skip("Flaky test")
    def test_AllSupportedPlatforms_InvalidAddress_AssetsProcessed(self, workspace, request, asset_processor):
        """
        Launch AP with invalid address in bootstrap.cfg
        Assets should process regardless of the new address
        """
        test_ip_address = "1.1.1.1"  # an IP address without Asset Processor

        asset_processor.create_temp_asset_root()
        # Edit remote_ip setting in bootstrap.cfg to an IP address without Asset Processor
        workspace.settings.modify_bootstrap_setting("remote_ip", test_ip_address,
                                                    bootstrap_path=os.path.join(asset_processor.temp_asset_root(),
                                                                                'bootstrap.cfg'))

        # Run AP Gui to verify that assets process regardless of the new address
        result, _ = asset_processor.gui_process(quitonidle=True)
        assert result, "AP GUI failed"

    @pytest.mark.test_case_id("C24168802")
    @pytest.mark.SUITE_sandbox
    @pytest.mark.BAT
    @pytest.mark.assetpipeline
    def test_AllSupportedPlatforms_ModifyAssetInfo_AssetsReprocessed(self, ap_setup_fixture, asset_processor):
        """
        Modifying assetinfo files triggers file reprocessing
        """
        env = ap_setup_fixture

        # Expected test asset sources and products
        # *.assetinfo and *.fbx files are not produced in cache, and file.fbx produces file.actor in cache
        expected_test_assets = ["jack.cdf", "Jack.fbx", "Jack.fbx.assetinfo", "Jack.mtl"]
        expected_cache_assets = ["jack.actor", "jack.cdf", "jack.mtl"]

        # Copy test assets to project folder and verify test assets folder exists
        test_assets_folder, cache_folder = asset_processor.prepare_test_environment(env["tests_dir"], "C24168802")
        assert os.path.exists(test_assets_folder), f"Test assets folder was not found {test_assets_folder}"

        # Collect test asset relative paths and verify original test assets
        test_assets_list = utils.get_relative_file_paths(test_assets_folder)
        assert utils.compare_lists(test_assets_list, expected_test_assets), "Test assets are not as expected"

        # Run AP Gui
        result, _ = asset_processor.gui_process(run_until_idle=True)
        assert result, "AP GUI failed"

        # Verify test assets in cache folder
        cache_assets_list = utils.get_relative_file_paths(cache_folder)
        # fmt:off
        assert utils.compare_lists(cache_assets_list, expected_cache_assets), \
            "One or more assets is missing between project folder and cache folder"
        # fmt:on

        # Grab timestamps of cached assets before edit of *.assetinfo file in project folder
        timestamps = [os.stat(os.path.join(cache_folder, asset)).st_mtime for asset in cache_assets_list]

        # Append new line to contents of *.assetinfo file in project folder
        asset_info_list = [item for item in test_assets_list if Path(item).suffix == '.assetinfo']
        assetinfo_paths_list = [os.path.join(test_assets_folder, item) for item in asset_info_list]
        for assetinfo_path in assetinfo_paths_list:
            fs.unlock_file(assetinfo_path)
            with open(assetinfo_path, "a") as project_asset_file:
                project_asset_file.write("\n")

        asset_processor.next_idle()
        asset_processor.stop()

        # Verify new timestamp for *.actor file in cache folder after edit of *.assetinfo file in project folder
        for asset in cache_assets_list:
            if ".actor" in asset:
                # fmt:off
                assert os.stat(os.path.join(cache_folder, asset)).st_mtime not in timestamps, \
                    f"Cached {asset} was not updated"
                # fmt: on