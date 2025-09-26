from importer import *

# Check if the buildings directory exists
buildings_dir = 'outputs/buildings'
if not os.path.exists(buildings_dir):
    print(f"Directory {buildings_dir} does not exist. Please run the building dumper first.")
    exit(1)

filelist = [file for file in os.listdir(buildings_dir) if file.endswith('.geojsonl')]

# sort filelist, using the number in the filename
filelist = sorted(filelist, key=lambda x: int(x.split('_')[-1].split('.')[0]))

registry_path = 'tests/checked_building_files.json'

visited = read_json(registry_path, [])

filelist = [filepath for filepath in filelist if filepath not in visited]

# Process files and collect newly processed ones
newly_processed = []

for filename in tqdm(filelist):
    filepath = os.path.join(buildings_dir, filename)
    
    try:
        gdf = gpd.read_file(filepath)
        
        # Check if 'objectid' column exists
        if 'objectid' not in gdf.columns:
            print(f"Warning: 'objectid' column not found in {filename}")
            continue

        # test if any id is missing, the column is "objectid", from the smaller to the biggest no number shall be missing:
        ids = gdf['objectid']
        
        if len(ids) == 0:
            print(f"Warning: No objectids found in {filename}")
            continue

        min_id = min(ids)
        max_id = max(ids)

        dif = max_id - min_id

        if dif != len(ids) - 1:
            raise Exception(f'File {filename} has missing ids, min_id: {min_id}, max_id: {max_id}, len(ids): {len(ids)}')
        
        newly_processed.append(filename)
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        continue

# Only update the registry once at the end with all newly processed files
if newly_processed:
    visited.extend(newly_processed)
    dump_json(visited, registry_path)
    print(f"Successfully processed {len(newly_processed)} files")