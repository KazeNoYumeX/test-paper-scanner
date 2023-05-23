from setuptools import setup, find_packages
from Test_Paper_Scanner import __version__

setup(
    name='Test_Paper_Scanner',
    version=__version__,
    author='KazeNoYumeX',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.11'
)
