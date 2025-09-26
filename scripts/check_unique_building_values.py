from importer import *
import numpy as np
import pandas as pd

buildings_folderpath, filelist = get_filelist('buildings')

if not filelist:
    print(f"No files found in {buildings_folderpath}")
    exit(1)

data = {}
types = []

columns_to_exclude = ['objectid', 'x_coord', 'y_coord', 'geometry', 'ctba_nome', 'nome']

for filename in tqdm(filelist):
    filepath = os.path.join(buildings_folderpath, filename)
    
    try:
        gdf = gpd.read_file(filepath)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        continue

    for col in gdf.columns:
        if col not in columns_to_exclude:
            values = []
            uniques = gdf[col].unique()

            # Process unique values with better type handling
            for value in uniques:
                value_type = type(value)
                types.append(str(value_type))
                
                # Handle different numpy and pandas types more robustly
                if pd.isna(value):
                    # Skip NaN/None values
                    continue
                elif isinstance(value, (np.integer, np.int64, np.int32)):
                    values.append(int(value))
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    if not np.isnan(value):
                        values.append(float(value))
                elif isinstance(value, np.bool_):
                    values.append(bool(value))
                elif isinstance(value, (str, np.str_)):
                    values.append(str(value))
                else:
                    # For any other types, try to convert to a serializable format
                    try:
                        # Try to convert to basic Python types
                        if hasattr(value, 'item'):  # numpy scalar
                            values.append(value.item())
                        else:
                            values.append(value)
                    except (ValueError, TypeError):
                        # If conversion fails, convert to string as fallback
                        values.append(str(value))

            # Update data dictionary with unique values
            if col in data:
                data[col] = list(set(data[col] + values))
            else:
                data[col] = list(set(values))

# Save results
try:
    dump_json(list_of_set_of_list(types), 'tests/unique_building_value_types.json')
    dump_json(data, 'metadata/unique_building_values.json')
    print("Successfully processed building values and saved results")
except Exception as e:
    print(f"Error saving results: {e}")
