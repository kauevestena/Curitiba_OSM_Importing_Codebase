from importer import *

geojsonl_lazy_dumper('buildings',use_alt=True,outfolderpath='outputs/buildings',chunksize=350,
                    #  extra_parameters={'units':'esriSRUnit_Meter'}
                    timeout=600
                     )
