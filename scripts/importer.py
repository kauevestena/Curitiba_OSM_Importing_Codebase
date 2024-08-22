# JUST TO IMPORT STUFF
import sys
sys.path.append('.')
from lib import *

def get_filelist(category,folder='outputs',extension='.geojsonl'):
    search_path = os.path.join(folder,category)
    filelist = [file for file in os.listdir(search_path) if file.endswith(extension) and category in file]

    return search_path,filelist