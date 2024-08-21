from importer import *

filelist = [file for file in os.listdir('outputs/buildings') if file.endswith('.geojsonl')]

# sort filelist, using the number in the filename
filelist = sorted(filelist, key=lambda x: int(x.split('_')[-1].split('.')[0]))

registry_path = 'tests/checked_building_files.json'

visited = read_json(registry_path,[])

filelist = [filepath for filepath in filelist if filepath not in visited]

for filename in tqdm(filelist):
        filepath = os.path.join('outputs/buildings', filename)
        gdf = gpd.read_file(filepath)

        # test if any id is missing, the column is "objectid", from the smaller to the biggest no number shall be missing:
        ids = gdf['objectid']

        min_id = min(ids)
        max_id = max(ids)

        dif = max_id - min_id

        if dif != len(ids) - 1:
                raise Exception(f'File {filename} has missing ids, min_id: {min_id}, max_id: {max_id}, len(ids): {len(ids)}')
        
        visited.append(filename)
        dump_json(visited,registry_path)