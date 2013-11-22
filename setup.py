from distutils.core import setup
import os

_this_dir = os.path.dirname(__file__)
README_path = os.path.join(_this_dir, 'README.md')

setup(
    name='annotation',
    description='TODO',
    long_description=open(README_path).read(),
    version='1.0.0',
    author='Alex Buchanan',
    author_email='buchanae@gmail.com',
    license='Apache',
    py_modules=['annotation', 'annotation.models', 'annotation.builders', 'annotation.gff_types'],
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
