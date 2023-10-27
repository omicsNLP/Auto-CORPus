import gc
import tarfile
import zipfile
import os
from collections import defaultdict

zip_extensions = [".zip", ".7z", ".rar", ".zlib", ".7-zip", ".pzip", ".xz"]
tar_extensions = [".tgz", ".tar"]
gzip_extensions = [".gzip", ".gz"]
archive_extensions = zip_extensions + tar_extensions + gzip_extensions

unique_directories = defaultdict(lambda: defaultdict(lambda: {"total": 0}))


def reset_directory_tally():
    """
    Reset the unique_directories global and run garbage collection
    """
    global unique_directories
    unique_directories = defaultdict(lambda: defaultdict(lambda: {"total": 0}))
    gc.collect()


def search_zip(path, extensions=None):
    """
    Recursively searches for file extensions within a ZIP archive.

    Args:
        path (str): The path to the ZIP archive.
        extensions (dict, optional): A dictionary to store extension information.
            Defaults to None, in which case a new defaultdict will be created.

    Returns:
        extensions (dict): A dictionary containing information about file extensions within the ZIP archive.
            The keys are file extensions, and the values are dictionaries with the following structure:
                - 'total' (int): The total count of files with the extension.
                - 'locations' (list): A list of paths to the locations of files with the extension.

    """
    if extensions is None:
        extensions = defaultdict(lambda: {'total': 0, 'locations': []})
    with zipfile.ZipFile(path, 'r') as zip_ref:
        # Iterate over the members (files and directories) within the ZIP archive
        for member in zip_ref.infolist():
            member_extension = os.path.splitext(member.filename)[-1]
            # Check if the member is a nested ZIP archive
            if member_extension.endswith("zip"):
                # Recursively search inside the nested ZIP archive
                search_zip(zip_ref.extract(member), extensions)
            # Check if the member has a valid file extension and is not from the _MACOSX directory
            elif "." in member_extension and "_MACOSX" not in member.filename:
                extensions[member_extension]['total'] += 1
                extensions[member_extension]['locations'].append(path)
            # Handle file paths without a file name but with an extension (e.g., _rels/.rels)
            else:
                # Only file paths without a file name, but with an extension such as _rels/.rels
                # should reach this
                member_extension = os.path.split(member.filename)[-1]
                extensions[member_extension]['total'] += 1
                extensions[member_extension]['locations'].append(path)
    # Return the updated extensions dictionary
    return extensions


def search_tar(root, file, folder_path, extensions=None):
    """
    Searches for file extensions within a tar-compressed file.

    Args:
        root (str): The root directory of the tar-compressed file.
        file (str): The name of the tar-compressed file.
        folder_path (str): The path to the folder containing the tar-compressed file.
        extensions (dict, optional): A dictionary to store extension information.
            Defaults to None, in which case a new defaultdict will be created.

    Returns:
        extensions (dict): A dictionary containing information about file extensions within the tar file.
            The keys are file extensions, and the values are dictionaries with the following structure:
                - 'total' (int): The total count of files with the extension.
                - 'locations' (list): A list of relative paths to the locations of files with the extension.

    """
    if extensions is None:
        extensions = defaultdict(lambda: {'total': 0, 'locations': []})
    # Get uncompressed filename and extension
    with tarfile.open(os.path.join(root, file), "r:gz") as archive:
        # Iterate over the members (files and directories) within the TAR archive
        for member in archive.getmembers():
            # Get the extension of the member's name
            member_extension = os.path.splitext(member.name)[-1]
            # Check if the extension is not empty
            if member_extension:
                location = os.path.relpath(os.path.join(root, file, member.name), folder_path)
                # Increment the total count of files with the extension
                extensions[member_extension]['total'] += 1
                # Add the location of the file to the list of locations for the extension
                extensions[member_extension]['locations'].append(location)
    # Return the updated extensions dictionary
    return extensions


def search_gzip(root, file, folder_path, extensions=None):
    """
    Searches for file extensions within a gzip-compressed file.

    Args:
        root (str): The root directory of the gzip-compressed file.
        file (str): The name of the gzip-compressed file.
        folder_path (str): The path to the folder containing the gzip-compressed file.
        extensions (dict, optional): A dictionary to store extension information.
            Defaults to None, in which case a new defaultdict will be created.

    Returns:
        extensions (dict): A dictionary containing information about file extensions within the gzip file.
            The keys are file extensions, and the values are dictionaries with the following structure:
                - 'total' (int): The total count of files with the extension.
                - 'locations' (list): A list of relative paths to the locations of files with the extension.

    """
    # Get uncompressed filename and extension
    if extensions is None:
        extensions = defaultdict(lambda: {'total': 0, 'locations': []})
    # Get uncompressed filename and extension
    filename, extension = os.path.splitext(file)
    if extension == '.gz':
        extension = os.path.splitext(filename)[-1]
    # Check if the extension is not empty
    if extension:
        location = os.path.relpath(os.path.join(root, file), folder_path)
        # Increment the total count of files with the extension
        extensions[extension]['total'] += 1
        # Add the location of the file to the list of locations for the extension
        extensions[extension]['locations'].append(location)
    # Return the updated extensions dictionary
    return extensions


def get_file_extensions(folder_path):
    """
    Retrieves information about file extensions in a specified folder and its subdirectories.

    Args:
        folder_path (str): The path to the folder to be scanned.

    Returns:
        extensions (dict): A dictionary containing information about file extensions.
            The keys are file extensions, and the values are dictionaries with the following structure:
                - 'total' (int): The total count of files with the extension.
                - 'locations' (list): A list of relative paths to the locations of files with the extension.

    """
    reset_directory_tally()  # Reset the directory tally
    extensions = defaultdict(lambda: {'total': 0, 'locations': []})
    # Recursively walk through the folder and its subdirectories
    for root, dirs, files in os.walk(folder_path):
        # Iterate over the files in the current directory
        for file in files:
            # Get file extension
            file_extension = os.path.splitext(file)[-1]
            # Check if the file has an extension
            if file_extension:
                location = os.path.relpath(os.path.join(root, file), folder_path)
                # Increment the total count of files with the extension
                extensions[file_extension]['total'] += 1
                # Increment the total count of files with the extension for the current directory
                unique_directories[root][file_extension]["total"] += 1
                # Add the location of the file to the list of locations for the extension
                extensions[file_extension]['locations'].append(location)

            # Check if the file is an archive and retrieve additional extensions
            new_extensions = {}
            if file_extension in zip_extensions:
                new_extensions = search_zip(os.path.join(root, file))
            elif file_extension in tar_extensions:
                new_extensions = search_tar(root, file, folder_path)
            elif file_extension in gzip_extensions:
                new_extensions = search_gzip(root, file, folder_path)
            # Process the additional extensions retrieved from archives
            if new_extensions:
                for extension_record in new_extensions.items():
                    extension = extension_record[0]
                    total = extension_record[1]["total"]
                    # Increment the total count of files with the additional extension for the current directory
                    unique_directories[root][extension]["total"] += total
                    # Increment the total count of files with the additional extension for the specific file location
                    unique_directories[os.path.join(root, file)][extension]["total"] += total
    # Return the dictionary of extensions and their information
    return extensions


def build_data_rows(structure):
    """
    Recursively builds a data table from a nested dictionary structure.

    Args:
        structure (dict): A nested dictionary representing the file structure.

    Returns:
        list: A list of data rows, where each row is a list containing file name,
        extension, and a numeric value.

    """
    data_table = []  # Initialize an empty list to store the data rows
    # Iterate over the files in the structure dictionary
    for file in structure.keys():
        # Iterate over the extensions for each file
        for extension in structure[file].keys():
            # Check if the value associated with the extension is an integer
            if type(structure[file][extension]) is int:
                # If it is an integer, add a data row with the file name,
                # extension, and the integer value to the data table
                data_table.append([file, extension, structure[file][extension]])
            else:
                # If the value is not an integer, assume it is a nested dictionary
                # representing a subdirectory and add a data row with the file name,
                # extension, and a default value of 1 to the data table
                data_table.append([file, extension, 1])

                # Recursively call the function to build data rows for the nested structure
                # and concatenate the resulting data rows to the current data_table
                data_table = data_table + build_data_rows(structure[file][extension])

    # Return the final data table
    return data_table


def print_output(extensions, input_path):
    """
    Print summaries of file counts based on their extensions and directories.

    Args:
        extensions: A dictionary containing file extensions and their corresponding counts.
        input_path: The input path used as the base directory for file paths.

    Returns:
        None
    """
    # Print directory level summaries
    for directory in unique_directories.keys():
        # Print the relative directory path
        print(F"{directory.replace(input_path, '')[1:]}")
        # Get the statistics for the directory
        directory_stats = unique_directories[directory]
        directory_total = 0
        # Print file counts for each extension in the directory
        for extension in directory_stats.keys():
            total = directory_stats[extension]["total"]
            print(F"{extension}: {total} files")
            directory_total += total
        # Print the total number of files in the directory
        print(F"Total: {directory_total} files")
        print("-----------------------")
    total_file_count = 0
    print("-- Aggregate counts --")
    # Print aggregate file counts for each extension
    for extension, stats in sorted(extensions.items()):
        total = stats['total']
        total_file_count += total
        print(F"{extension}: {total} files")
    # Print the total number of files across all extensions
    print(F"Total: {total_file_count} files")
