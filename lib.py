from constants import *

import os, json
from tqdm import tqdm
from esridump.dumper import EsriDumper
from urllib.parse import urljoin
import geopandas as gpd

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

    if use_alt:
        return urljoin(MAPSERVER_URL_ALT, LAYER_IDS[layername])

    return urljoin(MAPSERVER_URL, LAYER_IDS[layername])

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

    return d.get_metadata()

# TODO: get_layer_crs

def silly_dumper(layername,use_alt=False,outpath=None,crs=DEFAULT_CRS):
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
    
    layer_url = get_layer_url(layername,use_alt=use_alt)

    d = EsriDumper(layer_url)

    total_feats = d.get_feature_count()

    layer_metadata = d.get_metadata()

    all_feats = [feature for feature in tqdm(d,total=total_feats)]

    as_gdf = gpd.GeoDataFrame.from_features(all_feats,crs=crs)

    if outpath:
        as_gdf.to_file(outpath)

        metadata_outpath = outpath.split('.')[0] + '_metadata.json'

        dump_json(layer_metadata,metadata_outpath)

    return as_gdf


# only time setups
create_folderlist(['outputs','tests'])