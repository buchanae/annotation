from distutils.core import setup
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
    py_modules=[
        'annotation.models',
        'annotation.builders',
        'annotation.builders.core',
        'annotation.builders.gff',
        'annotation.sequences',
    ],
    dependency_links=[
        'http://github.com/abuchanan/interval/archive/v1.0.0.zip#egg=abuchanan_interval-1.0.0',
        'http://github.com/abuchanan/sequence_utils/archive/v0.2.0.zip#egg=abuchanan_sequence_utils-0.2.0',
    ],
    install_requires=[
        'more_itertools',
        'abuchanan_interval==1.0.0',
        'abuchanan_sequence_utils==0.2.0',
    ],
)
