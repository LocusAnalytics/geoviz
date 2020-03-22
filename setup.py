from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='geoviz',
      version='1.0.1',
      description='Wrapper to easily make geo-based visualizations',
      long_description=readme(),
      long_description_content_type = 'text/markdown',
      url='https://github.com/LocusAnalytics/geoviz',
      author='W. Aaron Lee',
      author_email='alee@locus.co',
      license='MIT',
      packages=['geoviz', 'geoviz.data'],
      include_package_data=True,
      install_requires=['pandas',
                        'matplotlib',
                        'bokeh',
                        'geopandas',
                        'descartes',
                        'pysal',
                        'us',
                        "importlib_resources"
                        ])
