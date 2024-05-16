from constants import *

import os, json
from tqdm import tqdm
from esridump.dumper import EsriDumper
from urllib.parse import urljoin
import geopandas as gpd
import logging

logging.basicConfig(filename='global_log.log',
                    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S',filemode='w')

OSM_CRS = 'EPSG:4326'

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_folderlist(inputlist):
    return [create_dir(dirpath) for dirpath in inputlist]

def read_json(path):
    with open(path) as f:
        return json.load(f)
    
def dump_json(data,path):
    with open(path,'w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=4)

def get_layer_url(layername,use_alt=False):

    baseurl = MAPSERVER_URL

    if use_alt:
        baseurl = MAPSERVER_URL_ALT

    if not baseurl.endswith('/'):
        baseurl += '/'

    return urljoin(baseurl, LAYER_IDS[layername])

def get_layer_metadata(layername,use_alt=False,outpath=None):
    """    layer_url, d , total_feats, layer_metadata = get_basic_layer_stuff(layername,use_alt=use_alt)

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

# TODO: get_layer_crs

def get_basic_layer_stuff(layername,use_alt=False):
    
    layer_url = get_layer_url(layername,use_alt=use_alt)

    d = EsriDumper(layer_url)

    total_feats = None

    try :
        total_feats = d.get_feature_count()
    except Exception as e:
        logging.error(e)
    
    layer_metadata = d.get_metadata()

    return layer_url, d , total_feats, layer_metadata

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
    _ , d , total_feats, layer_metadata = get_basic_layer_stuff(layername,use_alt=use_alt)

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
    with open(filepath,'a',encoding='utf-8') as f:
        f.write(data_str)

def read_file_as_list(filepath):
    if os.path.exists(filepath):
        with open(filepath,'r',encoding='utf-8') as f:
            return f.readlines()
    else:
        return []

def geojsonl_lazy_dumper(layername,use_alt=False,outfolderpath=None,crs=DEFAULT_CRS,chunksize=10000):
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
    # TODO: check if sometimes the iteration isn't random...
    # TODO: skip already downloaded features using d = EsriDumper(layer_url,start_with=N) being N the number of already downloaded features
    downloaded_registry_path = os.path.join(outfolderpath,f'{layername}_downloaded_registry.txt')
    downloaded_registry = read_file_as_list(downloaded_registry_path)

    # create output folder if it doesn't exist
    create_dir(outfolderpath)

    # get layer stuff
    _ , d , total_feats, layer_metadata = get_basic_layer_stuff(layername,use_alt=use_alt)

    j = 0
    outpath = layer_outpath(layername,outfolderpath,j=j)
    
    metadata_outpath = os.path.join(outfolderpath,f'{layername}_metadata.json')
    dump_json(layer_metadata,metadata_outpath)

    for i,feature in tqdm(enumerate(d),total=total_feats):
        if i % chunksize == 0 and i > 0:
            # noting that the current chunk was properly downloaded
            if not outpath in downloaded_registry:
                append_to_file(downloaded_registry_path,outpath)

            # updating outfile:
            j += 1
            outpath = layer_outpath(layername,outfolderpath,j=j)

            # but in case the file exists, it will hold duplicate features, then:
            if not outpath in downloaded_registry:
                if os.path.exists(outpath):
                    os.remove(outpath)

        if not outpath in downloaded_registry:
            append_to_file(outpath,json.dumps(feature)+'\n')

# one-time setups
create_folderlist(['outputs','tests'])