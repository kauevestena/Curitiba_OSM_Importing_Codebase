import argparse
from ..main import silly_dumper

def main():
    parser = argparse.ArgumentParser(description='Dumps building data.')
    parser.add_argument('--outpath', default='outputs/buildings.parquet', help='The output path for the parquet file.')
    parser.add_argument('--as-geoparquet', action='store_true', help='Save as GeoParquet.')
    args = parser.parse_args()

    silly_dumper('buildings', outpath=args.outpath, as_geoparquet=args.as_geoparquet)

if __name__ == "__main__":
    main()