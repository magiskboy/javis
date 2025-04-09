import os
import shutil
import subprocess
from datetime import datetime
from typing import List, Union
from pydantic import BaseModel


__all__ = [
    "get_file_details",
    "create_file",
    "update_file",
    "delete_file",
    "create_folder",
    "delete_folder",
    "read_folder",
    "copy_file",
    "move_file",
    "open_file",
    "read_file",
]

class FileDetails(BaseModel):
    name: str
    path: str
    size: int
    created: str
    modified: str
    is_file: bool
    is_dir: bool
    exists: bool = True


class FileOperationResult(BaseModel):
    success: bool
    path: str
    message: str


class FileCopyMoveResult(BaseModel):
    success: bool
    source: str
    destination: str
    message: str


class FolderContentsResult(BaseModel):
    success: bool
    path: str
    items: List[Union[str, FileDetails]]
    files_count: int
    folders_count: int
    message: str


def get_file_details(file_path: str) -> FileDetails:
    """Get detailed information about a file.

    Args:
        file_path (str): Path to the file.

    Returns:
        FileDetails: A model containing file details with the following fields:
            - name: Name of the file
            - path: Absolute path to the file
            - size: Size of the file in bytes
            - created: Creation timestamp
            - modified: Last modification timestamp
            - is_file: Boolean indicating if it's a file
            - is_dir: Boolean indicating if it's a directory
            - exists: Boolean indicating if the path exists

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stats = os.stat(file_path)
    return FileDetails(
        name=os.path.basename(file_path),
        path=os.path.abspath(file_path),
        size=stats.st_size,
        created=datetime.fromtimestamp(stats.st_ctime).isoformat(),
        modified=datetime.fromtimestamp(stats.st_mtime).isoformat(),
        is_file=os.path.isfile(file_path),
        is_dir=os.path.isdir(file_path),
        exists=True
    )


def create_file(file_path: str, content: str = "") -> FileOperationResult:
    """Create a new file with optional content.

    Args:
        file_path (str): Path where the file should be created.
        content (str, optional): Content to write to the file. Defaults to empty string.

    Returns:
        FileOperationResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - path: Absolute path to the created file
            - message: Description of the operation result

    Raises:
        FileExistsError: If the file already exists.
        IOError: If there's an error writing to the file.
    """
    if os.path.exists(file_path):
        raise FileExistsError(f"File already exists: {file_path}")
    
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        
        return FileOperationResult(
            success=True,
            path=os.path.abspath(file_path),
            message=f"File created successfully at {file_path}"
        )
    except IOError as e:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Failed to create file: {str(e)}"
        )


def update_file(file_path: str, content: str) -> FileOperationResult:
    """Update the content of an existing file.

    Args:
        file_path (str): Path to the file to update.
        content (str): New content to write to the file.

    Returns:
        FileOperationResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - path: Absolute path to the updated file
            - message: Description of the operation result

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there's an error writing to the file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
    
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        
        return FileOperationResult(
            success=True,
            path=os.path.abspath(file_path),
            message=f"File updated successfully at {file_path}"
        )
    except IOError as e:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Failed to update file: {str(e)}"
        )


def delete_file(file_path: str) -> FileOperationResult:
    """Delete a file.

    Args:
        file_path (str): Path to the file to delete.

    Returns:
        FileOperationResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - path: Absolute path to the deleted file
            - message: Description of the operation result

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if os.path.isdir(file_path):
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
    
    try:
        os.remove(file_path)
        return FileOperationResult(
            success=True,
            path=os.path.abspath(file_path),
            message=f"File deleted successfully: {file_path}"
        )
    except Exception as e:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Failed to delete file: {str(e)}"
        )


def create_folder(folder_path: str) -> FileOperationResult:
    """Create a new folder.

    Args:
        folder_path (str): Path where the folder should be created.

    Returns:
        FileOperationResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - path: Absolute path to the created folder
            - message: Description of the operation result

    Raises:
        FileExistsError: If the folder already exists.
    """
    if os.path.exists(folder_path):
        raise FileExistsError(f"Folder already exists: {folder_path}")
    
    try:
        os.makedirs(folder_path)
        return FileOperationResult(
            success=True,
            path=os.path.abspath(folder_path),
            message=f"Folder created successfully at {folder_path}"
        )
    except Exception as e:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(folder_path),
            message=f"Failed to create folder: {str(e)}"
        )


def delete_folder(folder_path: str, recursive: bool = False) -> FileOperationResult:
    """Delete a folder.

    Args:
        folder_path (str): Path to the folder to delete.
        recursive (bool, optional): Whether to recursively delete the folder and its contents.
            Defaults to False.

    Returns:
        FileOperationResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - path: Absolute path to the deleted folder
            - message: Description of the operation result

    Raises:
        FileNotFoundError: If the folder does not exist.
        NotADirectoryError: If the path points to a file.
        OSError: If the folder is not empty and recursive is False.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    
    try:
        if recursive:
            shutil.rmtree(folder_path)
        else:
            os.rmdir(folder_path)
        
        return FileOperationResult(
            success=True,
            path=os.path.abspath(folder_path),
            message=f"Folder deleted successfully: {folder_path}"
        )
    except OSError as e:
        if "Directory not empty" in str(e) and not recursive:
            return FileOperationResult(
                success=False,
                path=os.path.abspath(folder_path),
                message="Folder is not empty. Use recursive=True to delete non-empty folders."
            )
        return FileOperationResult(
            success=False,
            path=os.path.abspath(folder_path),
            message=f"Failed to delete folder: {str(e)}"
        )


def read_folder(folder_path: str, include_details: bool = False) -> FolderContentsResult:
    """List the contents of a folder.

    Args:
        folder_path (str): Path to the folder.
        include_details (bool, optional): Whether to include detailed information about each item.
            Defaults to False.

    Returns:
        FolderContentsResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - path: Absolute path to the folder
            - items: List of items in the folder (filenames or detailed dictionaries)
            - files_count: Number of files in the folder
            - folders_count: Number of subfolders in the folder
            - message: Description of the operation result

    Raises:
        FileNotFoundError: If the folder does not exist.
        NotADirectoryError: If the path points to a file.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    
    try:
        items = os.listdir(folder_path)
        files_count = 0
        folders_count = 0
        
        result_items = []
        for item in items:
            item_path = os.path.join(folder_path, item)
            is_dir = os.path.isdir(item_path)
            
            if is_dir:
                folders_count += 1
            else:
                files_count += 1
            
            if include_details:
                result_items.append(get_file_details(item_path))
            else:
                result_items.append(item)
        
        return FolderContentsResult(
            success=True,
            path=os.path.abspath(folder_path),
            items=result_items,
            files_count=files_count,
            folders_count=folders_count,
            message=f"Successfully listed {len(items)} items in {folder_path}"
        )
    except Exception as e:
        return FolderContentsResult(
            success=False,
            path=os.path.abspath(folder_path),
            items=[],
            files_count=0,
            folders_count=0,
            message=f"Failed to list folder contents: {str(e)}"
        )


def copy_file(source_path: str, destination_path: str, overwrite: bool = False) -> FileCopyMoveResult:
    """Copy a file from source to destination.

    Args:
        source_path (str): Path to the source file.
        destination_path (str): Path where the file should be copied to.
        overwrite (bool, optional): Whether to overwrite if destination exists. Defaults to False.

    Returns:
        FileCopyMoveResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - source: Absolute path to the source file
            - destination: Absolute path to the destination file
            - message: Description of the operation result

    Raises:
        FileNotFoundError: If the source file does not exist.
        FileExistsError: If the destination file exists and overwrite is False.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    if not os.path.isfile(source_path):
        raise IsADirectoryError(f"Source path is not a file: {source_path}")
    
    if os.path.exists(destination_path) and not overwrite:
        raise FileExistsError(f"Destination file already exists: {destination_path}")
    
    try:
        shutil.copy2(source_path, destination_path)
        return FileCopyMoveResult(
            success=True,
            source=os.path.abspath(source_path),
            destination=os.path.abspath(destination_path),
            message=f"File copied successfully from {source_path} to {destination_path}"
        )
    except Exception as e:
        return FileCopyMoveResult(
            success=False,
            source=os.path.abspath(source_path),
            destination=os.path.abspath(destination_path),
            message=f"Failed to copy file: {str(e)}"
        )


def move_file(source_path: str, destination_path: str, overwrite: bool = False) -> FileCopyMoveResult:
    """Move a file from source to destination.

    Args:
        source_path (str): Path to the source file.
        destination_path (str): Path where the file should be moved to.
        overwrite (bool, optional): Whether to overwrite if destination exists. Defaults to False.

    Returns:
        FileCopyMoveResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - source: Absolute path to the source file
            - destination: Absolute path to the destination file
            - message: Description of the operation result

    Raises:
        FileNotFoundError: If the source file does not exist.
        FileExistsError: If the destination file exists and overwrite is False.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    if os.path.exists(destination_path) and not overwrite:
        raise FileExistsError(f"Destination file already exists: {destination_path}")
    
    try:
        shutil.move(source_path, destination_path)
        return FileCopyMoveResult(
            success=True,
            source=os.path.abspath(source_path),
            destination=os.path.abspath(destination_path),
            message=f"File moved successfully from {source_path} to {destination_path}"
        )
    except Exception as e:
        return FileCopyMoveResult(
            success=False,
            source=os.path.abspath(source_path),
            destination=os.path.abspath(destination_path),
            message=f"Failed to move file: {str(e)}"
        )


def open_file(file_path: str) -> FileOperationResult:
    """Open a file using the system's default application.

    Args:
        file_path (str): Path to the file to open.

    Returns:
        FileOperationResult: A model containing the result with the following fields:
            - success: Boolean indicating if operation was successful
            - path: Absolute path to the file
            - message: Description of the operation result
    """
    
    if not os.path.exists(file_path):
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"File not found: {file_path}"
        )
    
    try:
        subprocess.run(['open', file_path], check=True)
        return FileOperationResult(
            success=True,
            path=os.path.abspath(file_path),
            message=f"File opened successfully: {file_path}"
        )
    except subprocess.SubprocessError as e:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Failed to open file: {str(e)}"
        )


def read_file(file_path: str) -> Union[str, FileOperationResult]:
    """Read the content of a file.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        Union[str, FileOperationResult]: The content of the file as a string if successful,
            or a FileOperationResult with error details if the operation failed.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        PermissionError: If the file cannot be read due to permission issues.
    """
    if not os.path.exists(file_path):
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"File not found: {file_path}"
        )
    
    if os.path.isdir(file_path):
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Path points to a directory, not a file: {file_path}"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return content
    except PermissionError:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Permission denied: Cannot read file {file_path}"
        )
    except UnicodeDecodeError:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Failed to decode file: {file_path} is not a valid text file or has an unsupported encoding"
        )
    except Exception as e:
        return FileOperationResult(
            success=False,
            path=os.path.abspath(file_path),
            message=f"Failed to read file: {str(e)}"
        )
