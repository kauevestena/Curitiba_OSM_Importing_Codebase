import os
import argparse
import geopandas as gpd
from tqdm import tqdm
from ..main import read_json, dump_json

def main():
    parser = argparse.ArgumentParser(description='Checks building data.')
    parser.add_argument('--buildings-folder', default='outputs/buildings', help='The folder with the building data.')
    parser.add_argument('--registry-path', default='tests/checked_building_files.json', help='The path to the registry file.')
    args = parser.parse_args()

    filelist = [file for file in os.listdir(args.buildings_folder) if file.endswith('.geojsonl')]

    # sort filelist, using the number in the filename
    filelist = sorted(filelist, key=lambda x: int(x.split('_')[-1].split('.')[0]))

    visited = read_json(args.registry_path,[])

    filelist = [filepath for filepath in filelist if filepath not in visited]

    for filename in tqdm(filelist):
            filepath = os.path.join(args.buildings_folder, filename)
            gdf = gpd.read_file(filepath)

            # test if any id is missing, the column is "objectid", from the smaller to the biggest no number shall be missing:
            ids = gdf['objectid']

            min_id = min(ids)
            max_id = max(ids)

            dif = max_id - min_id

            if dif != len(ids) - 1:
                    raise Exception(f'File {filename} has missing ids, min_id: {min_id}, max_id: {max_id}, len(ids): {len(ids)}')

            visited.append(filename)
            dump_json(visited, args.registry_path)

if __name__ == '__main__':
    main()