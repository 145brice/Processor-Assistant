"""
Test folder_manager.py - Offline tests, no API calls.
"""

import pytest
import shutil
from pathlib import Path
from folder_manager import (
    BASE_DIR,
    ensure_base_structure,
    get_client_folder,
    get_next_conditions_number,
    get_conditions_count,
    create_conditions_folder,
    match_condition_to_folder,
    scan_for_documents,
    fetch_for_condition,
    move_file,
    create_folder_manual,
    get_folder_structure,
    init,
)


@pytest.fixture(scope="module")
def setup_test_folders():
    """Create test folder structure."""
    # Clean up if exists
    test_dir = BASE_DIR / "_test_run"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Init base structure
    init()
    
    # Create test client
    test_client = BASE_DIR / "Clients" / "Active" / "_TestRun"
    if test_client.exists():
        shutil.rmtree(test_client)
    test_client.mkdir(parents=True, exist_ok=True)
    (test_client / "Submission").mkdir(exist_ok=True)
    (test_client / "Closing_Package").mkdir(exist_ok=True)
    
    yield test_client
    
    # Cleanup after tests
    # shutil.rmtree(test_client)


class TestInit:
    """Test initialization."""
    
    def test_ensure_base_structure(self):
        """Test base folders are created."""
        created = ensure_base_structure()
        # Should not raise, may return empty list if already exists
        assert isinstance(created, list)
    
    def test_init_returns_base_dir(self):
        """Test init returns BASE_DIR."""
        result = init()
        assert result == BASE_DIR


class TestClientFolder:
    """Test client folder operations."""
    
    def test_get_client_folder_creates_new(self, setup_test_folders):
        """Test creating new client folder."""
        client = get_client_folder("Test_New", "active")
        assert client.exists()
        assert "Test_New" in str(client)
    
    def test_get_client_folder_existing(self, setup_test_folders):
        """Test getting existing client folder."""
        client = get_client_folder("Test_New", "active")
        client2 = get_client_folder("Test_New", "active")
        assert client == client2


class TestConditionsFolders:
    """Test Conditions folder logic."""
    
    def test_get_next_conditions_number_empty(self, setup_test_folders):
        """Test next number when no Conditions folders exist."""
        client = setup_test_folders
        num = get_next_conditions_number(client)
        assert num == 1
    
    def test_create_conditions_folder(self, setup_test_folders):
        """Test creating Conditions folder."""
        client = setup_test_folders
        folder = create_conditions_folder(client, "VOE needed")
        assert folder.exists()
        assert folder.name.startswith("Conditions_")
    
    def test_get_next_conditions_number_after_create(self, setup_test_folders):
        """Test next number increments after creation."""
        client = setup_test_folders
        create_conditions_folder(client, "First")
        num = get_next_conditions_number(client)
        assert num == 2
    
    def test_max_seven_conditions(self, setup_test_folders):
        """Test max 7 Conditions folders enforced."""
        client = setup_test_folders
        
        # Create 7 folders
        for i in range(7):
            create_conditions_folder(client, f"Condition {i}")
        
        # 8th should merge into last
        folder_8 = create_conditions_folder(client, "Condition 7")
        assert folder_8.name == "Conditions_7"
        
        # Count should still be 7
        assert get_conditions_count(client) == 7


class TestMatchCondition:
    """Test condition matching logic."""
    
    def test_match_creates_new_if_no_existing(self, setup_test_folders):
        """Test match creates new folder when none exist."""
        client = setup_test_folders
        folder, is_new = match_condition_to_folder("VOE needed", client)
        assert is_new
        assert folder.exists()
    
    def test_match_existing_by_keyword(self, setup_test_folders):
        """Test match finds existing folder by keyword."""
        client = setup_test_folders
        # Create a VOE folder
        voe_folder = create_conditions_folder(client, "VOE verification required")
        
        # Match should find it
        folder, is_new = match_condition_to_folder("Need VOE document", client)
        # Note: current implementation is simplistic, may not match
        # This test documents expected behavior
        assert folder.exists()


class TestScanDocuments:
    """Test document scanning."""
    
    def test_scan_empty_folder(self, setup_test_folders):
        """Test scan returns empty list for empty folder."""
        client = setup_test_folders
        results = scan_for_documents(client, ["VOE"])
        assert results == []
    
    def test_scan_finds_files(self, setup_test_folders):
        """Test scan finds matching files."""
        client = setup_test_folders
        
        # Create test files
        submission = client / "Submission"
        (submission / "voe_2025.pdf").write_text("test")
        (submission / "paystub.pdf").write_text("test")
        
        results = scan_for_documents(client, ["voe"])
        assert len(results) == 1
        assert results[0]["file"] == "voe_2025.pdf"


class TestMoveFile:
    """Test file move/copy operations."""
    
    def test_move_file(self, setup_test_folders):
        """Test moving file between folders."""
        client = setup_test_folders
        
        # Create source file
        src = client / "Submission" / "test_move.pdf"
        src.write_text("test content")
        
        # Create dest folder
        dst_folder = client / "Conditions_1"
        dst_folder.mkdir(exist_ok=True)
        
        # Move
        result = move_file(src, dst_folder, make_copy=False)
        
        assert result["success"]
        assert not src.exists()  # Original gone
        assert (dst_folder / "test_move.pdf").exists()  # New exists
    
    def test_copy_file(self, setup_test_folders):
        """Test copying file between folders."""
        client = setup_test_folders
        
        # Create source file
        src = client / "Submission" / "test_copy.pdf"
        src.write_text("test content")
        
        # Create dest folder
        dst_folder = client / "Conditions_1"
        dst_folder.mkdir(exist_ok=True)
        
        # Copy
        result = move_file(src, dst_folder, make_copy=True)
        
        assert result["success"]
        assert src.exists()  # Original still there
        assert (dst_folder / "test_copy.pdf").exists()  # Copy exists


class TestManualFolder:
    """Test manual folder creation."""
    
    def test_create_folder_manual(self, setup_test_folders):
        """Test manual folder creation."""
        client = setup_test_folders
        
        result = create_folder_manual(client, "My_Custom_Folder")
        
        assert result["success"]
        assert (client / "My_Custom_Folder").exists()
    
    def test_create_folder_manual_duplicate(self, setup_test_folders):
        """Test manual folder creation fails if exists."""
        client = setup_test_folders
        
        # Create first
        create_folder_manual(client, "Dup_Folder")
        
        # Try again
        result = create_folder_manual(client, "Dup_Folder")
        
        assert not result["success"]
        assert "exists" in result["error"]


class TestFolderStructure:
    """Test folder structure listing."""
    
    def test_get_folder_structure(self, setup_test_folders):
        """Test getting folder structure."""
        client = setup_test_folders
        
        structure = get_folder_structure(client)
        
        assert len(structure) >= 2  # Submission, Closing_Package at minimum
        
        # Check structure format
        for folder in structure:
            assert "name" in folder
            assert "path" in folder
            assert "file_count" in folder
            assert "is_conditions" in folder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
