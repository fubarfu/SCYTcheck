"""
Unit tests for FileSelector component - folder selection and validation.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.components.file_selector import FileSelector


@pytest.fixture
def mock_parent():
    """Create a mock parent widget for tkinter."""
    # Use a MagicMock with proper tkinter internals
    mock = MagicMock()
    mock.tk = MagicMock()  # tkinter needs a tk attribute
    mock._last_child_ids = {}  # tkinter uses this for widget naming
    return mock


@pytest.fixture
def mock_parent():
    """Create a mock parent widget for tkinter."""
    # Use a MagicMock with proper tkinter internals
    mock = MagicMock()
    mock.tk = MagicMock()  # tkinter needs a tk attribute
    mock._last_child_ids = {}  # tkinter uses this for widget naming
    return mock


@pytest.fixture
def file_selector(mock_parent) -> FileSelector:
    """Create a FileSelector instance with mocked parent."""
    with patch('src.components.file_selector.tk.StringVar') as mock_stringvar, \
         patch('src.components.file_selector.ttk.Label') as mock_label, \
         patch('src.components.file_selector.ttk.Entry') as mock_entry, \
         patch('src.components.file_selector.ttk.Button') as mock_button:
        
        # Create mock StringVar instance with state management
        mock_stringvar_instance = MagicMock()
        # Use a dictionary to simulate StringVar's internal state
        stringvar_state = {"value": ""}
        
        def stringvar_get():
            return stringvar_state["value"]
        
        def stringvar_set(value):
            stringvar_state["value"] = value
        
        mock_stringvar_instance.get.side_effect = stringvar_get
        mock_stringvar_instance.set.side_effect = stringvar_set
        mock_stringvar.return_value = mock_stringvar_instance
        
        # Create mock widgets
        mock_label.return_value = MagicMock()
        mock_entry.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        
        selector = FileSelector(mock_parent, label_text="Test Output Folder")
        return selector


@pytest.fixture
def fs_factory(mock_parent):
    """Factory fixture for creating FileSelector instances with proper mocks."""
    def create_fs():
        with patch('src.components.file_selector.tk.StringVar') as mock_stringvar, \
             patch('src.components.file_selector.ttk.Label') as mock_label, \
             patch('src.components.file_selector.ttk.Entry') as mock_entry, \
             patch('src.components.file_selector.ttk.Button') as mock_button:
            
            # Create mock StringVar instance with state management
            mock_stringvar_instance = MagicMock()
            # Use a dictionary to simulate StringVar's internal state
            stringvar_state = {"value": ""}
            
            def stringvar_get():
                return stringvar_state["value"]
            
            def stringvar_set(value):
                stringvar_state["value"] = value
            
            mock_stringvar_instance.get.side_effect = stringvar_get
            mock_stringvar_instance.set.side_effect = stringvar_set
            mock_stringvar.return_value = mock_stringvar_instance
            
            # Create mock widgets
            mock_label.return_value = MagicMock()
            mock_entry.return_value = MagicMock()
            mock_button.return_value = MagicMock()
            
            return FileSelector(mock_parent)
    return create_fs


class TestFolderSelection:
    """Test folder selection dialog behavior."""
    
    def test_folder_selector_initialization(self, file_selector: FileSelector) -> None:
        """Test FileSelector initializes with empty path."""
        assert file_selector.get() == ""
    
    def test_set_path_programmatically(self, file_selector: FileSelector) -> None:
        """Test setting folder path programmatically."""
        test_path = "/test/folder"
        file_selector.set_path(test_path)
        assert file_selector.get() == test_path
    
    def test_set_path_with_whitespace(self, file_selector: FileSelector) -> None:
        """Test that get() strips whitespace from path."""
        file_selector.set_path("  /test/folder  ")
        assert file_selector.get() == "/test/folder"


class TestFolderValidation:
    """Test folder validation logic."""
    
    def test_validate_empty_path(self, file_selector: FileSelector) -> None:
        """Test validation fails for empty path."""
        is_valid, error_msg = file_selector.validate_selected_folder()
        assert not is_valid
        assert "select an output folder" in error_msg.lower()
    
    def test_validate_nonexistent_folder(self, file_selector: FileSelector) -> None:
        """Test validation fails for non-existent folder."""
        file_selector.set_path("/this/path/does/not/exist/anywhere")
        is_valid, error_msg = file_selector.validate_selected_folder()
        assert not is_valid
        assert "does not exist" in error_msg.lower()
    
    def test_validate_existing_folder(self, fs_factory) -> None:
        """Test validation passes for existing folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = fs_factory()
            fs.set_path(tmpdir)
            is_valid, error_msg = fs.validate_selected_folder()
            assert is_valid
            assert error_msg == ""
    
    def test_validate_file_not_directory(self, fs_factory) -> None:
        """Test validation fails when path is a file, not directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")
            
            fs = fs_factory()
            fs.set_path(str(test_file))
            is_valid, error_msg = fs.validate_selected_folder()
            
            assert not is_valid
            assert "not a directory" in error_msg.lower()
    
    def test_validate_read_only_folder(self, fs_factory) -> None:
        """Test validation fails for read-only folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = fs_factory()
            fs.set_path(tmpdir)
            
            # Mock os.access to return False for write permission
            with patch("src.components.file_selector.os.access", return_value=False):
                is_valid, error_msg = fs.validate_selected_folder()
                assert not is_valid
                assert "not writable" in error_msg.lower()
    
    def test_validate_writable_folder(self, fs_factory) -> None:
        """Test validation passes for writable folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = fs_factory()
            fs.set_path(tmpdir)
            
            # Verify folder is writable (should be true by default in temp)
            is_valid, error_msg = fs.validate_selected_folder()
            assert is_valid
            assert error_msg == ""


class TestErrorHandling:
    """Test error dialog and validation error display."""
    
    def test_show_validation_error_with_invalid_path(self, file_selector: FileSelector) -> None:
        """Test show_validation_error for invalid path."""
        file_selector.set_path("/nonexistent/path")
        
        with patch.object(file_selector, "show_error") as mock_show_error:
            result = file_selector.show_validation_error()
            
            assert not result
            mock_show_error.assert_called_once()
            call_args = mock_show_error.call_args
            assert "Invalid Output Folder" in call_args[0][0]
            assert "does not exist" in call_args[0][1].lower()
    
    def test_show_validation_error_with_valid_path(self, fs_factory) -> None:
        """Test show_validation_error for valid path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = fs_factory()
            fs.set_path(tmpdir)
            
            with patch.object(fs, "show_error") as mock_show_error:
                result = fs.show_validation_error()
                
                assert result
                mock_show_error.assert_not_called()
    
    def test_show_validation_error_empty_path(self, file_selector: FileSelector) -> None:
        """Test show_validation_error for empty path."""
        with patch.object(file_selector, "show_error") as mock_show_error:
            result = file_selector.show_validation_error()
            
            assert not result
            mock_show_error.assert_called_once()
            call_args = mock_show_error.call_args
            assert "select an output folder" in call_args[0][1].lower()


class TestFolderValidationMessages:
    """Test that error messages are user-friendly."""
    
    def test_error_message_clarity(self, file_selector: FileSelector) -> None:
        """Test error messages are clear and actionable."""
        test_cases = [
            ("/nonexistent", "does not exist", "select a valid folder"),
            ("", "select an output folder", "before proceeding"),
        ]
        
        for path, expected_substr1, expected_substr2 in test_cases:
            file_selector.set_path(path)
            is_valid, error_msg = file_selector.validate_selected_folder()
            
            if not is_valid:
                assert expected_substr1.lower() in error_msg.lower()
                assert expected_substr2.lower() in error_msg.lower()
    
    def test_path_shown_in_error_message(self, file_selector: FileSelector) -> None:
        """Test that invalid path is shown in error message."""
        invalid_path = "/some/invalid/test/path/here"
        file_selector.set_path(invalid_path)
        
        is_valid, error_msg = file_selector.validate_selected_folder()
        assert not is_valid
        assert invalid_path in error_msg


class TestFolderSelectorIntegration:
    """Integration tests for folder selector workflow."""
    
    def test_valid_workflow_select_and_validate(self, fs_factory) -> None:
        """Test complete workflow: select folder and validate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = fs_factory()
            
            # Step 1: Set folder
            fs.set_path(tmpdir)
            assert fs.get() == tmpdir
            
            # Step 2: Validate
            with patch.object(fs, "show_error") as mock_show_error:
                is_valid = fs.show_validation_error()
                assert is_valid
                mock_show_error.assert_not_called()
    
    def test_error_workflow_select_invalid_and_validate(self, file_selector: FileSelector) -> None:
        """Test workflow with invalid selection."""
        invalid_path = "/this/does/not/exist"
        file_selector.set_path(invalid_path)
        
        with patch.object(file_selector, "show_error") as mock_show_error:
            is_valid = file_selector.show_validation_error()
            
            assert not is_valid
            mock_show_error.assert_called_once()
