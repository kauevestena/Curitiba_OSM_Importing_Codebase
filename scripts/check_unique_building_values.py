from importer import *
import numpy as np

buildings_folderpath, filelist = get_filelist('buildings')

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

    dump_json(list_of_set_of_list(types),'tests/unique_building_value_types.json')
    dump_json(data,'metadata/unique_building_values.json')
