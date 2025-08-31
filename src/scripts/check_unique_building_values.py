import os
import argparse
import numpy as np
import geopandas as gpd
from tqdm import tqdm
from ..main import get_filelist, dump_json, list_of_set_of_list

def main():
    parser = argparse.ArgumentParser(description='Checks unique building values.')
    parser.add_argument('--buildings-folder', default='outputs', help='The folder with the building data.')
    parser.add_argument('--types-outpath', default='tests/unique_building_value_types.json', help='The output path for the types file.')
    parser.add_argument('--values-outpath', default='metadata/unique_building_values.json', help='The output path for the values file.')
    args = parser.parse_args()

    buildings_folderpath, filelist = get_filelist('buildings', folder=args.buildings_folder)

    data = {}

    types = []

    columns_to_exclude = ['objectid','x_coord','y_coord','geometry','ctba_nome','nome']

    for filename in tqdm(filelist):
        filepath = os.path.join(buildings_folderpath, filename)
        gdf = gpd.read_file(filepath)

        for col in gdf.columns:
            if not col in columns_to_exclude:
                values = []

                uniques = gdf[col].unique()


                # to avoid numpy types headache
                for value in uniques:
                    types.append(str(type(value)))
                    # if isinstance(value,str):
                    #     values.append(value)
                    #     continue

                    # if not value:
                    #     values.append(value)
                    #     continue

                    if isinstance(value, np.int64):
                        if not np.isnan(value):
                            values.append(int(value))
                    else:
                        try:
                            # since np.isnan throws an exception if value is not a number
                            # that's might be the last resort agains nans
                            if np.isnan(value):
                                continue
                        except:
                            pass

                        values.append(value)


                if col in data:
                    data[col] = list(set(data[col]).union((set(values))))
                else:
                    data[col] = values

        dump_json(list_of_set_of_list(types), args.types_outpath)
        dump_json(data, args.values_outpath)

if __name__ == '__main__':
    main()
