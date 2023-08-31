from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='ckanext-geoimapact',
    version='0.0.1',
    description='A collection of various extensions of ckan, which are needed for the geoimact DataCatalog project',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords="ckan geoimpact switzerland metadata catalog",
    author='geoimpact',
    author_email='info@geoimpact.ch',
    url='https://github.com/geoimpactag/ckanext-geoimpact',
    project_urls={
        'Documentation': 'https://github.com/geoimpactag/ckanext-geoimpact/blob/main/README.md',
        'Source': 'https://github.com/geoimpactag/ckanext-geoimpact',
        'Tracker': 'https://github.com/geoimpactag/ckanext-geoimpact/issues',
    },
    license='',  # TODO: add license
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=['ckan'],  # TODO: if we overweite the the fluent plugin, we need to add it here
    entry_points='''
        [ckan.plugins]
        geoimapact=ckanext.geoimapact.plugins:GeoimpactPlugin
    ''',
)