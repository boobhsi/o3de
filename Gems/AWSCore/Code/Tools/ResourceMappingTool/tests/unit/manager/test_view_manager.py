"""
All or portions of this file Copyright (c) Amazon.com, Inc. or its affiliates or
its licensors.

For complete copyright and license terms please see the LICENSE at the root of this
distribution (the "License"). All use of this software is governed by the License,
or, if provided, by the license below or the license accompanying this file. Do not
remove or modify any license notices. This file is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from typing import List
from unittest import TestCase
from unittest.mock import (call, MagicMock, patch)

from manager.view_manager import (ViewManager, ViewManagerConstants)


class TestViewManager(TestCase):
    """
    ThreadManager unit test cases
    """
    _mock_import_resources_page: MagicMock
    _mock_view_edit_page: MagicMock
    _mock_main_window: MagicMock
    _mock_stacked_pages: MagicMock
    _expected_view_manager: ViewManager

    @classmethod
    def setUpClass(cls) -> None:
        import_resources_page_patcher: patch = patch("manager.view_manager.ImportResourcesPage")
        cls._mock_import_resources_page = import_resources_page_patcher.start()

        view_edit_page_patcher: patch = patch("manager.view_manager.ViewEditPage")
        cls._mock_view_edit_page = view_edit_page_patcher.start()

        main_window_patcher: patch = patch("manager.view_manager.QMainWindow")
        cls._mock_main_window = main_window_patcher.start()

        stacked_pages_patcher: patch = patch("manager.view_manager.QStackedWidget")
        cls._mock_stacked_pages = stacked_pages_patcher.start()

        cls._expected_view_manager = ViewManager()

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()

    def setUp(self) -> None:
        TestViewManager._mock_view_edit_page.reset_mock()
        TestViewManager._mock_import_resources_page.reset_mock()
        TestViewManager._mock_main_window.reset_mock()
        TestViewManager._mock_stacked_pages.reset_mock()

    def test_get_instance_return_same_instance(self) -> None:
        assert ViewManager.get_instance() is TestViewManager._expected_view_manager

    def test_get_instance_raise_exception(self) -> None:
        self.assertRaises(Exception, ViewManager)

    def test_get_import_resources_page_return_expected_page(self) -> None:
        expected_page: MagicMock = TestViewManager._mock_import_resources_page.return_value
        mocked_stacked_pages: MagicMock = TestViewManager._mock_stacked_pages.return_value
        mocked_stacked_pages.widget.return_value = expected_page

        actual_page: MagicMock = TestViewManager._expected_view_manager.get_import_resources_page()
        mocked_stacked_pages.widget.assert_called_once_with(ViewManagerConstants.IMPORT_RESOURCES_PAGE_INDEX)
        assert actual_page == expected_page

    def test_get_view_edit_page_return_expected_page(self) -> None:
        expected_page: MagicMock = TestViewManager._mock_view_edit_page.return_value
        mocked_stacked_pages: MagicMock = TestViewManager._mock_stacked_pages.return_value
        mocked_stacked_pages.widget.return_value = expected_page

        actual_page: MagicMock = TestViewManager._expected_view_manager.get_view_edit_page()
        mocked_stacked_pages.widget.assert_called_once_with(ViewManagerConstants.VIEW_AND_EDIT_PAGE_INDEX)
        assert actual_page == expected_page

    def test_setup_expected_page_gets_added_in_order(self) -> None:
        mocked_stacked_pages: MagicMock = TestViewManager._mock_stacked_pages.return_value
        mocked_import_resources_page: MagicMock = TestViewManager._mock_import_resources_page.return_value
        mocked_view_edit_page: MagicMock = TestViewManager._mock_view_edit_page.return_value

        TestViewManager._expected_view_manager.setup()
        mocked_calls: List[call] = [call(mocked_view_edit_page), call(mocked_import_resources_page)]
        mocked_stacked_pages.addWidget.assert_has_calls(mocked_calls)

    def test_show_stacked_pages_show_with_expected_index(self) -> None:
        mocked_stacked_pages: MagicMock = TestViewManager._mock_stacked_pages.return_value
        mocked_main_window: MagicMock = TestViewManager._mock_main_window.return_value

        TestViewManager._expected_view_manager.show()
        mocked_stacked_pages.setCurrentIndex.assert_called_once_with(ViewManagerConstants.VIEW_AND_EDIT_PAGE_INDEX)
        mocked_main_window.show.assert_called_once()

    def test_switch_to_view_edit_page_stacked_pages_switch_to_expected_index(self) -> None:
        mocked_stacked_pages: MagicMock = TestViewManager._mock_stacked_pages.return_value

        TestViewManager._expected_view_manager.switch_to_view_edit_page()
        mocked_stacked_pages.setCurrentIndex.assert_called_once_with(ViewManagerConstants.VIEW_AND_EDIT_PAGE_INDEX)

    def test_switch_to_import_resources_page_stacked_pages_switch_to_expected_index_and_set_with_expected_state(self) -> None:
        mocked_stacked_pages: MagicMock = TestViewManager._mock_stacked_pages.return_value
        expected_page: MagicMock = TestViewManager._mock_import_resources_page.return_value
        mocked_stacked_pages.widget.return_value = expected_page
        expected_search_version: str = "dummy_search"

        TestViewManager._expected_view_manager.switch_to_import_resources_page(expected_search_version)
        mocked_stacked_pages.setCurrentIndex.assert_called_once_with(ViewManagerConstants.IMPORT_RESOURCES_PAGE_INDEX)
        assert expected_page.search_version == expected_search_version