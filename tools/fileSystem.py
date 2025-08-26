import os
from langchain.tools import tool

@tool
def find_files_in_directory(directory_path) -> list[str]:
    """
        Returns a list of files in a {directory_path}

        Args:
            directory_path (str): The path of the driectory to search for file

        Returns:
            list: A list containing the names of the files (not including directories)
    """

    files = []
    for item in os.listdir(directory_path):
        full_path = os.path.join(directory_path, item)
        if os.path.isfile(full_path):
            files.append(item)
    return files

@tool
def read_file(file_path) -> list[str]:
    """
        Returns a File Contents of file_path

        Args:
            file_path (str): The path of the file to read

        Returns:
            list: A list lines in File contents
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.readlines()
        return file_contents
    except FileExistsError:
        return [f"No file in {file_path}"]
    except Exception as e:
        return [f"An error eccurred: {e}"]

@tool
def write_file(file_path, contents, mode) -> str:
    """
        Writing {file_path} and Return result message of writing (Success or Error)

        Args:
            file_path (str): The path of file to write
            contents (str): Content to be filled into the {file_path}
            mode (str): mode variable in open Function

        Returns:
            str: Always "Success" if written correctly, or error message.
        Important:
            If you receive "Success", consider the task finished and answer the user directly.
            Do NOT call this tool again for the same request.

            If you recevie error message, you should finish task and answer the user directly about error message and Do Not Call this tool again for the same request.
    """
    try:
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(contents)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"An error occurred while writing to the file: {e}"

@tool
def delete_file(file_path) -> str:
    """
        Description:
            Delete {file_path} and Return result message

        Code logic steps:
            1. Check the file exist by {file_path}
            2. Start to delete {file_path}
            3. Return result message
            4. If There is no {file_path}, Then Return message about it

        Args:
            file_path (str) : The path of file to delete

        Returns:
            str: Successfully delete message or Doesn't exist file message
    """

    if os.path.exists(file_path):
        os.remove(file_path)
        return f"Successfully delete {file_path}"
    else:
        return f"There is no {file_path}"