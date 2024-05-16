from importer import *

geojsonl_lazy_dumper('buildings',use_alt=False,outfolderpath='outputs/buildings',crs=DEFAULT_CRS,chunksize=10000)