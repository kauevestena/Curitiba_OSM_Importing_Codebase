from constants import *

import os, json
from tqdm import tqdm
from esridump.dumper import EsriDumper
from urllib.parse import urljoin
import geopandas as gpd
import logging
from tenacity import retry, wait_exponential, wait_random
from json import JSONEncoder

OSM_CRS = 'EPSG:4326'

def create_dir(path):
    """
    Creates a directory if it does not already exist.

    Args:
        path (str): The path of the directory to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)

def create_folderlist(inputlist):
    """
    Creates a list of directories.

    Args:
        inputlist (list): A list of directory paths to create.
    """
    return [create_dir(dirpath) for dirpath in inputlist]

def read_json(path,default={}):
    """
    Reads a JSON file from the specified path.

    Args:
        path (str): The path to the JSON file.
        default (Union[dict, list, None], optional): The default value to return if the file does not exist.
                                                    If default is a dictionary, it will be used as the default value.
                                                    If default is a list, it will be used as the default value.
                                                    If default is None, an empty dictionary will be used as the default value.
                                                    Defaults to {}.

    Returns:
        dict or list: The contents of the JSON file, or the default value if the file does not exist.
    """
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    else:
        return default

class Int64Encoder(JSONEncoder):
    """
    A custom JSON encoder to handle numpy and pandas types that are not serializable by default.
    """
    def default(self, o):
        import numpy as np
        import pandas as pd
        
        # Handle numpy integer types
        if isinstance(o, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(o)
        # Handle numpy floating point types
        elif isinstance(o, (np.floating, np.float64, np.float32, np.float16)):
            if np.isnan(o):
                return None
            return float(o)
        # Handle numpy boolean types
        elif isinstance(o, (np.bool_, np.bool)):
            return bool(o)
        # Handle numpy string types
        elif isinstance(o, (np.str_, np.unicode_)):
            return str(o)
        # Handle pandas NaType
        elif pd.isna(o):
            return None
        # Handle any other numpy types by converting to Python types
        elif hasattr(o, 'item'):
            return o.item()
        
        return super().default(o)

def dump_json(data, path):
    """
    Dumps a dictionary or list to a JSON file.

    Args:
        data (dict or list): The data to dump.
        path (str): The path to the output JSON file.
    
    Raises:
        OSError: If there's an issue creating directories or writing the file.
        TypeError: If the data is not JSON serializable.
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(path)
        if directory:
            create_dir(directory)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, cls=Int64Encoder)
    except (OSError, IOError) as e:
        logging.error(f"Error writing JSON file {path}: {e}")
        raise
    except TypeError as e:
        logging.error(f"Error serializing data to JSON for {path}: {e}")
        raise

def get_layer_url(layername, use_alt=False):
    """
    Constructs the URL for a specific layer.

    Args:
        layername (str): The name of the layer.
        use_alt (bool, optional): Whether to use the alternative map server URL.
                                  Defaults to False.

    Returns:
        str: The full URL of the layer.
    """
    baseurl = MAPSERVER_URL_ALT if use_alt else MAPSERVER_URL

    if not baseurl.endswith('/'):
        baseurl += '/'

    layer_id_key = f"{layername}_alt" if use_alt else layername
    layer_id = LAYER_IDS[layer_id_key]

    return urljoin(baseurl, str(layer_id))

def get_layer_metadata(layername, use_alt=False, outpath=None):
    """
    Retrieves and optionally saves the metadata of a map service layer.

    Args:
        layername (str): The name of the layer.
        use_alt (bool, optional): Whether to use the alternative map server URL.
                                  Defaults to False.
        outpath (str, optional): The file path to save the metadata as a JSON file.
                                 If None, the metadata is not saved. Defaults to None.

    Returns:
        dict: A dictionary containing the layer's metadata.
    """
    d = EsriDumper(get_layer_url(layername, use_alt=use_alt))
    md = d.get_metadata()

    if outpath:
        dump_json(md, outpath)

    return md

# TODO: get_layer_crs

def get_basic_layer_stuff(layername, use_alt=False):
    """
    Initializes an EsriDumper and retrieves basic layer information.

    Args:
        layername (str): The name of the layer.
        use_alt (bool, optional): Whether to use the alternative map server URL.
                                  Defaults to False.

    Returns:
        tuple: A tuple containing:
            - str: The layer's URL.
            - EsriDumper: An EsriDumper instance for the layer.
            - int: The total number of features in the layer.
            - dict: The layer's metadata.
    """
    layer_url = get_layer_url(layername, use_alt=use_alt)
    d = EsriDumper(layer_url)

    total_feats = None
    try:
        total_feats = d.get_feature_count()
    except Exception as e:
        logging.error(e)
    
    layer_metadata = d.get_metadata()

    return layer_url, d, total_feats, layer_metadata

def silly_dumper(layername, use_alt=False, outpath=None, different_crs=None, as_geoparquet=False):
    """
    Dumps all features from a layer into a GeoDataFrame.

    This function provides a simple way to dump all features from a layer without
    any filtering or pagination. It is not optimized for large datasets.

    Args:
        layername (str): The name of the layer to dump.
        use_alt (bool, optional): Whether to use the alternative map server URL.
                                  Defaults to False.
        outpath (str, optional): The file path to save the output. If None, the
                                 GeoDataFrame is not saved. Defaults to None.
        different_crs (str, optional): The original CRS of the data if it's not
                                       the default. Defaults to None.
        as_geoparquet (bool, optional): If True, saves the output as a GeoParquet
                                        file. Otherwise, saves as a GeoJSON file.
                                        Defaults to False.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing all features from the layer.
    """
    _, d, total_feats, layer_metadata = get_basic_layer_stuff(layername, use_alt=use_alt)

    all_feats = [feature for feature in tqdm(d, total=total_feats)]

    if different_crs:
        as_gdf = gpd.GeoDataFrame.from_features(all_feats, crs=different_crs).to_crs(OSM_CRS)
    else:
        as_gdf = gpd.GeoDataFrame.from_features(all_feats, crs=OSM_CRS)

    if outpath:
        if as_geoparquet:
            as_gdf.to_parquet(outpath)
        else:
            as_gdf.to_file(outpath)

        metadata_outpath = outpath.split('.')[0] + '_metadata.json'
        dump_json(layer_metadata, metadata_outpath)

    return as_gdf

def append_to_file(filepath, data_str):
    """
    Appends a string to a file.

    Args:
        filepath (str): The path to the file.
        data_str (str): The string to append.
    
    Raises:
        OSError: If there's an issue creating directories or writing to the file.
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(filepath)
        if directory:
            create_dir(directory)
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(data_str)
    except (OSError, IOError) as e:
        logging.error(f"Error appending to file {filepath}: {e}")
        raise


def read_file_as_list(filepath):
    """
    Reads a file and returns its lines as a list of strings.

    Args:
        filepath (str): The path to the file.

    Returns:
        list: A list of strings, where each string is a line from the file.
              Returns an empty list if the file does not exist.
    
    Raises:
        OSError: If there's an issue reading the file (other than file not existing).
    """
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    except (OSError, IOError) as e:
        logging.error(f"Error reading file {filepath}: {e}")
        raise


def listdir_fullpath(inputfolderpath, extension=None):
    """
    Lists all files in a directory, returning their full paths.

    Args:
        inputfolderpath (str): The path to the directory.
        extension (str, optional): If provided, only files with this extension
                                   are returned. Defaults to None.

    Returns:
        list: A list of full paths to the files in the directory.
    """
    if not os.path.exists(inputfolderpath):
        return []
    else:
        if extension:
            return [os.path.join(inputfolderpath, filename) for filename in os.listdir(inputfolderpath) if
                    filename.endswith(extension)]
        else:
            return [os.path.join(inputfolderpath, filename) for filename in os.listdir(inputfolderpath)]

@retry(wait=wait_exponential(multiplier=1, min=10, max=120) + wait_random(min=1, max=12))
def geojsonl_lazy_dumper(layername, use_alt=False, outfolderpath=None, out_crs=None, chunksize=1000, page_size=100, extra_parameters=None, timeout=None):
    """
    Dumps features from a layer to a GeoJSONL file with resume capabilities.

    This function is designed to be resilient, using exponential backoff for retries.
    It can resume downloads from where they left off by checking for a registry of
    completed chunks.

    Args:
        layername (str): The name of the layer to dump.
        use_alt (bool, optional): Whether to use the alternative map server URL.
                                  Defaults to False.
        outfolderpath (str, optional): The directory to save the output files.
                                       Defaults to None.
        out_crs (str, optional): The CRS for the output data. Defaults to None.
        chunksize (int, optional): The number of features to save in each chunk file.
                                   Defaults to 1000.
        page_size (int, optional): The number of features to request per page from
                                   the server. Defaults to 100.
        extra_parameters (dict, optional): Extra parameters to pass in the query to
                                           the server. Defaults to None.
        timeout (int, optional): The timeout for the HTTP requests. Defaults to None.
    
    Raises:
        ValueError: If layername is empty or outfolderpath is None.
        Exception: If there are issues with the data download or file operations.
    """
    if not layername:
        raise ValueError("layername cannot be empty")
    
    if outfolderpath is None:
        raise ValueError("outfolderpath cannot be None")
    
    def layer_outpath(layername, outfolderpath, j=0):
        return os.path.join(outfolderpath, f'{layername}_chunk_{j}.geojsonl')

    # download registry, to give resume capabilities:
    # TODO: transform into a class, for ease up using in other situations
    downloaded_registry_path = os.path.join(outfolderpath, f'{layername}_downloaded_registry.txt')
    downloaded_registry = read_file_as_list(downloaded_registry_path)

    n_chunks = 0
    start_idx = 0

    if downloaded_registry:
        n_chunks = len(downloaded_registry)

        # estimate the chunk size by reading one file:
        if os.path.exists(downloaded_registry[0]):
            resumed_chunksize = len(read_file_as_list(downloaded_registry[0]))
            start_idx = n_chunks * resumed_chunksize
        else:
            logging.warning(f"Registry file {downloaded_registry[0]} not found, starting from beginning")

        existent_outpaths = listdir_fullpath(outfolderpath, extension='.geojsonl')

        # deleting uncompleted chunks:
        for outpath in existent_outpaths:
            if outpath not in downloaded_registry:
                try:
                    os.remove(outpath)
                    logging.info(f"Removed incomplete chunk: {outpath}")
                except OSError as e:
                    logging.warning(f"Could not remove file {outpath}: {e}")

    # create output folder if it doesn't exist
    create_dir(outfolderpath)

    # get layer stuff
    layer_url, _, total_feats, layer_metadata = get_basic_layer_stuff(layername, use_alt=use_alt)

    # for proper resuming capabilities: 
    d = EsriDumper(layer_url, start_with=start_idx, max_page_size=page_size, extra_query_args=extra_parameters, timeout=timeout)

    j = n_chunks
    outpath = layer_outpath(layername, outfolderpath, j=j)
    
    metadata_outpath = os.path.join(outfolderpath, f'{layername}_metadata.json')
    dump_json(layer_metadata, metadata_outpath)

    for i, feature in tqdm(enumerate(d, start=start_idx), total=total_feats, initial=start_idx):
        if i % chunksize == 0 and i > start_idx:
            # noting that the current chunk was properly downloaded
            if outpath not in downloaded_registry:
                append_to_file(downloaded_registry_path, outpath + '\n')

            # updating outfile:
            j += 1
            outpath = layer_outpath(layername, outfolderpath, j=j)

        append_to_file(outpath, json.dumps(feature) + '\n')

# one-time setups
create_folderlist(['outputs','tests','logs'])

logging.basicConfig(filename='logs/global_log.log',
                    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S',filemode='w')

def list_of_set_of_list(inputlist):
    """
    Removes duplicate elements from a list by converting it to a set and back to a list.

    Args:
        inputlist (list): The input list.

    Returns:
        list: A new list with duplicate elements removed.
    """
    return list(set(inputlist))