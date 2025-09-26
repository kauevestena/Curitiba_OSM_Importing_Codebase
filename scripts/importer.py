# JUST TO IMPORT STUFF
import sys
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
    """
    search_path = os.path.join(folder, category)
    filelist = [file for file in os.listdir(search_path) if file.endswith(extension) and category in file]

    return search_path, filelist