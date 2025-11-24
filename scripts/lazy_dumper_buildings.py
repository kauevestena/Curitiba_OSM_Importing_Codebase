from importer import *
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump building data from Geocuritiba portal.')
    parser.add_argument('--output', '-o', type=str, default='outputs/buildings',
                        help='Path to the output directory (default: outputs/buildings)')
    
    args = parser.parse_args()
    
    geojsonl_lazy_dumper('buildings', use_alt=True, outfolderpath=args.output, chunksize=350,
                         timeout=600)
