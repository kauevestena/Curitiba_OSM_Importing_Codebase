import argparse
from ..main import geojsonl_lazy_dumper

def main():
    parser = argparse.ArgumentParser(description='Dumps building data lazily.')
    parser.add_argument('--outfolderpath', default='outputs/buildings', help='The output folder path.')
    parser.add_argument('--chunksize', type=int, default=350, help='The chunk size.')
    parser.add_argument('--timeout', type=int, default=600, help='The timeout.')
    parser.add_argument('--use-alt', action='store_true', help='Use alternative URL.')
    args = parser.parse_args()

    geojsonl_lazy_dumper('buildings', use_alt=args.use_alt, outfolderpath=args.outfolderpath, chunksize=args.chunksize, timeout=args.timeout)

if __name__ == "__main__":
    main()
