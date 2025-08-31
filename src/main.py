from .constants import *

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
    Creates a directory if it does not exist.

    Args:
        path (str): The path to the directory.
    """
    if not os.path.exists(path):
        os.makedirs(path)

def create_folderlist(inputlist):
    """
    Creates a list of directories.

    Args:
        inputlist (list): A list of directory paths.
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
    A JSON encoder that converts int64 to string.
    """
    def default(self, o):
        if isinstance(o, int):
            return str(o)
        return super().default(o)

def dump_json(data, path):
    """
    Dumps a dictionary to a JSON file.

    Args:
        data (dict): The dictionary to dump.
        path (str): The path to the JSON file.
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_layer_url(layername,use_alt=False):
    """
    Gets the URL of a layer.

    Args:
        layername (str): The name of the layer.
        use_alt (bool, optional): Whether to use the alternative URL. Defaults to False.

    Returns:
        str: The URL of the layer.
    """
    baseurl = MAPSERVER_URL

    if use_alt:
        baseurl = MAPSERVER_URL_ALT

    if not baseurl.endswith('/'):
        baseurl += '/'

    layer_id = LAYER_IDS[layername]

    if use_alt:
        layer_id = LAYER_IDS[layername+'_alt']

    return urljoin(baseurl,layer_id)

def get_layer_metadata(layername,use_alt=False,outpath=None):
    """
    Retrieves the metadata of a layer from the EsriDumper object.

    Args:
        layername (str): The name of the layer to retrieve the metadata for.
        use_alt (bool, optional): Whether to use the alternative layer URL. Defaults to False.
        outpath (str, optional): The path to save the metadata as a JSON file. Defaults to None.

    Returns:
        dict: The metadata of the layer.
    """
    d = EsriDumper(get_layer_url(layername,use_alt=use_alt))
    md = d.get_metadata()
    if outpath:
        dump_json(md,outpath)
    return md

def get_basic_layer_stuff(layername,use_alt=False):
    """
    Gets basic information about a layer.

    Args:
        layername (str): The name of the layer.
        use_alt (bool, optional): Whether to use the alternative URL. Defaults to False.

    Returns:
        tuple: A tuple containing the layer URL, the EsriDumper object, the total number of features, and the layer metadata.
    """
    layer_url = get_layer_url(layername,use_alt=use_alt)
    d = EsriDumper(layer_url)
    total_feats = None
    try :
        total_feats = d.get_feature_count()
    except Exception as e:
        logging.error(e)
    layer_metadata = d.get_metadata()
    return layer_url, d, total_feats, layer_metadata

@retry(wait=wait_exponential(multiplier=1, min=10, max=120) + wait_random(min=1, max=12))
def get_features(layername, use_alt=False, start_with=0, max_page_size=100, extra_query_args=None, timeout=None):
    """
    Retrieves features from an Esri layer.

    Args:
        layername (str): The name of the layer.
        use_alt (bool, optional): Whether to use the alternative URL. Defaults to False.
        start_with (int, optional): The starting index for fetching features. Defaults to 0.
        max_page_size (int, optional): The maximum number of features per page. Defaults to 100.
        extra_query_args (dict, optional): Extra query arguments. Defaults to None.
        timeout (int, optional): The timeout for the request. Defaults to None.

    Returns:
        tuple: A tuple containing the EsriDumper object and the total number of features.
    """
    layer_url = get_layer_url(layername, use_alt=use_alt)
    d = EsriDumper(layer_url, start_with=start_with, max_page_size=max_page_size, extra_query_args=extra_query_args, timeout=timeout)
    total_feats = d.get_feature_count()
    return d, total_feats

def silly_dumper(layername,use_alt=False,outpath=None,different_crs=None,as_geoparquet=False):
    """
    Dumps the features of a given layer from the EsriDumper object and returns a GeoDataFrame.
    
    It got no optimization, it got no filtering, it got no pagination.
    It's just a poor silly little thing hahaha

    Parameters:
        layername (str): The name of the layer to dump.
        use_alt (bool, optional): Whether to use the alternative layer URL. Defaults to False.
        outpath (str, optional): The path to save the GeoDataFrame as a file. Defaults to None.
        crs (str, optional): The CRS of the GeoDataFrame. Defaults to DEFAULT_CRS.
    
    Returns:
        gpd.GeoDataFrame: The GeoDataFrame containing the dumped features.
    """
    d, total_feats = get_features(layername, use_alt=use_alt)
    layer_metadata = d.get_metadata()

    all_feats = [feature for feature in tqdm(d,total=total_feats)]

    if different_crs:
        as_gdf = gpd.GeoDataFrame.from_features(all_feats,crs=different_crs).to_crs(OSM_CRS)
    else:
        as_gdf = gpd.GeoDataFrame.from_features(all_feats,crs=OSM_CRS) # apparently, default is WGS84 already

    if outpath:
        if as_geoparquet:
            as_gdf.to_parquet(outpath)
        else:
            as_gdf.to_file(outpath)

        metadata_outpath = outpath.split('.')[0] + '_metadata.json'

        dump_json(layer_metadata,metadata_outpath)

    return as_gdf

def append_to_file(filepath,data_str):
    """
    Appends a string to a file.

    Args:
        filepath (str): The path to the file.
        data_str (str): The string to append.
    """
    with open(filepath,'a',encoding='utf-8') as f:
        f.write(data_str)

def read_file_as_list(filepath):
    """
    Reads a file and returns a list of lines.

    Args:
        filepath (str): The path to the file.

    Returns:
        list: A list of lines.
    """
    if os.path.exists(filepath):
        with open(filepath,'r',encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    else:
        return []

def listdir_fullpath(inputfolderpath,extension=None):
    """
    Lists all files in a directory.

    Args:
        inputfolderpath (str): The path to the directory.
        extension (str, optional): The extension of the files to list. Defaults to None.

    Returns:
        list: A list of full paths to the files.
    """
    if not os.path.exists(inputfolderpath):
        return []
    else:
        if extension:
            return [os.path.join(inputfolderpath,filename) for filename in os.listdir(inputfolderpath) if filename.endswith(extension)]
        else:
            return [os.path.join(inputfolderpath,filename) for filename in os.listdir(inputfolderpath)]

@retry(wait=wait_exponential(multiplier=1, min=10, max=120) + wait_random(min=1, max=12))
def geojsonl_lazy_dumper(layername,use_alt=False,outfolderpath=None,out_crs=None,chunksize=1000,page_size=100,extra_parameters=None,timeout=None):
    """
    Dumps the features of a given layer in the geojsonl format with resume capabilities.

    Parameters:
        layername (str): The name of the layer to dump.
        use_alt (bool, optional): Whether to use the alternative layer URL. Defaults to False.
        outfolderpath (str): The path to output the dumped features.
        crs (str): The CRS of the dumped features. Defaults to DEFAULT_CRS.
        chunksize (int): The number of features per chunk.

    Returns:
        None
    """
    def layer_outpath(layername,outfolderpath,j=0):

        return os.path.join(outfolderpath,f'{layername}_chunk_{j}.geojsonl')

    # download registry, to give resume capabilities:
    # TODO: transform into a class, for ease up using in other situations
    downloaded_registry_path = os.path.join(outfolderpath,f'{layername}_downloaded_registry.txt')
    downloaded_registry = read_file_as_list(downloaded_registry_path)

    n_chunks = 0
    start_idx = 0

    if downloaded_registry:
        n_chunks = len(downloaded_registry)

        #estimate the chunk size by reading one file:
        resumed_chunksize = len(read_file_as_list(downloaded_registry[0]))

        start_idx = n_chunks * resumed_chunksize

        existent_outpaths = listdir_fullpath(outfolderpath,extension='.geojsonl')

        # deleting uncompleted chunks:
        for outpath in existent_outpaths:
            if not outpath in downloaded_registry:
                os.remove(outpath)


    # create output folder if it doesn't exist
    create_dir(outfolderpath)

    # get layer stuff
    d, total_feats = get_features(layername, use_alt=use_alt, start_with=start_idx, max_page_size=page_size, extra_query_args=extra_parameters, timeout=timeout)
    layer_metadata = d.get_metadata()

    j = n_chunks # - 1
    outpath = layer_outpath(layername,outfolderpath,j=j)
    
    metadata_outpath = os.path.join(outfolderpath,f'{layername}_metadata.json')
    dump_json(layer_metadata,metadata_outpath)

    for i,feature in tqdm(enumerate(d,start=start_idx),total=total_feats,initial=start_idx):
        if i % chunksize == 0 and i > start_idx:
            # noting that the current chunk was properly downloaded
            if not outpath in downloaded_registry:
                append_to_file(downloaded_registry_path,outpath+'\n')

            # updating outfile:
            j += 1
            outpath = layer_outpath(layername,outfolderpath,j=j)

        append_to_file(outpath,json.dumps(feature)+'\n')

# one-time setups
create_folderlist(['outputs','tests','logs'])

logging.basicConfig(filename='logs/global_log.log',
                    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S',filemode='w')

def list_of_set_of_list(inputlist):
    """
    Removes duplicates from a list.

    Args:
        inputlist (list): The list to remove duplicates from.

    Returns:
        list: The list without duplicates.
    """
    return list(set(inputlist))

def get_filelist(category,folder='outputs',extension='.geojsonl'):
    """
    Gets a list of files in a directory.

    Args:
        category (str): The category of the files.
        folder (str, optional): The folder to search in. Defaults to 'outputs'.
        extension (str, optional): The extension of the files. Defaults to '.geojsonl'.

    Returns:
        tuple: A tuple containing the search path and the list of files.
    """
    search_path = os.path.join(folder,category)
    filelist = [file for file in os.listdir(search_path) if file.endswith(extension) and category in file]

    return search_path,filelist