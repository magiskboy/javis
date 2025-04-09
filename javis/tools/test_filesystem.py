import os
import shutil
import unittest
import tempfile

from javis.tools import filesystem


class TestFilesystem(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp(prefix="test_filesystem_")
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        self.test_folder_path = os.path.join(self.temp_dir, "test_folder")
        
        # Create a test file with content
        with open(self.test_file_path, "w") as f:
            f.write("Test content")

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_file_details(self):
        # Test getting details of an existing file
        details = filesystem.get_file_details(self.test_file_path)
        self.assertEqual(details.name, "test_file.txt")
        self.assertEqual(details.path, os.path.abspath(self.test_file_path))
        self.assertTrue(details.is_file)
        self.assertFalse(details.is_dir)
        self.assertTrue(details.exists)
        
        # Test non-existent file
        with self.assertRaises(FileNotFoundError):
            filesystem.get_file_details(os.path.join(self.temp_dir, "nonexistent.txt"))

    def test_create_file(self):
        # Test creating a new file
        new_file_path = os.path.join(self.temp_dir, "new_file.txt")
        result = filesystem.create_file(new_file_path, "New content")
        self.assertTrue(result.success)
        self.assertEqual(result.path, os.path.abspath(new_file_path))
        self.assertTrue(os.path.exists(new_file_path))
        
        # Verify content
        with open(new_file_path, "r") as f:
            self.assertEqual(f.read(), "New content")
        
        # Test creating a file that already exists
        with self.assertRaises(FileExistsError):
            filesystem.create_file(self.test_file_path)

    def test_update_file(self):
        # Test updating an existing file
        result = filesystem.update_file(self.test_file_path, "Updated content")
        self.assertTrue(result.success)
        
        # Verify content was updated
        with open(self.test_file_path, "r") as f:
            self.assertEqual(f.read(), "Updated content")
        
        # Test updating a non-existent file
        with self.assertRaises(FileNotFoundError):
            filesystem.update_file(os.path.join(self.temp_dir, "nonexistent.txt"), "content")

    def test_delete_file(self):
        # Test deleting an existing file
        result = filesystem.delete_file(self.test_file_path)
        self.assertTrue(result.success)
        self.assertFalse(os.path.exists(self.test_file_path))
        
        # Test deleting a non-existent file
        with self.assertRaises(FileNotFoundError):
            filesystem.delete_file(os.path.join(self.temp_dir, "nonexistent.txt"))
        
        # Test deleting a directory as a file
        os.makedirs(self.test_folder_path)
        with self.assertRaises(IsADirectoryError):
            filesystem.delete_file(self.test_folder_path)

    def test_create_folder(self):
        # Test creating a new folder
        result = filesystem.create_folder(self.test_folder_path)
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(self.test_folder_path))
        self.assertTrue(os.path.isdir(self.test_folder_path))
        
        # Test creating a folder that already exists
        with self.assertRaises(FileExistsError):
            filesystem.create_folder(self.test_folder_path)

    def test_delete_folder(self):
        # Create a folder for testing
        os.makedirs(self.test_folder_path)
        
        # Test deleting an empty folder
        result = filesystem.delete_folder(self.test_folder_path)
        self.assertTrue(result.success)
        self.assertFalse(os.path.exists(self.test_folder_path))
        
        # Create a non-empty folder
        os.makedirs(self.test_folder_path)
        with open(os.path.join(self.test_folder_path, "file.txt"), "w") as f:
            f.write("content")
        
        # Test deleting a non-empty folder without recursive flag
        result = filesystem.delete_folder(self.test_folder_path)
        self.assertFalse(result.success)
        self.assertTrue(os.path.exists(self.test_folder_path))
        
        # Test deleting a non-empty folder with recursive flag
        result = filesystem.delete_folder(self.test_folder_path, recursive=True)
        self.assertTrue(result.success)
        self.assertFalse(os.path.exists(self.test_folder_path))
        
        # Test deleting a non-existent folder
        with self.assertRaises(FileNotFoundError):
            filesystem.delete_folder(os.path.join(self.temp_dir, "nonexistent_folder"))

    def test_list_folder_contents(self):
        # Create a folder with some contents
        os.makedirs(self.test_folder_path)
        file1_path = os.path.join(self.test_folder_path, "file1.txt")
        file2_path = os.path.join(self.test_folder_path, "file2.txt")
        subfolder_path = os.path.join(self.test_folder_path, "subfolder")
        
        with open(file1_path, "w") as f:
            f.write("content1")
        with open(file2_path, "w") as f:
            f.write("content2")
        os.makedirs(subfolder_path)
        
        # Test listing without details
        result = filesystem.list_folder_contents(self.test_folder_path)
        self.assertTrue(result.success)
        self.assertEqual(result.files_count, 2)
        self.assertEqual(result.folders_count, 1)
        self.assertEqual(len(result.items), 3)
        self.assertIn("file1.txt", result.items)
        self.assertIn("file2.txt", result.items)
        self.assertIn("subfolder", result.items)
        
        # Test listing with details
        result = filesystem.list_folder_contents(self.test_folder_path, include_details=True)
        self.assertTrue(result.success)
        self.assertEqual(result.files_count, 2)
        self.assertEqual(result.folders_count, 1)
        self.assertEqual(len(result.items), 3)
        
        # Verify details are included
        for item in result.items:
            if item.name == "file1.txt":
                self.assertTrue(item.is_file)
                self.assertFalse(item.is_dir)
            elif item.name == "subfolder":
                self.assertFalse(item.is_file)
                self.assertTrue(item.is_dir)
        
        # Test listing a non-existent folder
        with self.assertRaises(FileNotFoundError):
            filesystem.list_folder_contents(os.path.join(self.temp_dir, "nonexistent_folder"))

    def test_copy_file(self):
        # Test copying a file
        dest_path = os.path.join(self.temp_dir, "copied_file.txt")
        result = filesystem.copy_file(self.test_file_path, dest_path)
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(dest_path))
        
        # Verify content was copied
        with open(dest_path, "r") as f:
            self.assertEqual(f.read(), "Test content")
        
        # Test copying to an existing destination without overwrite
        with self.assertRaises(FileExistsError):
            filesystem.copy_file(self.test_file_path, dest_path)
        
        # Test copying to an existing destination with overwrite
        with open(self.test_file_path, "w") as f:
            f.write("New test content")
        
        result = filesystem.copy_file(self.test_file_path, dest_path, overwrite=True)
        self.assertTrue(result.success)
        
        # Verify content was overwritten
        with open(dest_path, "r") as f:
            self.assertEqual(f.read(), "New test content")
        
        # Test copying a non-existent file
        with self.assertRaises(FileNotFoundError):
            filesystem.copy_file(os.path.join(self.temp_dir, "nonexistent.txt"), dest_path)

    def test_move_file(self):
        # Test moving a file
        dest_path = os.path.join(self.temp_dir, "moved_file.txt")
        result = filesystem.move_file(self.test_file_path, dest_path)
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(dest_path))
        self.assertFalse(os.path.exists(self.test_file_path))
        
        # Create a new source file for further tests
        with open(self.test_file_path, "w") as f:
            f.write("Test content for move")
        
        # Test moving to an existing destination without overwrite
        with self.assertRaises(FileExistsError):
            filesystem.move_file(self.test_file_path, dest_path)
        
        # Test moving to an existing destination with overwrite
        result = filesystem.move_file(self.test_file_path, dest_path, overwrite=True)
        self.assertTrue(result.success)
        self.assertFalse(os.path.exists(self.test_file_path))
        
        # Verify content was moved
        with open(dest_path, "r") as f:
            self.assertEqual(f.read(), "Test content for move")
        
        # Test moving a non-existent file
        with self.assertRaises(FileNotFoundError):
            filesystem.move_file(os.path.join(self.temp_dir, "nonexistent.txt"), dest_path)


if __name__ == "__main__":
    unittest.main()
