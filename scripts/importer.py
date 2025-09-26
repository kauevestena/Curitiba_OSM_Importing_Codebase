# JUST TO IMPORT STUFF
import sys
import os
sys.path.append('.')
from lib import *

def get_filelist(category, folder='outputs', extension='.geojsonl'):
    """
    Retrieves a list of files in a directory that match a given category and extension.

    Args:
        category (str): The category to search for in the filenames.
        folder (str, optional): The root folder to search in. Defaults to 'outputs'.
        extension (str, optional): The file extension to filter by.
                                   Defaults to '.geojsonl'.

    Returns:
        tuple: A tuple containing:
            - str: The full path of the search directory.
            - list: A list of filenames that match the criteria.
    
    Raises:
        ValueError: If category is empty.
        FileNotFoundError: If the search directory doesn't exist.
    """
    if not category:
        raise ValueError("category cannot be empty")
    
    search_path = os.path.join(folder, category)
    
    if not os.path.exists(search_path):
        raise FileNotFoundError(f"Directory {search_path} does not exist")
    
    try:
        filelist = [file for file in os.listdir(search_path) 
                   if file.endswith(extension) and category in file]
    except OSError as e:
        logging.error(f"Error reading directory {search_path}: {e}")
        raise
    
    return search_path, filelist