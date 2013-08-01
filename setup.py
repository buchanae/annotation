from distutils.core import setup


setup(
    name='annotation',
    description='TODO',
    long_description=open('README.md').read(),
    version='1.0.0',
    author='Alex Buchanan',
    author_email='buchanae@gmail.com',
    license='Apache',
    py_modules=['annotation'],
    dependency_links=[
        'http://github.com/abuchanan/interval/archive/v1.0.0.zip#egg=abuchanan_interval-1.0.0',
        'http://github.com/abuchanan/interval/archive/v0.2.0.zip#egg=abuchanan_sequence_utils-0.2.0',
    ],
    install_requires=[
        'more_itertools',
        'abuchanan_interval==1.0.0',
        'abuchanan_sequence_utils==0.2.0',
    ],
)
