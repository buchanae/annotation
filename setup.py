from setuptools import setup, find_packages
import os

_this_dir = os.path.dirname(__file__)
README_path = os.path.join(_this_dir, 'README.md')
README = open(README_path).read()

setup(
    name='annotation',
    description='Tools for working with genome annotations.',
    long_description=README,
    version='2.0.0',
    author='Alex Buchanan',
    author_email='buchanae@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'more_itertools',
        'interval==1.0.1',
        'sequence_utils==0.2.0',
        'gff==2.0.0',
    ],
)
