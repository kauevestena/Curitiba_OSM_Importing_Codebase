from setuptools import setup, find_packages

setup(
    name='curitiba-osm-importer',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'tqdm',
        'geopandas',
        'esridump',
        'pyarrow',
        'tenacity',
    ],
    entry_points={
        'console_scripts': [
            'simple-dumper-buildings = src.scripts.simple_dumper_buildings:main',
            'lazy-dumper-buildings = src.scripts.lazy_dumper_buildings:main',
            'check-buildings = src.scripts.check_buildings:main',
            'check-unique-building-values = src.scripts.check_unique_building_values:main',
        ],
    },
)
